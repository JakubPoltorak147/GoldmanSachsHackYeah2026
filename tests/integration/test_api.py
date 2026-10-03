import asyncio
import io
import json
from uuid import UUID

import httpx
import pytest

from app.control_layer.api import create_app
from app.control_layer.audit import JsonLinesAuditSink
from app.control_layer.composition import default_controls
from app.control_layer.domain import Finding, PolicyError, Span
from app.control_layer.registry import ControlRegistration, ControlRegistry
from app.control_layer.targets import (
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

    def invoke(self, interaction):
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


class FailingSink:
    def emit(self, event):
        raise RuntimeError("RAW_AUDIT_SECRET alice@example.com")


def setup_app(
    tmp_path, action="REDACT", enabled=True, control=None, sink=None, target_fail=False
):
    path = tmp_path / "policy.yaml"
    path.write_text(
        "version: 1\npolicy_id: test-policy\ncontrols:\n  email-address:\n"
        f"    enabled: {str(enabled).lower()}\n    findings:\n"
        f"      pii.email: {action}\n"
    )
    stream = io.StringIO()
    target = SpyTarget(stream, target_fail)
    app = create_app(
        policy_path=path,
        audit_sink=sink or JsonLinesAuditSink(stream),
        target_registry=TargetRegistry(
            (RegisteredTarget(TargetDefinition("local-echo"), target),)
        ),
        control_registry=None
        if control is None
        else ControlRegistry(
            (
                ControlRegistration(
                    default_controls().registrations[0].definition, control
                ),
            )
        ),
    )
    return app, target, stream


def request(app, **kwargs):
    async def run():
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                return await client.post("/v1/interactions", **kwargs)

    return asyncio.run(run())


def payload(content):
    return {"target_id": "local-echo", "content": content}


@pytest.mark.parametrize("content", ["  🙂 e\u0301\n  ", " ", "🙂" * 16384])
def test_allowed_exact_content_and_character_limit(tmp_path, content):
    app, target, stream = setup_app(tmp_path)
    response = request(app, json=payload(content))
    assert response.status_code == 200
    body = response.json()
    UUID(body["interaction_id"])
    assert body["action"] == "ALLOW"
    assert body["result"]["content"] == content
    assert len(target.calls) == 1
    assert target.calls[0].content == content
    assert body["interaction_id"] == str(target.calls[0].id)
    assert "content" not in json.loads(stream.getvalue())


@pytest.mark.parametrize(
    "action,status,expected",
    [
        ("ALLOW", 200, "  Contact <alice@example.com>!  "),
        ("REDACT", 200, "  Contact <[REDACTED]>!  "),
        ("BLOCK", 403, None),
    ],
)
def test_policy_http_mapping_and_dispatch_audit_order(
    tmp_path, action, status, expected
):
    app, target, stream = setup_app(tmp_path, action)
    response = request(app, json=payload("  Contact <alice@example.com>!  "))
    assert response.status_code == status
    body = response.json()
    assert body["action"] == action
    assert "pii.email" in response.text
    assert len(target.calls) == (0 if expected is None else 1)
    if expected is not None:
        assert target.calls[0].content == expected
        assert body["result"]["content"] == expected
    else:
        assert "alice@example.com" not in response.text
        assert body.get("result") is None
    if action == "REDACT":
        assert "alice@example.com" not in response.text
    record = json.loads(stream.getvalue())
    assert record["action"] == action
    assert record["forwarding_eligible"] == (action != "BLOCK")
    assert "alice@example.com" not in stream.getvalue()
    assert "span" not in stream.getvalue()


@pytest.mark.parametrize(
    "invalid",
    [
        {},
        {"target_id": "local-echo"},
        {"content": "RAW_SECRET"},
        {"target_id": "local-echo", "content": ""},
        {"target_id": "local-echo", "content": "🙂" * 16385},
        {"target_id": "https://evil.example", "content": "RAW_SECRET"},
        {"target_id": "local-echo", "content": 123},
        {"target_id": "local-echo", "content": True},
        {"target_id": "local-echo", "content": None},
        {"target_id": "local-echo", "content": ["RAW_SECRET"]},
        {"target_id": "local-echo", "content": {"secret": "RAW_SECRET"}},
        {"target_id": 123, "content": "RAW_SECRET"},
        {"target_id": None, "content": "RAW_SECRET"},
        {"target_id": ["local-echo"], "content": "RAW_SECRET"},
        {"target_id": "local-echo", "content": "RAW_SECRET", "principal": "admin"},
        {"target_id": "local-echo", "content": "RAW_SECRET", "id": "caller-id"},
        {"target_id": "local-echo", "content": "RAW_SECRET", "metadata": {}},
        [],
        "RAW_SECRET",
        None,
    ],
)
def test_invalid_shape_never_dispatches_or_reflects_input(tmp_path, invalid):
    app, target, stream = setup_app(tmp_path)
    response = request(
        app, content=json.dumps(invalid), headers={"content-type": "application/json"}
    )
    assert response.status_code == 422
    assert target.calls == []
    assert stream.getvalue() == ""
    assert "RAW_SECRET" not in response.text
    assert "caller-id" not in response.text
    assert "evil.example" not in response.text
    assert "input" not in response.text


@pytest.mark.parametrize(
    "raw",
    [
        b'{"target_id":"local-echo","content":"RAW_SECRET alice@example.com",',
        b'{"target_id":"local-echo","content":"\\ud800"}',
        b'{"target_id":"local-echo","content":"\\udfff"}',
        b'{"target_id":"local-echo","content":"RAW_SECRET\xff"}',
    ],
)
def test_malformed_json_unicode_is_sanitized(tmp_path, raw):
    app, target, stream = setup_app(tmp_path)
    response = request(app, content=raw, headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert target.calls == []
    assert stream.getvalue() == ""
    assert "RAW_SECRET" not in response.text
    assert "alice@example.com" not in response.text
    assert "decode" not in response.text.lower()


def test_surrogate_pair_decodes_to_valid_scalar(tmp_path):
    app, target, _ = setup_app(tmp_path)
    response = request(
        app,
        content=b'{"target_id":"local-echo","content":"\\ud83d\\ude42"}',
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 200
    assert target.calls[0].content == "🙂"


@pytest.mark.parametrize(
    "control",
    [
        FakeControl(fail=True),
        FakeControl((Finding("email-address", "pii.email", Span(-1, 2)),)),
        FakeControl((Finding("email-address", "unmapped.secret", Span(0, 1)),)),
    ],
)
def test_evaluation_failures_have_no_decision_and_never_dispatch(tmp_path, control):
    app, target, stream = setup_app(tmp_path, control=control)
    response = request(app, json=payload("RAW_SECRET alice@example.com"))
    assert response.status_code == 503
    assert target.calls == []
    assert response.json().get("action") is None
    assert response.json().get("finding_codes") in (None, [])
    for secret in ["RAW_SECRET", "RAW_CONTROL_SECRET", "alice@example.com", "BLOCK"]:
        assert secret not in response.text + stream.getvalue()
    record = json.loads(stream.getvalue())
    assert record["event_type"] == "operational_failure"
    assert "action" not in record
    assert "finding_counts" not in record


def test_audit_failure_never_dispatches(tmp_path):
    app, target, _ = setup_app(tmp_path, sink=FailingSink())
    response = request(app, json=payload("RAW_SECRET alice@example.com"))
    assert response.status_code == 503
    assert target.calls == []
    assert response.json().get("action") is None
    for secret in ["RAW_SECRET", "RAW_AUDIT_SECRET", "alice@example.com", "BLOCK"]:
        assert secret not in response.text


def test_target_failure_is_502_after_decision_audit(tmp_path):
    app, target, stream = setup_app(tmp_path, target_fail=True)
    response = request(app, json=payload("RAW_SECRET alice@example.com"))
    assert response.status_code == 502
    assert len(target.calls) == 1
    record = json.loads(stream.getvalue())
    assert record["event_type"] == "decision"
    assert record["forwarding_eligible"] is True
    for secret in ["RAW_SECRET", "RAW_TARGET_SECRET", "alice@example.com", "success"]:
        assert secret not in response.text + stream.getvalue()


def test_disabled_control_skipped_and_audited(tmp_path):
    control = FakeControl(fail=True)
    app, target, stream = setup_app(tmp_path, enabled=False, control=control)
    response = request(app, json=payload("alice@example.com"))
    assert response.status_code == 200
    assert response.json()["action"] == "ALLOW"
    assert control.calls == 0
    assert target.calls[0].content == "alice@example.com"
    assert json.loads(stream.getvalue())["control_status"] == {"email-address": False}


def test_invalid_policy_prevents_startup(tmp_path):
    path = tmp_path / "invalid.yaml"
    path.write_text("version: 99\n")
    app = create_app(policy_path=path)

    async def run():
        async with app.router.lifespan_context(app):
            pytest.fail("Invalid policy must not permit application startup")

    with pytest.raises(PolicyError):
        asyncio.run(run())


def test_environment_selects_block_policy_at_startup(tmp_path, monkeypatch):
    path = tmp_path / "alternate-policy.yaml"
    path.write_text(
        "version: 1\npolicy_id: environment-selected\ncontrols:\n"
        "  email-address:\n    enabled: true\n    findings:\n"
        "      pii.email: BLOCK\n"
    )
    monkeypatch.setenv("CONTROL_LAYER_POLICY", str(path))
    stream = io.StringIO()
    target = SpyTarget(stream)
    app = create_app(
        audit_sink=JsonLinesAuditSink(stream),
        target_registry=TargetRegistry(
            (RegisteredTarget(TargetDefinition("local-echo"), target),)
        ),
    )
    response = request(app, json=payload("alice@example.com"))
    assert response.status_code == 403
    assert response.json()["action"] == "BLOCK"
    assert response.json()["finding_codes"] == ["pii.email"]
    assert target.calls == []
    record = json.loads(stream.getvalue())
    assert record["action"] == "BLOCK"
    assert record["forwarding_eligible"] is False


def test_missing_environment_policy_prevents_startup(tmp_path, monkeypatch):
    monkeypatch.setenv("CONTROL_LAYER_POLICY", str(tmp_path / "missing.yaml"))
    stream = io.StringIO()
    target = SpyTarget(stream)
    app = create_app(
        audit_sink=JsonLinesAuditSink(stream),
        target_registry=TargetRegistry(
            (RegisteredTarget(TargetDefinition("local-echo"), target),)
        ),
    )
    with pytest.raises(PolicyError):
        request(app, json=payload("alice@example.com"))
    assert target.calls == []
    assert stream.getvalue() == ""
