import io
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.control_layer.audit import AuditEvent, JsonLinesAuditSink
from app.control_layer.composition import default_controls, default_targets
from app.control_layer.domain import Action, Finding, Interaction, Span
from app.control_layer.policy import load_policy
from app.control_layer.registry import ControlRegistration, ControlRegistry
from app.control_layer.reporting import (
    Completion,
    EventFilter,
    GroupBy,
    InvocationStatus,
    ReportingError,
    ReportingProjection,
)
from app.control_layer.reporting_store import PersistentAuditSink, ReportingStore
from app.control_layer.service import InteractionService
from app.control_layer.targets import (
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
    TargetResult,
)

CANARY = "UNSAFE_CANARY alice@example.com SSN: 123-45-6789 Bearer secret-value"


class Target:
    def __init__(self, store, stream):
        self.store, self.stream = store, stream
        self.calls = []
        self.fail = False
        self.invalid = False

    def invoke(self, interaction):
        # Actual committed history is visible before dispatch, with original
        # stdout eligibility shape and no completion yet.
        event = self.store.get_event(interaction.id)
        assert event.invocation_status == InvocationStatus.UNKNOWN
        assert any(
            json.loads(line)["interaction_id"] == str(interaction.id)
            for line in self.stream.getvalue().splitlines()
        )
        self.calls.append(interaction)
        if self.fail:
            raise RuntimeError(CANARY)
        if self.invalid:
            return {"content": CANARY, "model": CANARY}
        return TargetResult(CANARY)


def composition(
    tmp_path, action=Action.REDACT, *, control=None, enabled=True, model=None
):
    tmp_path.mkdir(parents=True, exist_ok=True)
    registration = default_controls().registrations[0]
    if control is not None:
        registration = ControlRegistration(registration.definition, control)
    path = tmp_path / "policy.yaml"
    path.write_text(
        "version: 1\npolicy_id: test\ncontrols:\n  email-address:\n"
        f"    enabled: {str(enabled).lower()}\n    findings:\n"
        f"      pii.email: {action}\n"
    )
    policy = load_policy(path, ControlRegistry((registration,)))
    store = ReportingStore(tmp_path / "db.sqlite3")
    stream = io.StringIO()
    target = Target(store, stream)
    targets = TargetRegistry(
        (RegisteredTarget(TargetDefinition("local-echo", model), target),)
    )
    projection = ReportingProjection(policy, targets)
    sink = PersistentAuditSink(JsonLinesAuditSink(stream), store, projection)
    service = InteractionService(policy, sink, targets)
    return service, store, sink, target, stream


def audit(service, action=Action.ALLOW, *, timestamp=None, counts=()):
    return AuditEvent(
        "decision",
        uuid4(),
        timestamp or datetime.now(UTC),
        "local-echo",
        service.policy.digest,
        ("email-address",),
        (("email-address", True),),
        action,
        counts,
        action != Action.BLOCK,
        2.0,
    )


def window():
    now = datetime.now(UTC)
    return EventFilter(now - timedelta(days=1), now + timedelta(days=1))


@pytest.mark.parametrize("action", list(Action))
def test_actions_restart_content_free_and_timings(tmp_path, action):
    service, store, sink, target, stream = composition(tmp_path, action)
    interaction = Interaction.create("local-echo", CANARY)
    result = service.evaluate(interaction)
    assert result.error_code is None
    assert result.decision.action == action
    event = store.get_event(interaction.id)
    assert event.event.action == action
    assert event.event.findings[0].control_id == "email-address"
    assert event.event.findings[0].count == 1
    assert event.event.reason_code == "policy_resolved"
    assert event.invocation_status == (
        InvocationStatus.NOT_INVOKED
        if action == Action.BLOCK
        else InvocationStatus.SUCCEEDED
    )
    assert len(target.calls) == (0 if action == Action.BLOCK else 1)
    if action == Action.REDACT:
        assert "alice@example.com" not in target.calls[0].content
    if event.completion:
        assert (
            event.completion.total_duration_ms
            >= event.completion.invocation_duration_ms
            >= 0
        )
    assert len(stream.getvalue().splitlines()) == 1
    serialized = repr(asdict(event)) + stream.getvalue()
    for secret in (
        CANARY,
        "alice@example.com",
        "123-45-6789",
        "secret-value",
        "[REDACTED]",
        "span",
        "content",
    ):
        assert secret not in serialized
    store.close()
    raw = (tmp_path / "db.sqlite3").read_bytes()
    assert b"alice@example.com" not in raw
    assert b"UNSAFE_CANARY" not in raw
    reopened = ReportingStore(tmp_path / "db.sqlite3")
    assert reopened.get_event(interaction.id) == event
    assert reopened.list_events() == (event,)
    reopened.close()


@pytest.mark.parametrize("action", [Action.ALLOW, Action.REDACT])
@pytest.mark.parametrize("invalid", [False, True])
def test_target_failure_is_separate_safe_completion(tmp_path, action, invalid):
    service, store, _, target, _ = composition(tmp_path, action)
    target.fail, target.invalid = not invalid, invalid
    result = service.evaluate(Interaction.create("local-echo", CANARY))
    assert result.error_code == "target_failed"
    event = store.get_event(result.interaction_id)
    assert event.event.action == action
    assert event.invocation_status == InvocationStatus.FAILED
    assert event.completion.error_code == "target_failed"
    assert CANARY not in repr(event)
    assert len(target.calls) == 1
    store.close()


class InvalidControl:
    id = "email-address"

    def evaluate(self, interaction):
        return (Finding("foreign", "pii.email", Span(0, 1)),)


@pytest.mark.parametrize("target_id", ["local-echo", "PRIVATE_SECRET_UNKNOWN"])
def test_operational_failure_and_unresolved_never_store_assertions(tmp_path, target_id):
    service, store, _, target, _ = composition(tmp_path, control=InvalidControl())
    result = service.evaluate(Interaction.create(target_id, CANARY))
    assert result.error_code == "evaluation_failed"
    event = store.get_event(result.interaction_id)
    assert event.event.action is None
    assert event.event.findings == ()
    assert event.event.error_code == "evaluation_failed"
    assert event.invocation_status == InvocationStatus.NOT_INVOKED
    assert event.event.target_id == (
        "local-echo" if target_id == "local-echo" else "unresolved"
    )
    assert "PRIVATE_SECRET_UNKNOWN" not in repr(event)
    assert not target.calls
    store.close()


@pytest.mark.parametrize(
    "change",
    [
        {"target_id": "unregistered"},
        {"target_id": CANARY},
        {"target_id": 1},
        {"policy_digest": "f" * 64},
        {"policy_digest": CANARY},
        {"interaction_id": str(uuid4())},
        {"event_type": "unknown"},
        {"timestamp": datetime.now()},
        {"timestamp": CANARY},
        {"evaluated_controls": ("unregistered",)},
        {"evaluated_controls": ["email-address"]},
        {"control_status": (("email-address", 1),)},
        {"control_status": (("email-address", False),)},
        {"finding_counts": (("foreign.code", 1),)},
        {"finding_counts": (("pii.email", True),)},
        {"finding_counts": (("pii.email", 0),)},
        {"finding_counts": (("pii.email", -1),)},
        {"finding_counts": (("pii.email", 1), ("pii.email", 1))},
        {"finding_counts": {"pii.email": 1}},
        {"finding_counts": ((CANARY, 1),)},
        {"action": "ALLOW"},
        {"action": Action.BLOCK},
        {"error_code": CANARY},
        {"forwarding_eligible": 1},
        {"forwarding_eligible": False},
        {"evaluation_duration_ms": float("nan")},
        {"evaluation_duration_ms": float("inf")},
        {"evaluation_duration_ms": -1},
        {"evaluation_duration_ms": True},
    ],
)
def test_projection_rejects_untrusted_or_inconsistent_metadata(tmp_path, change):
    service, store, sink, target, stream = composition(tmp_path)
    with pytest.raises(ReportingError, match="^invalid_reporting_record$"):
        sink.projection.project(replace(audit(service), **change))
    assert store.list_events() == ()
    assert not stream.getvalue() and not target.calls
    store.close()


@pytest.mark.parametrize(
    "model", ["", CANARY, 3, True, {}, "a" * 129, "http://model", "Model", " model"]
)
def test_invalid_model_identity(model):
    with pytest.raises(ValueError, match="invalid_registration"):
        TargetDefinition("local-echo", model)


def test_trusted_model_and_composition_share_config(tmp_path, monkeypatch):
    monkeypatch.setenv("CONTROL_LAYER_OLLAMA_MODEL", "qwen2.5:0.5b")
    registry = default_targets()
    binding = registry.resolve("local-ollama")
    assert binding.definition.model_id == binding.adapter.settings.model
    assert registry.resolve("local-echo").definition.model_id is None
    service, store, _, _, _ = composition(tmp_path, model="operator-model:v1")
    result = service.evaluate(Interaction.create("local-echo", CANARY))
    assert store.get_event(result.interaction_id).event.model_id == "operator-model:v1"
    store.close()


def test_unknown_completion_restart_and_exact_aggregates(tmp_path):
    service, store, sink, _, _ = composition(tmp_path)
    when = datetime(2026, 10, 4, tzinfo=UTC)
    # Three decisions: repeated REDACT findings, succeeded ALLOW, unknown ALLOW.
    redacted = audit(service, Action.REDACT, timestamp=when, counts=(("pii.email", 3),))
    succeeded = audit(service, timestamp=when + timedelta(seconds=1))
    unknown = audit(service, timestamp=when + timedelta(seconds=2))
    for event in (redacted, succeeded, unknown):
        sink.emit(event)
    sink.complete(redacted.interaction_id, InvocationStatus.FAILED, 4.0, 8.0)
    sink.complete(succeeded.interaction_id, InvocationStatus.SUCCEEDED, 6.0, 10.0)
    # Historical different policy includes BLOCK without changing today's registry.
    blocked = replace(
        redacted, interaction_id=uuid4(), action=Action.BLOCK, forwarding_eligible=False
    )
    block_service, _, block_sink, _, _ = composition(tmp_path / "block", Action.BLOCK)
    blocked = replace(blocked, policy_digest=block_service.policy.digest)
    sink.store._append_event(block_sink.projection.project(blocked))
    block_sink.store.close()
    operational = replace(
        audit(service),
        timestamp=when,
        event_type="operational_failure",
        action=None,
        finding_counts=(),
        error_code="evaluation_failed",
        forwarding_eligible=False,
        evaluated_controls=(),
    )
    sink.emit(operational)
    store.close()
    store = ReportingStore(tmp_path / "db.sqlite3")
    filters = EventFilter(when, when + timedelta(days=1))
    summary = store.summarize(filters, group_by=GroupBy.ACTION)
    overall = summary.overall
    assert overall.interaction_total == 5
    assert dict(overall.actions) == {Action.ALLOW: 2, Action.REDACT: 1, Action.BLOCK: 1}
    assert overall.operational_failure_total == 1
    assert dict(overall.invocations) == {
        InvocationStatus.SUCCEEDED: 1,
        InvocationStatus.FAILED: 1,
        InvocationStatus.UNKNOWN: 1,
        InvocationStatus.NOT_INVOKED: 2,
    }
    assert overall.findings[0].occurrences == 6
    assert overall.findings[0].affected_interactions == 2
    assert overall.evaluation.samples == 5 and overall.evaluation.mean_ms == 2.0
    assert overall.invocation.samples == 2 and overall.invocation.mean_ms == 5.0
    assert overall.invocation.min_ms == 4.0 and overall.invocation.max_ms == 6.0
    assert overall.total.mean_ms == 9.0
    assert len(summary.groups) == 4
    assert sum(g.summary.interaction_total for g in summary.groups) == 5
    assert (
        store.get_event(unknown.interaction_id).invocation_status
        == InvocationStatus.UNKNOWN
    )
    assert store.get_event(uuid4()) is None
    page = store.list_events(limit=2)
    second = store.list_events(limit=2, after_sequence=page[-1].sequence)
    assert len({e.sequence for e in (*page, *second)}) == 4
    assert (
        store.list_events(EventFilter(action=Action.BLOCK))[0].event.action
        == Action.BLOCK
    )
    assert (
        len(store.list_events(EventFilter(invocation_status=InvocationStatus.UNKNOWN)))
        == 1
    )
    empty = store.summarize(
        EventFilter(when + timedelta(days=2), when + timedelta(days=3))
    ).overall
    assert empty.interaction_total == 0
    assert empty.invocation.samples == 0 and empty.invocation.mean_ms is None
    assert store.list_events(EventFilter(target_id="historical-target")) == ()
    # Half-open upper boundary excludes the event at the boundary.
    assert (
        store.summarize(
            EventFilter(when, when + timedelta(seconds=1))
        ).overall.interaction_total
        == 3
    )
    store.close()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"action": "ALLOW"},
        {"target_id": "x' OR 1=1--"},
        {"invocation_status": "succeeded"},
        {"from_time": datetime.now(UTC)},
        {"from_time": datetime.now(), "to_time": datetime.now()},
        {"from_time": "bad", "to_time": "bad"},
    ],
)
def test_filter_validation_is_fixed_and_no_reflection(kwargs):
    with pytest.raises(ReportingError, match="^invalid_reporting_query$"):
        EventFilter(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": True},
        {"limit": 0},
        {"limit": 1001},
        {"after_sequence": True},
        {"after_sequence": 0},
    ],
)
def test_query_limit_validation(tmp_path, kwargs):
    store = ReportingStore(tmp_path / "db")
    with pytest.raises(ReportingError, match="^invalid_reporting_query$"):
        store.list_events(**kwargs)
    with pytest.raises(ReportingError, match="^invalid_reporting_query$"):
        store.summarize(EventFilter())
    with pytest.raises(ReportingError, match="^invalid_reporting_query$"):
        store.summarize(
            EventFilter(datetime.now(UTC), datetime.now(UTC) + timedelta(days=32))
        )
    with pytest.raises(ReportingError, match="^invalid_reporting_query$"):
        store.summarize(window(), group_by="action; DROP TABLE audit_events")
    store.close()


def test_concurrent_requests_keep_separate_evidence(tmp_path):
    service, store, _, target, _ = composition(tmp_path)
    interactions = [Interaction.create("local-echo", f"clean {i}") for i in range(24)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(service.evaluate, interactions))
    assert all(r.error_code is None for r in results)
    assert len(target.calls) == 24
    assert {e.event.interaction_id for e in store.list_events()} == {
        i.id for i in interactions
    }
    assert all(
        e.invocation_status == InvocationStatus.SUCCEEDED for e in store.list_events()
    )
    store.close()


def test_duplicate_orphan_and_block_outcome_rejection(tmp_path):
    service, store, sink, _, _ = composition(tmp_path)
    event = audit(service)
    sink.emit(event)
    with pytest.raises(ReportingError):
        store._append_event(sink.projection.project(event))
    assert len(store.list_events()) == 1
    assert store.health == "reporting_write_failed"
    store.close()
    for kind in ("orphan", "blocked", "duplicate"):
        folder = tmp_path / kind
        service, store, sink, _, _ = composition(folder, Action.BLOCK)
        event = audit(service, Action.BLOCK, counts=(("pii.email", 1),))
        if kind == "blocked":
            sink.emit(event)
        if kind == "duplicate":
            event = audit(service)
            sink.emit(event)
            store._append_completion(
                Completion(
                    event.interaction_id,
                    datetime.now(UTC),
                    InvocationStatus.SUCCEEDED,
                    1,
                    2,
                )
            )
        with pytest.raises(ReportingError):
            store._append_completion(
                Completion(
                    event.interaction_id,
                    datetime.now(UTC),
                    InvocationStatus.FAILED,
                    1,
                    2,
                )
            )
        store.close()


def test_atomic_rollback_and_gate_failure(tmp_path):
    service, store, _, target, _ = composition(tmp_path)
    store._connection.execute(
        "CREATE TRIGGER fail_child BEFORE INSERT ON event_controls "
        "BEGIN SELECT RAISE(ABORT,'UNSAFE_CANARY'); END"
    )
    for _ in range(2):
        result = service.evaluate(Interaction.create("local-echo", CANARY))
        assert result.error_code == "audit_failed"
    assert not target.calls
    assert store.list_events() == ()
    assert store.health == "reporting_write_failed"
    store.close()


def test_completion_failure_preserves_outcome_and_poison_gate(tmp_path, monkeypatch):
    service, store, _, target, _ = composition(tmp_path)

    def fail(completion):
        raise RuntimeError(CANARY)

    monkeypatch.setattr(store, "_append_completion", fail)
    first = service.evaluate(Interaction.create("local-echo", "clean"))
    assert first.target_result is not None and first.error_code is None
    assert (
        store.get_event(first.interaction_id).invocation_status
        == InvocationStatus.UNKNOWN
    )
    second = service.evaluate(Interaction.create("local-echo", "clean"))
    assert second.error_code == "audit_failed"
    assert len(target.calls) == 1 and store.health == "reporting_write_failed"
    store.close()


@pytest.mark.parametrize("phase", ["gate", "completion"])
def test_committed_then_raised_never_retries_or_deletes(tmp_path, monkeypatch, phase):
    service, store, _, target, _ = composition(tmp_path)
    method = "_append_event" if phase == "gate" else "_append_completion"
    original = getattr(store, method)

    def commit_then_raise(record):
        original(record)
        raise RuntimeError(CANARY)

    monkeypatch.setattr(store, method, commit_then_raise)
    result = service.evaluate(Interaction.create("local-echo", "clean"))
    event = store.get_event(result.interaction_id)
    assert event.invocation_status == (
        InvocationStatus.UNKNOWN if phase == "gate" else InvocationStatus.SUCCEEDED
    )
    assert len(target.calls) == (0 if phase == "gate" else 1)
    assert result.error_code == ("audit_failed" if phase == "gate" else None)
    assert (
        service.evaluate(Interaction.create("local-echo", "clean")).error_code
        == "audit_failed"
    )
    assert len(store.list_events()) == 1
    store.close()


def test_read_failure_does_not_poison_writes(tmp_path):
    service, store, sink, _, _ = composition(tmp_path)
    with pytest.raises(ReportingError, match="^reporting_unavailable$"):
        with store._read() as db:
            db.execute("SELECT * FROM absent_table")
    assert store.health == "healthy"
    sink.emit(audit(service))
    store.close()
    with pytest.raises(ReportingError, match="^reporting_unavailable$"):
        store.list_events()


@pytest.mark.parametrize("path", ["", ":memory:", "file:unsafe?mode=memory"])
def test_reject_non_file_configuration(path):
    with pytest.raises(ReportingError, match="^invalid_reporting_configuration$"):
        ReportingStore(path)


def test_schema_mismatch_symlink_and_private_defaults(tmp_path):
    path = tmp_path / "new" / "db"
    store = ReportingStore(path)
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    store.close()
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(ReportingError, match="^reporting_unavailable$"):
        ReportingStore(link)
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA user_version=999")
    before = path.read_bytes()
    with pytest.raises(ReportingError, match="^invalid_reporting_configuration$"):
        ReportingStore(path)
    assert path.read_bytes() == before


@pytest.mark.parametrize("mismatch", ["columns", "constraint", "trigger"])
def test_incompatible_version_one_schema_fails_startup(tmp_path, mismatch):
    path = tmp_path / "incompatible.sqlite3"
    if mismatch == "columns":
        with sqlite3.connect(path) as db:
            db.execute("PRAGMA user_version=1")
            for table in (
                "audit_events",
                "event_controls",
                "event_findings",
                "invocation_outcomes",
            ):
                db.execute(f"CREATE TABLE {table} (wrong_column TEXT)")
    else:
        store = ReportingStore(path)
        store.close()
        with sqlite3.connect(path) as db:
            if mismatch == "trigger":
                db.execute("DROP TRIGGER eligible_outcome")
            else:
                # Same columns, different structural guarantee.
                db.execute("DROP TABLE event_findings")
                db.execute("""CREATE TABLE event_findings (
                    interaction_id TEXT NOT NULL
                    REFERENCES audit_events(interaction_id),
                    control_id TEXT NOT NULL, code TEXT NOT NULL,
                    action TEXT NOT NULL CHECK(action IN ('ALLOW','REDACT','BLOCK')),
                    count INTEGER NOT NULL, PRIMARY KEY(interaction_id,code))""")
    before = path.read_bytes()
    with pytest.raises(ReportingError, match="^invalid_reporting_configuration$"):
        ReportingStore(path)
    assert path.read_bytes() == before
