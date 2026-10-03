import hashlib
import io
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Lock

import pytest

from app.control_layer.audit import JsonLinesAuditSink
from app.control_layer.composition import default_controls
from app.control_layer.domain import Action, Finding, Interaction, Span
from app.control_layer.policy import load_policy
from app.control_layer.registry import ControlRegistration, ControlRegistry
from app.control_layer.service import InteractionService
from app.control_layer.targets import (
    LocalEchoTarget,
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
    TargetResult,
)


class SpyTarget:
    def __init__(self, stream, fail=False):
        self.stream = stream
        self.calls = []
        self.fail = fail
        self.lock = Lock()

    def invoke(self, interaction):
        with self.lock:
            records = [json.loads(line) for line in self.stream.getvalue().splitlines()]
            assert any(r["interaction_id"] == str(interaction.id) for r in records)
            self.calls.append(interaction)
        if self.fail:
            raise RuntimeError("RAW_TARGET_SECRET alice@example.com")
        return TargetResult(interaction.content)


class FakeControl:
    id = "email-address"

    def __init__(self, output=(), fail=False):
        self.output = output
        self.fail = fail
        self.calls = 0

    def evaluate(self, interaction):
        self.calls += 1
        if self.fail:
            raise RuntimeError("RAW_CONTROL_SECRET alice@example.com")
        return self.output


def make_service(action=Action.REDACT, enabled=True, control=None, target_fail=False):
    registry = ControlRegistry((default_controls().registrations[0],))
    if control is not None:
        registry = ControlRegistry(
            (ControlRegistration(registry.registrations[0].definition, control),)
        )
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "policy.yaml"
        path.write_text(
            "version: 1\npolicy_id: test\ncontrols:\n  email-address:\n"
            f"    enabled: {str(enabled).lower()}\n    findings:\n"
            f"      pii.email: {action.value}\n"
        )
        policy = load_policy(path, registry)
    stream = io.StringIO()
    target = SpyTarget(stream, fail=target_fail)
    service = InteractionService(
        policy,
        JsonLinesAuditSink(stream),
        TargetRegistry((RegisteredTarget(TargetDefinition("local-echo"), target),)),
    )
    return service, target, stream


@pytest.mark.parametrize("action", list(Action))
def test_policy_actions_dispatch_once_after_audit(action):
    service, target, stream = make_service(action)
    interaction = Interaction.create("local-echo", "  Hi <alice@example.com>!  ")
    outcome = service.evaluate(interaction)
    assert outcome.error_code is None
    assert outcome.decision.action == action
    assert outcome.interaction_id == interaction.id
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert len(records) == 1
    assert records[0]["action"] == action.value
    assert records[0]["forwarding_eligible"] == (action != Action.BLOCK)
    if action == Action.BLOCK:
        assert target.calls == []
        assert outcome.target_result is None
    elif action == Action.ALLOW:
        assert target.calls == [interaction]
        assert target.calls[0] is interaction
        assert outcome.target_result.content == interaction.content
    else:
        assert len(target.calls) == 1
        assert target.calls[0].content == "  Hi <[REDACTED]>!  "
        assert target.calls[0].id == interaction.id
        assert target.calls[0] is not interaction
        assert outcome.target_result.content == target.calls[0].content
        assert interaction.content == "  Hi <alice@example.com>!  "


def test_no_findings_preserves_original_and_echo_adapter():
    service, target, _ = make_service()
    interaction = Interaction.create("local-echo", "  🙂 e\u0301\n")
    outcome = service.evaluate(interaction)
    assert outcome.decision.action == Action.ALLOW
    assert outcome.decision.reason_code == "no_findings"
    assert target.calls[0] is interaction
    assert LocalEchoTarget().invoke(interaction).content == interaction.content


def test_disabled_control_is_never_evaluated_and_has_explicit_status():
    control = FakeControl(fail=True)
    service, target, stream = make_service(enabled=False, control=control)
    interaction = Interaction.create("local-echo", "alice@example.com")
    outcome = service.evaluate(interaction)
    assert control.calls == 0
    assert outcome.decision.action == Action.ALLOW
    assert target.calls == [interaction]
    record = json.loads(stream.getvalue())
    assert record["control_status"] == {"email-address": False}
    assert record["evaluated_controls"] == []


def test_audit_allowlist_excludes_sensitive_content_and_spans():
    service, _, stream = make_service()
    interaction = Interaction.create("local-echo", "RAW_SECRET alice@example.com")
    service.evaluate(interaction)
    raw = stream.getvalue()
    record = json.loads(raw)
    assert set(record) == {
        "event_type",
        "interaction_id",
        "timestamp",
        "target_id",
        "policy_digest",
        "evaluated_controls",
        "control_status",
        "forwarding_eligible",
        "evaluation_duration_ms",
        "action",
        "finding_counts",
    }
    assert record["event_type"] == "decision"
    assert record["control_status"] == {"email-address": True}
    assert record["evaluated_controls"] == ["email-address"]
    assert record["finding_counts"] == {"pii.email": 1}
    assert record["timestamp"].endswith("+00:00")
    assert record["target_id"] == "local-echo"
    assert record["evaluation_duration_ms"] >= 0
    for value in (
        interaction.content,
        "RAW_SECRET",
        "alice@example.com",
        hashlib.sha256(interaction.content.encode()).hexdigest(),
        "span",
        "snippet",
        "content_hash",
        "target_success",
        "completion",
    ):
        assert value not in raw


def test_concurrent_requests_emit_complete_lines_before_corresponding_dispatch():
    service, target, stream = make_service()
    interactions = [Interaction.create("local-echo", f"request {n}") for n in range(40)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(service.evaluate, interactions))
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert len(records) == len(interactions) == len(target.calls)
    assert {r["interaction_id"] for r in records} == {str(i.id) for i in interactions}
    assert all(o.error_code is None for o in outcomes)


class BrokenStream(io.StringIO):
    def __init__(self, failure):
        super().__init__()
        self.failure = failure
        self.write_calls = 0
        self.flush_calls = 0

    def write(self, line):
        self.write_calls += 1
        if self.failure == "partial_exception":
            super().write(line[:12])
            raise RuntimeError("RAW_SINK_SECRET")
        if self.failure == "short_count":
            super().write(line[:12])
            return 12
        return super().write(line)

    def flush(self):
        self.flush_calls += 1
        if self.failure == "flush_exception":
            raise RuntimeError("RAW_SINK_SECRET")
        super().flush()


@pytest.mark.parametrize(
    "failure", ["partial_exception", "short_count", "flush_exception"]
)
@pytest.mark.parametrize("action", [Action.ALLOW, Action.REDACT])
def test_sink_failure_poisoning_prevents_first_and_subsequent_dispatch(failure, action):
    service, target, _ = make_service(action)
    stream = BrokenStream(failure)
    service.audit_sink = JsonLinesAuditSink(stream)
    for _ in range(2):
        outcome = service.evaluate(
            Interaction.create("local-echo", "alice@example.com")
        )
        assert outcome.error_code == "audit_failed"
        assert outcome.decision is None
        assert outcome.target_result is None
        assert "RAW_SINK_SECRET" not in repr(outcome)
    assert target.calls == []
    assert stream.write_calls == 1
    assert stream.flush_calls == (1 if failure == "flush_exception" else 0)


@pytest.mark.parametrize(
    "output",
    [
        [],
        ("RAW_SECRET",),
        (Finding("forged", "pii.email", Span(0, 1)),),
        (Finding("email-address", "RAW_SECRET", Span(0, 1)),),
        (Finding("email-address", "pii.email", None),),
        (Finding("email-address", "pii.email", Span(-1, 2)),),
        (Finding("email-address", "pii.email", Span(2, 2)),),
        (Finding("email-address", "pii.email", Span(0, 1000)),),
        (Finding("email-address", "pii.email", Span(True, 2)),),
        (Finding("email-address", "pii.email", Span(0, 1.5)),),
    ],
)
def test_invalid_control_contract_is_operational_without_synthetic_findings(output):
    service, target, stream = make_service(control=FakeControl(output))
    outcome = service.evaluate(
        Interaction.create("local-echo", "RAW_SECRET alice@example.com")
    )
    assert outcome.error_code == "evaluation_failed"
    assert outcome.decision is None
    assert outcome.target_result is None
    assert target.calls == []
    record = json.loads(stream.getvalue())
    assert record["event_type"] == "operational_failure"
    assert record["error_code"] == "evaluation_failed"
    assert record["forwarding_eligible"] is False
    assert "action" not in record
    assert "finding_counts" not in record
    assert "RAW_SECRET" not in stream.getvalue()
    assert "alice@example.com" not in stream.getvalue()


def test_control_exception_is_sanitized_with_safe_operational_event():
    service, target, stream = make_service(control=FakeControl(fail=True))
    outcome = service.evaluate(Interaction.create("local-echo", "alice@example.com"))
    assert outcome.error_code == "evaluation_failed"
    assert outcome.decision is None
    assert target.calls == []
    assert json.loads(stream.getvalue())["event_type"] == "operational_failure"
    assert "RAW_CONTROL_SECRET" not in stream.getvalue() + repr(outcome)


@pytest.mark.parametrize(
    "mappings",
    [
        (),
        (("pii.email", "REDACT"),),
        (("pii.email", Action.REDACT), ("pii.email", Action.ALLOW)),
    ],
)
def test_inconsistent_policy_mapping_stops_dispatch(mappings):
    service, target, stream = make_service()
    service.policy = replace(
        service.policy, entries=(replace(service.policy.entries[0], mappings=mappings),)
    )
    outcome = service.evaluate(Interaction.create("local-echo", "alice@example.com"))
    assert outcome.error_code == "evaluation_failed"
    assert outcome.decision is None
    assert target.calls == []
    assert "action" not in json.loads(stream.getvalue())


def test_evaluation_failure_with_unavailable_sink_still_stops_dispatch():
    service, target, _ = make_service(control=FakeControl(fail=True))
    service.audit_sink = JsonLinesAuditSink(BrokenStream("flush_exception"))
    outcome = service.evaluate(Interaction.create("local-echo", "alice@example.com"))
    assert outcome.error_code == "evaluation_failed"
    assert outcome.decision is None
    assert target.calls == []


@pytest.mark.parametrize("action", [Action.ALLOW, Action.REDACT])
def test_target_failure_is_sanitized_after_decision_event_without_completion_claim(
    action,
):
    service, target, stream = make_service(action, target_fail=True)
    outcome = service.evaluate(Interaction.create("local-echo", "alice@example.com"))
    assert outcome.error_code == "target_failed"
    assert outcome.decision.action == action
    assert outcome.target_result is None
    assert len(target.calls) == 1
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert len(records) == 1
    assert records[0]["event_type"] == "decision"
    assert records[0]["forwarding_eligible"] is True
    for value in ("RAW_TARGET_SECRET", "alice@example.com", "completion", "success"):
        assert value not in stream.getvalue() + repr(outcome)
