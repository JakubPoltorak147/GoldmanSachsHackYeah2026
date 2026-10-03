import json

import pytest

from app.control_layer.targets import (
    LocalEchoTarget,
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
    TargetResult,
)
from scripts import smoke_local_model as smoke


def registry(target):
    return TargetRegistry(
        (
            RegisteredTarget(TargetDefinition("local-echo"), LocalEchoTarget()),
            RegisteredTarget(TargetDefinition("local-ollama"), target),
        )
    )


class TextTarget:
    def __init__(self, result="RAW_OUTPUT", fail=False):
        self.result, self.fail = result, fail
        self.calls = []

    def invoke(self, interaction):
        self.calls.append(interaction)
        if self.fail:
            raise RuntimeError("RAW_PROMPT RAW_OUTPUT http://private")
        return TargetResult(self.result)


@pytest.mark.parametrize("text", ["", "RAW_OUTPUT", "😀"])
def test_smoke_success_no_content_print(text, capsys):
    target = TextTarget(text)
    assert smoke.main(registry(target)) == 0
    output = capsys.readouterr().out
    assert "SMOKE PASS" in output and f"length={len(text)}" in output
    assert "RAW_" not in output and "sunrise" not in output
    assert len(target.calls) == 1


@pytest.mark.parametrize("target", [TextTarget(fail=True), TextTarget("\ud800")])
def test_smoke_fixed_nonzero_failure_privacy(target, capsys):
    assert smoke.main(registry(target)) == 1
    assert capsys.readouterr().out == (
        "SMOKE FAIL — prerequisites unavailable or verification failed\n"
    )


def test_smoke_configuration_failure_sanitized(monkeypatch, capsys):
    monkeypatch.setenv("CONTROL_LAYER_OLLAMA_MODEL", "RAW_SECRET")
    assert smoke.main() == 1
    assert "RAW_SECRET" not in capsys.readouterr().out


@pytest.mark.parametrize(
    "body,status",
    [
        ({}, 502),
        ({"action": "BLOCK"}, 200),
        ({"action": "ALLOW", "interaction_id": "id", "result": {"content": 3}}, 200),
        (
            {
                "action": "ALLOW",
                "interaction_id": "id",
                "result": {"content": "x", "extra": True},
            },
            200,
        ),
        (
            {
                "action": "ALLOW",
                "interaction_id": "id",
                "result": {"content": "\udfff"},
            },
            200,
        ),
    ],
)
def test_result_checks_reject_invalid_shapes(body, status):
    import httpx

    sink = smoke.RecordingSink()
    sink.records = [
        {"interaction_id": "id", "action": "ALLOW", "forwarding_eligible": True}
    ]
    with pytest.raises(ValueError, match="^smoke_failed$"):
        smoke.check_result(
            httpx.Response(status, content=json.dumps(body).encode()), "ALLOW", sink
        )


def test_observer_requires_audit_before_dispatch():
    target = TextTarget()
    observer = smoke.ObservedTarget(
        registry(target).resolve("local-ollama"), smoke.RecordingSink()
    )
    from app.control_layer.domain import Interaction

    with pytest.raises(ValueError, match="^smoke_failed$"):
        observer.invoke(Interaction.create("local-ollama", "RAW_PROMPT"))
    assert target.calls == []
