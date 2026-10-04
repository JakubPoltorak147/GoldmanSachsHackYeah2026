"""HTTP boundary: budget enforcement, observe mode, usage endpoint, privacy."""

import io
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

import yaml
from fastapi.testclient import TestClient

from app.control_layer.api import create_app
from app.control_layer.audit import JsonLinesAuditSink
from app.control_layer.composition import default_controls
from app.control_layer.registry import ControlRegistration, ControlRegistry
from app.control_layer.targets import (
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
    TargetResult,
)
from app.control_layer.usage_control import UsageBudgetControl, UsageMeter

OFFLINE = (
    Path(__file__).resolve().parents[2] / "config" / "policy-evaluation-offline.yaml"
)
CANARY = "CANARY_BUDGET_PAYLOAD_7f3a"
BEARER = "Authorization: Bearer abcdefghijklmnop1234567890"


class Clock:
    def __init__(self):
        self.now = 5000.0

    def __call__(self):
        return self.now


class Target:
    def __init__(self):
        self.calls = []
        self.lock = Lock()

    def invoke(self, interaction):
        with self.lock:
            self.calls.append(interaction)
        return TargetResult(interaction.content)


def make_app(tmp_path, *, limits=None, mapping=None, enabled=True, clock=None):
    def mutate(raw):
        entry = raw["controls"]["usage-budget"]
        entry["enabled"] = enabled
        entry["limits"].update(limits or {})
        if mapping:
            entry["findings"] = {code: mapping for code in entry["findings"]}

    raw = yaml.safe_load(OFFLINE.read_text())
    mutate(raw)
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(raw))
    clock = clock or Clock()
    registry = ControlRegistry(
        tuple(
            ControlRegistration(r.definition, UsageBudgetControl(UsageMeter(clock)))
            if r.definition.id == "usage-budget"
            else r
            for r in default_controls().registrations
        )
    )
    stream, target = io.StringIO(), Target()
    app = create_app(
        policy_path=path,
        control_registry=registry,
        audit_sink=JsonLinesAuditSink(stream),
        target_registry=TargetRegistry(
            (RegisteredTarget(TargetDefinition("local-echo"), target),)
        ),
    )
    return app, target, stream, clock


def post(client, content):
    return client.post(
        "/v1/interactions", json={"target_id": "local-echo", "content": content}
    )


def test_request_limit_blocks_after_exact_boundary_and_never_calls_target(tmp_path):
    app, target, stream, _ = make_app(tmp_path, limits={"max_requests": 3})
    with TestClient(app) as client:
        responses = [post(client, "hello") for _ in range(4)]
    assert [r.status_code for r in responses] == [200, 200, 200, 403]
    assert responses[3].json()["action"] == "BLOCK"
    assert responses[3].json()["finding_codes"] == ["budget.request_limit"]
    assert "result" not in responses[3].json()
    assert len(target.calls) == 3
    last = json.loads(stream.getvalue().splitlines()[-1])
    assert last["action"] == "BLOCK" and last["forwarding_eligible"] is False
    assert last["finding_counts"] == {"budget.request_limit": 1}
    assert "usage-budget" in last["evaluated_controls"]


def test_oversized_request_is_blocked_and_boundary_request_passes(tmp_path):
    app, target, _, _ = make_app(tmp_path, limits={"max_request_tokens": 100})
    with TestClient(app) as client:
        allowed = post(client, "x" * 400)
        blocked = post(client, "x" * 401)
    assert allowed.status_code == 200 and allowed.json()["action"] == "ALLOW"
    assert blocked.status_code == 403
    assert blocked.json()["finding_codes"] == ["budget.request_size"]
    assert len(target.calls) == 1


def test_token_window_exhaustion_and_reset(tmp_path):
    app, target, _, clock = make_app(
        tmp_path, limits={"max_estimated_tokens": 30, "max_request_tokens": 20}
    )
    with TestClient(app) as client:
        assert post(client, "x" * 80).status_code == 200  # 20 tokens
        exhausted = post(client, "x" * 80)  # 40 > 30
        assert exhausted.status_code == 403
        assert exhausted.json()["finding_codes"] == ["budget.token_limit"]
        clock.now += 60
        assert post(client, "x" * 80).status_code == 200
    assert len(target.calls) == 2


def test_observe_only_mapping_records_finding_but_forwards(tmp_path):
    app, target, stream, _ = make_app(
        tmp_path, limits={"max_requests": 1}, mapping="ALLOW"
    )
    with TestClient(app) as client:
        first, second = post(client, "hello"), post(client, "hello")
        usage = client.get("/v1/usage").json()
    assert (first.status_code, second.status_code) == (200, 200)
    assert second.json()["finding_codes"] == ["budget.request_limit"]
    assert second.json()["action"] == "ALLOW"
    assert len(target.calls) == 2
    assert usage["breaches"]["request_limit"] == 1
    assert json.loads(stream.getvalue().splitlines()[-1])["finding_counts"] == {
        "budget.request_limit": 1
    }


def test_budget_block_combines_with_other_controls_central_precedence(tmp_path):
    app, target, _, _ = make_app(tmp_path, limits={"max_requests": 1})
    with TestClient(app) as client:
        assert post(client, "alice@example.com").json()["action"] == "REDACT"
        both = post(client, "alice@example.com")
    assert both.status_code == 403
    assert both.json()["finding_codes"] == ["pii.email", "budget.request_limit"]
    assert len(target.calls) == 1


def test_requests_blocked_by_other_controls_are_still_charged(tmp_path):
    app, target, _, _ = make_app(tmp_path)
    with TestClient(app) as client:
        assert post(client, BEARER).status_code == 403
        usage = client.get("/v1/usage").json()
    assert usage["requests"]["used"] == 1 and usage["estimated_tokens"]["used"] == 12
    assert target.calls == []


def test_usage_snapshot_reads_do_not_charge(tmp_path):
    app, _, _, clock = make_app(tmp_path)
    with TestClient(app) as client:
        for text in ("a" * 4, "b" * 8, "c" * 9):
            post(client, text)
        clock.now += 20
        first = client.get("/v1/usage")
        second = client.get("/v1/usage")
    assert first.status_code == 200 and first.json() == second.json()
    assert first.headers["cache-control"] == "no-store"
    assert first.json() == {
        "enabled": True,
        "window_seconds": 60,
        "resets_in_seconds": 40,
        "requests": {"used": 3, "limit": 20},
        "estimated_tokens": {"used": 1 + 2 + 3, "limit": 2000},
        "max_request_tokens": 400,
        "breaches": {"request_limit": 0, "token_limit": 0, "request_size": 0},
    }


def test_usage_disabled_and_fixed_errors(tmp_path):
    app, _, _, _ = make_app(tmp_path, enabled=False)
    with TestClient(app) as client:
        disabled = client.get("/v1/usage")
        query = client.get("/v1/usage?x=1")
        method = client.post("/v1/usage", json={})
        slash = client.get("/v1/usage/", follow_redirects=False)
        unbudgeted = post(client, "x" * 16384)
    assert disabled.status_code == 200 and disabled.json() == {"enabled": False}
    assert disabled.headers["cache-control"] == "no-store"
    assert unbudgeted.status_code == 200
    assert (query.status_code, query.json()) == (422, {"error_code": "invalid_request"})
    assert (method.status_code, method.json()) == (
        405,
        {"error_code": "method_not_allowed"},
    )
    assert (slash.status_code, slash.json()) == (404, {"error_code": "not_found"})
    for response in (query, method, slash):
        assert response.headers["cache-control"] == "no-store"
    assert "x=1" not in query.text and "x=1" not in slash.text


def test_privacy_canary_absent_from_audit_reporting_usage_and_errors(tmp_path):
    app, _, stream, _ = make_app(tmp_path, limits={"max_request_tokens": 5})
    with TestClient(app) as client:
        blocked = post(client, CANARY * 3)
        surfaces = [
            blocked.text,
            client.get("/v1/usage").text,
            client.get("/v1/reporting/events").text,
            client.get("/v1/reporting/summary").text,
            stream.getvalue(),
        ]
        events = client.get("/v1/reporting/events").json()["items"]
    assert blocked.status_code == 403
    assert all(CANARY not in surface for surface in surfaces)
    codes = [f["code"] for f in events[0]["event"]["findings"]]
    assert codes == ["budget.request_size"]


def test_concurrent_burst_never_over_admits(tmp_path):
    app, target, _, _ = make_app(tmp_path, limits={"max_requests": 10})
    with TestClient(app) as client:
        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(
                pool.map(lambda _: post(client, "hi").status_code, range(40))
            )
        usage = client.get("/v1/usage").json()
    assert statuses.count(200) == 10 and statuses.count(403) == 30
    assert len(target.calls) == 10
    assert usage["breaches"]["request_limit"] == 30


def test_shipped_default_policy_admits_maximum_size_request_and_reports_usage(
    tmp_path,
):
    app = create_app(
        policy_path=OFFLINE.with_name("policy.yaml"),
        audit_sink=JsonLinesAuditSink(io.StringIO()),
        target_registry=TargetRegistry(
            (RegisteredTarget(TargetDefinition("local-echo"), Target()),)
        ),
    )
    with TestClient(app) as client:
        assert post(client, "x" * 16384).status_code == 200
        usage = client.get("/v1/usage").json()
    assert usage["estimated_tokens"] == {"used": 4096, "limit": 60000}
    assert usage["requests"] == {"used": 1, "limit": 120}
    assert usage["max_request_tokens"] == 4096


def test_registry_without_budget_control_reports_disabled_usage(tmp_path):
    raw = yaml.safe_load(OFFLINE.read_text())
    raw["controls"].pop("usage-budget")
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(raw))
    registry = ControlRegistry(
        tuple(
            r
            for r in default_controls().registrations
            if r.definition.id != "usage-budget"
        )
    )
    app = create_app(
        policy_path=path,
        control_registry=registry,
        audit_sink=JsonLinesAuditSink(io.StringIO()),
        target_registry=TargetRegistry(
            (RegisteredTarget(TargetDefinition("local-echo"), Target()),)
        ),
    )
    with TestClient(app) as client:
        assert client.get("/v1/usage").json() == {"enabled": False}
