"""Local HTTP composition with actual production detectors, audited spy/echo."""

import base64
import io
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

import pytest
import yaml
from fastapi.testclient import TestClient

from app.control_layer import composition
from app.control_layer.api import create_app
from app.control_layer.attack_signatures import load_attack_catalog
from app.control_layer.audit import JsonLinesAuditSink
from app.control_layer.domain import Finding, PolicyError, Span
from app.control_layer.registry import ControlRegistration, ControlRegistry
from app.control_layer.targets import (
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
    TargetResult,
)

POLICY_PATH = Path(__file__).resolve().parents[2] / "config" / "policy.yaml"
PAT = "ghp_" + "A" * 36
OAUTH = "gho_" + "B" * 36
PEM = (
    "-----BEGIN PRIVATE KEY-----\n"
    + base64.b64encode(b"synthetic-pem-envelope-fixture-32!").decode()
    + "\n-----END PRIVATE KEY-----"
)
ATTACKS = (
    "cos\nsystem\n\ncposix\nsystem\n\n__import__('os').system(\nexec(base64.b64decode("
)
CONTENT = (
    f"😀 <alice@example.com>\nAuthorization: Bearer {PAT}\n{PEM}\n"
    f"{OAUTH}\nSSN: 123-45-6789\n{ATTACKS}"
)
CODES = [
    "pii.email",
    "secret.bearer",
    "secret.pem_private_key",
    "secret.github_pat",
    "secret.github_oauth",
    "pii.us_ssn",
    "attack.pickle_os_system",
    "attack.pickle_posix_system",
    "attack.python_os_system",
    "attack.python_exec_base64",
]
IDS = [
    "email-address",
    "bearer-credential",
    "pem-private-key",
    "github-token",
    "us-ssn",
    "known-attack-signatures",
]


class Target:
    def __init__(self, stream):
        self.stream = stream
        self.calls = []
        self.lock = Lock()

    def invoke(self, interaction):
        with self.lock:
            records = [json.loads(line) for line in self.stream.getvalue().splitlines()]
            assert any(
                r["interaction_id"] == str(interaction.id) and r["forwarding_eligible"]
                for r in records
            )
            self.calls.append(interaction)
        return TargetResult(interaction.content)


def app_setup(tmp_path, action=None, mutate=None, registry=None, sink=None):
    path = POLICY_PATH
    if action or mutate:
        raw = yaml.safe_load(path.read_text())
        if action:
            for config in raw["controls"].values():
                for code in config["findings"]:
                    config["findings"][code] = (
                        "ALLOW"
                        if action == "REDACT" and code.startswith("attack.")
                        else action
                    )
        if mutate:
            mutate(raw)
        path = tmp_path / "policy.yaml"
        path.write_text(yaml.safe_dump(raw))
    stream = io.StringIO()
    target = Target(stream)
    app = create_app(
        policy_path=path,
        control_registry=registry,
        audit_sink=sink or JsonLinesAuditSink(stream),
        target_registry=TargetRegistry(
            (RegisteredTarget(TargetDefinition("local-echo"), target),)
        ),
    )
    return app, target, stream


def post(client, content):
    return client.post(
        "/v1/interactions", json={"target_id": "local-echo", "content": content}
    )


@pytest.mark.parametrize(
    "action,status", [(None, 403), ("ALLOW", 200), ("REDACT", 200)]
)
def test_complete_default_registered_pack_end_to_end(tmp_path, action, status):
    app, target, stream = app_setup(tmp_path, action)
    with TestClient(app) as client:
        entries = app.state.service.policy.entries
        response = post(client, CONTENT)
        assert app.state.service.policy.entries is entries
    assert response.status_code == status
    body = response.json()
    assert body["action"] == (action or "BLOCK")
    assert body["finding_codes"] == CODES
    record = json.loads(stream.getvalue())
    assert record["evaluated_controls"] == IDS
    assert record["control_status"] == dict.fromkeys(IDS, True) | {
        "semantic-security": False
    }
    assert record["finding_counts"] == dict.fromkeys(CODES, 1)
    for value in [
        "alice@example.com",
        "123-45-6789",
        PAT,
        OAUTH,
        PEM,
        *[s.literal for s in load_attack_catalog().signatures],
    ]:
        assert value not in stream.getvalue()
    if action is None:
        assert target.calls == [] and "result" not in body
        assert PAT not in response.text and "123-45-6789" not in response.text
    else:
        expected = (
            CONTENT
            if action == "ALLOW"
            else (
                "😀 <[REDACTED]>\nAuthorization: Bearer [REDACTED]\n"
                f"[REDACTED]\n[REDACTED]\nSSN: [REDACTED]\n{ATTACKS}"
            )
        )
        assert body["result"] == {"content": expected}
        assert len(target.calls) == 1
        assert str(target.calls[0].id) == body["interaction_id"]


def test_default_email_echo_multiplicity_and_public_target_compatibility(tmp_path):
    app, target, stream = app_setup(tmp_path)
    with TestClient(app) as client:
        assert post(client, "  😀 e\u0301\n").json()["result"] == {
            "content": "  😀 e\u0301\n"
        }
        email = post(client, "<alice@example.com> <bob@example.com>")
        assert email.json()["finding_codes"] == ["pii.email", "pii.email"]
        assert email.json()["result"] == {"content": "<[REDACTED]> <[REDACTED]>"}
        before = stream.getvalue()
        response = client.post(
            "/v1/interactions", json={"target_id": "ollama", "content": PAT}
        )
        assert response.status_code == 422 and response.json() == {
            "error_code": "invalid_request"
        }
        assert stream.getvalue() == before
    assert len(target.calls) == 2


def test_explicit_disabled_migration_skips_new_controls(tmp_path):
    def mutate(raw):
        for id in IDS[1:]:
            raw["controls"][id] = {"enabled": False}

    app, target, stream = app_setup(tmp_path, mutate=mutate)
    with TestClient(app) as client:
        response = post(client, CONTENT)
    assert response.status_code == 200 and response.json()["action"] == "REDACT"
    assert response.json()["finding_codes"] == ["pii.email"]
    assert PAT in target.calls[0].content
    record = json.loads(stream.getvalue())
    assert record["evaluated_controls"] == ["email-address"]
    assert record["control_status"] == {id: id == "email-address" for id in IDS} | {
        "semantic-security": False
    }


@pytest.mark.parametrize(
    "case", ["unknown", "foreign", "producer", "span", "exception"]
)
def test_expanded_http_evaluation_failures_sanitized_no_dispatch(tmp_path, case):
    class Invalid:
        def evaluate(self, interaction):
            if case == "exception":
                raise RuntimeError("RAW_EXCEPTION_SECRET " + interaction.content)
            return {
                "unknown": (Finding("github-token", "RAW_UNKNOWN_SECRET", Span(0, 1)),),
                "foreign": (Finding("github-token", "pii.email", Span(0, 1)),),
                "producer": (Finding("email-address", "pii.email", Span(0, 1)),),
                "span": (Finding("github-token", "secret.github_pat", Span(False, 1)),),
            }[case]

    registry = ControlRegistry(
        tuple(
            ControlRegistration(r.definition, Invalid())
            if r.definition.id == "github-token"
            else r
            for r in composition.default_controls().registrations
        )
    )
    app, target, stream = app_setup(tmp_path, registry=registry)
    with TestClient(app) as client:
        response = post(client, CONTENT)
    assert response.status_code == 503
    assert response.json()["error_code"] == "evaluation_failed"
    assert "action" not in response.json() and "finding_codes" not in response.json()
    assert target.calls == []
    record = json.loads(stream.getvalue())
    assert record["event_type"] == "operational_failure" and "action" not in record
    for value in [
        PAT,
        OAUTH,
        "alice@example.com",
        "123-45-6789",
        "RAW_UNKNOWN_SECRET",
        "RAW_EXCEPTION_SECRET",
    ]:
        assert value not in stream.getvalue() + response.text


@pytest.mark.parametrize("action", ["ALLOW", "REDACT"])
def test_http_audit_failure_during_multi_control_eligible_decision(tmp_path, action):
    class FailedSink:
        def emit(self, event):
            raise OSError("RAW_AUDIT_SECRET " + PAT)

    app, target, stream = app_setup(tmp_path, action, sink=FailedSink())
    with TestClient(app) as client:
        response = post(client, CONTENT)
    assert (
        response.status_code == 503 and response.json()["error_code"] == "audit_failed"
    )
    assert (
        "action" not in response.json()
        and target.calls == []
        and stream.getvalue() == ""
    )
    assert PAT not in response.text and "RAW_AUDIT_SECRET" not in response.text


def test_concurrent_default_pack_state_isolation_and_audit_gate(tmp_path):
    app, target, stream = app_setup(tmp_path)
    with TestClient(app) as client:
        texts = [
            f"<user{i}@example.com> SSN: 123-45-6789"
            + ("\nexec(base64.b64decode(" if i % 2 == 0 else "")
            for i in range(24)
        ]
        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(lambda text: post(client, text), texts))
    records = {
        r["interaction_id"]: r for r in map(json.loads, stream.getvalue().splitlines())
    }
    assert len(records) == 24 and len(target.calls) == 12
    for i, response in enumerate(responses):
        body = response.json()
        record = records[body["interaction_id"]]
        assert record["finding_counts"] == {
            "pii.email": 1,
            "pii.us_ssn": 1,
            **({"attack.python_exec_base64": 1} if i % 2 == 0 else {}),
        }
        assert response.status_code == (403 if i % 2 == 0 else 200)
        if i % 2:
            assert body["result"]["content"] == "<[REDACTED]> SSN: [REDACTED]"
    assert (
        "@example.com" not in stream.getvalue()
        and "123-45-6789" not in stream.getvalue()
    )


def test_malformed_catalog_startup_even_disabled_and_snapshot(tmp_path, monkeypatch):
    cat = tmp_path / "catalog.json"
    original = {
        "version": 1,
        "catalog_id": "test",
        "signatures": [
            {
                "id": "test",
                "code": "attack.python_exec_base64",
                "literal": "exec(base64.b64decode(",
            }
        ],
    }
    cat.write_text(json.dumps(original))
    monkeypatch.setattr(
        composition, "load_attack_catalog", lambda: load_attack_catalog(cat)
    )

    def mutate(raw):
        raw["controls"]["known-attack-signatures"]["findings"] = {
            "attack.python_exec_base64": "BLOCK"
        }

    app, target, stream = app_setup(tmp_path, mutate=mutate)
    with TestClient(app) as client:
        cat.write_text("RAW_CATALOG_SECRET malformed")
        response = post(client, "exec(base64.b64decode(")
        assert response.status_code == 403 and response.json()["finding_codes"] == [
            "attack.python_exec_base64"
        ]
    assert target.calls == [] and "RAW_CATALOG_SECRET" not in stream.getvalue()
    app, _, _ = app_setup(
        tmp_path,
        mutate=lambda raw: raw["controls"]["known-attack-signatures"].update(
            enabled=False
        ),
    )
    with pytest.raises(PolicyError, match="^invalid_policy$"):
        with TestClient(app):
            pytest.fail("Malformed catalog allowed startup")


def test_actual_default_echo_adapter_and_input_boundaries():
    stream = io.StringIO()
    app = create_app(audit_sink=JsonLinesAuditSink(stream))
    with TestClient(app) as client:
        plain = "😀" * 16384
        response = post(client, plain)
        assert (
            response.status_code == 200
            and response.json()["result"]["content"] == plain
        )
        response = post(client, "<alice@example.com> SSN: 123-45-6789")
        assert response.json()["result"]["content"] == "<[REDACTED]> SSN: [REDACTED]"
        before = stream.getvalue()
        for invalid in ["a" * 16385, ""]:
            response = post(client, invalid)
            assert response.status_code == 422 and response.json() == {
                "error_code": "invalid_request"
            }
        assert stream.getvalue() == before


def test_default_pack_rejects_json_escaped_surrogate():
    stream = io.StringIO()
    with TestClient(create_app(audit_sink=JsonLinesAuditSink(stream))) as client:
        response = client.post(
            "/v1/interactions",
            content=b'{"target_id":"local-echo","content":"\\ud800"}',
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 422
    assert response.json() == {"error_code": "invalid_request"}
    assert stream.getvalue() == ""


def test_invalid_long_label_cannot_bypass_default_redaction():
    stream = io.StringIO()
    with TestClient(create_app(audit_sink=JsonLinesAuditSink(stream))) as client:
        response = post(client, "XUS SSN: 123-45-6789")
    assert response.status_code == 200
    assert response.json()["action"] == "REDACT"
    assert response.json()["finding_codes"] == ["pii.us_ssn"]
    assert response.json()["result"]["content"] == "XUS SSN: [REDACTED]"
    assert "123-45-6789" not in stream.getvalue()
