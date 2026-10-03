import io
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
import yaml

from app.control_layer.audit import JsonLinesAuditSink
from app.control_layer.domain import Finding, Interaction
from app.control_layer.policy import load_policy
from app.control_layer.registry import (
    ControlDefinition,
    ControlRegistration,
    ControlRegistry,
    FindingDefinition,
)
from app.control_layer.service import InteractionService
from app.control_layer.targets import (
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
    TargetResult,
)


class Control:
    def __init__(self, output=()):
        self.output = output
        self.calls = 0

    def evaluate(self, interaction):
        self.calls += 1
        return self.output


class Target:
    def __init__(self, stream, identifier):
        self.stream = stream
        self.identifier = identifier
        self.calls = []

    def invoke(self, interaction):
        records = [json.loads(line) for line in self.stream.getvalue().splitlines()]
        record = next(r for r in records if r["interaction_id"] == str(interaction.id))
        assert record["target_id"] == self.identifier
        self.calls.append(interaction)
        return TargetResult(interaction.content)


def setup(tmp_path, action="ALLOW", output=None):
    control = Control((Finding("sample", "sample.code"),) if output is None else output)
    registration = ControlRegistration(
        ControlDefinition("sample", [FindingDefinition("sample.code", False, False)]),
        control,
    )
    registry = ControlRegistry([registration])
    path = tmp_path / "policy.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "policy_id": "test",
                "controls": {
                    "sample": {"enabled": True, "findings": {"sample.code": action}}
                },
            }
        )
    )
    bound = load_policy(path, registry)
    stream = io.StringIO()
    targets = [Target(stream, identifier) for identifier in ("first", "second")]
    target_registry = TargetRegistry(
        [RegisteredTarget(TargetDefinition(t.identifier), t) for t in targets]
    )
    return (
        InteractionService(bound, JsonLinesAuditSink(stream), target_registry),
        control,
        targets,
        stream,
    )


def test_two_targets_and_retained_binding_after_audit(tmp_path, monkeypatch):
    service, control, targets, stream = setup(tmp_path)
    resolved = []
    original = TargetRegistry.resolve

    def resolve(self, identifier):
        resolved.append(identifier)
        return original(self, identifier)

    monkeypatch.setattr(TargetRegistry, "resolve", resolve)
    original_emit = service.audit_sink.emit

    class Sink:
        def emit(self, event):
            original_emit(event)
            service.targets = TargetRegistry([])

    initial = service.targets
    service.audit_sink = Sink()
    for identifier in ("first", "second"):
        service.targets = initial
        interaction = Interaction.create(identifier, "text")
        outcome = service.evaluate(interaction)
        assert outcome.error_code is None
        assert outcome.decision.resolutions[0].finding.code == "sample.code"
    assert resolved == ["first", "second"]
    assert control.calls == 2
    assert all(len(t.calls) == 1 for t in targets)
    assert [
        json.loads(line)["target_id"] for line in stream.getvalue().splitlines()
    ] == ["first", "second"]


@pytest.mark.parametrize(
    "identifier", ["https://host/RAW_SECRET", "RAW_SECRET", "unresolved", None, []]
)
def test_unknown_target_has_no_evaluations_or_calls_and_safe_audit(
    tmp_path, identifier
):
    service, control, targets, stream = setup(tmp_path)
    outcome = service.evaluate(Interaction.create(identifier, "RAW_SECRET"))
    assert outcome.error_code == "evaluation_failed"
    assert outcome.decision is None
    assert control.calls == 0
    assert all(t.calls == [] for t in targets)
    record = json.loads(stream.getvalue())
    assert record["target_id"] == "unresolved"
    assert record["evaluated_controls"] == []
    assert "action" not in record and "finding_counts" not in record
    assert "RAW_SECRET" not in stream.getvalue() + repr(outcome)


@pytest.mark.parametrize(
    "action,output",
    [
        ("BLOCK", None),
        ("ALLOW", (Finding("forged", "sample.code"),)),
        ("ALLOW", (Finding("sample", "RAW_SECRET"),)),
    ],
)
def test_block_and_invalid_output_do_not_dispatch(tmp_path, action, output):
    service, _, targets, stream = setup(tmp_path, action, output)
    outcome = service.evaluate(Interaction.create("second", "RAW_SECRET"))
    assert all(t.calls == [] for t in targets)
    record = json.loads(stream.getvalue())
    assert record["target_id"] == "second"
    if action == "BLOCK":
        assert outcome.decision.action.value == "BLOCK"
    else:
        assert outcome.error_code == "evaluation_failed"
        assert record["evaluated_controls"] == []
        assert "finding_counts" not in record and "action" not in record
        assert "forged" not in stream.getvalue()
    assert "RAW_SECRET" not in stream.getvalue()


def test_concurrent_multiple_target_audit_and_dispatch(tmp_path):
    service, _, targets, stream = setup(tmp_path)
    interactions = [
        Interaction.create("first" if i % 2 else "second", "text") for i in range(40)
    ]
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(service.evaluate, interactions))
    assert all(o.error_code is None for o in outcomes)
    assert len(stream.getvalue().splitlines()) == 40
    assert [len(t.calls) for t in targets] == [20, 20]


def test_failed_audit_no_target_calls(tmp_path):
    service, _, targets, _ = setup(tmp_path)

    class FailedSink:
        def emit(self, event):
            raise RuntimeError("RAW_SECRET")

    service.audit_sink = FailedSink()
    assert (
        service.evaluate(Interaction.create("second", "text")).error_code
        == "audit_failed"
    )
    assert all(t.calls == [] for t in targets)


@pytest.mark.parametrize("result", [None, "RAW_SECRET", TargetResult(1)])
def test_invalid_target_results_sanitized_after_audit(tmp_path, result):
    service, _, targets, stream = setup(tmp_path)
    targets[0].invoke = lambda interaction: result
    outcome = service.evaluate(Interaction.create("first", "text"))
    assert outcome.error_code == "target_failed"
    assert outcome.target_result is None
    record = json.loads(stream.getvalue())
    assert record["event_type"] == "decision"
    assert "target_success" not in record
    assert "RAW_SECRET" not in repr(outcome) + stream.getvalue()


@pytest.mark.parametrize("failure", ["short", "flush"])
def test_generic_sink_poisoning(failure, tmp_path):
    service, _, targets, _ = setup(tmp_path)

    class Broken(io.StringIO):
        writes = 0

        def write(self, line):
            self.writes += 1
            if failure == "short":
                return super().write(line[:1])
            return super().write(line)

        def flush(self):
            if failure == "flush":
                raise RuntimeError("RAW_SECRET")

    stream = Broken()
    service.audit_sink = JsonLinesAuditSink(stream)
    for identifier in ("first", "second"):
        assert (
            service.evaluate(Interaction.create(identifier, "text")).error_code
            == "audit_failed"
        )
    assert stream.writes == 1
    assert all(t.calls == [] for t in targets)


def test_unknown_target_with_failed_operational_sink(tmp_path):
    service, control, targets, _ = setup(tmp_path)

    class Failed:
        def emit(self, event):
            raise RuntimeError("RAW_SECRET")

    service.audit_sink = Failed()
    outcome = service.evaluate(Interaction.create("https://RAW_SECRET", "text"))
    assert outcome.error_code == "evaluation_failed"
    assert control.calls == 0
    assert all(t.calls == [] for t in targets)
