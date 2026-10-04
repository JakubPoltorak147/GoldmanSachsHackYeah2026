import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.control_layer.reporting import ReportingError
from tests.fixtures.dashboard import (
    EXCEPTION_CANARY,
    INPUT_CANARY,
    OUTPUT_CANARY,
    SEMANTIC_CANARY,
    dashboard_app,
    seed_dashboard,
)


@pytest.fixture
def evidence(tmp_path):
    app, store, state, calls, stream = dashboard_app(tmp_path)
    ids = seed_dashboard(app, store, state)
    with TestClient(app) as client:
        yield client, store, calls, stream, ids
    store.close()


def test_summary_events_detail_exact_safe_evidence(evidence, caplog):
    client, store, calls, stream, ids = evidence
    before = len(calls)
    response = client.get("/v1/reporting/summary")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    result = response.json()
    assert result["reporting_health"] == "healthy"
    summary = result["overall"]
    assert summary["interaction_total"] == 7
    assert summary["actions"] == {"ALLOW": 3, "REDACT": 1, "BLOCK": 2}
    assert summary["operational_failure_total"] == 1
    assert summary["invocations"] == {
        "succeeded": 2,
        "failed": 1,
        "unknown": 1,
        "not_invoked": 3,
    }
    assert summary["evaluation"]["samples"] == 7
    assert summary["semantic"]["samples"] == 7
    assert summary["invocation"]["samples"] == 3
    findings = {f["code"]: f for f in summary["findings"]}
    assert findings["pii.email"]["occurrences"] == 2
    assert findings["pii.email"]["affected_interactions"] == 1
    assert findings["semantic.instruction_override"]["occurrences"] == 1
    lower, upper = (
        datetime.fromisoformat(result["window"][key])
        for key in ("from_time", "to_time")
    )
    assert upper - lower == timedelta(days=1)
    events = client.get("/v1/reporting/events", params={"limit": 2}).json()
    assert [v["sequence"] for v in events["items"]] == [7, 6]
    older = client.get(
        "/v1/reporting/events",
        params={"limit": 2, "before_sequence": events["next_before_sequence"]},
    ).json()
    assert [v["sequence"] for v in older["items"]] == [5, 4]
    details = [
        client.get(f"/v1/reporting/events/{identifier}").json()
        for identifier in ids.values()
    ]
    detail = client.get(f"/v1/reporting/events/{ids['target_failed']}").json()["item"]
    assert detail["event"]["action"] == "ALLOW"
    assert detail["completion"]["error_code"] == "target_failed"
    assert detail["event"]["model_id"] == "generation:v1"
    assert detail["event"]["semantic_model_id"] == "qwen2.5:3b"
    failed = client.get(f"/v1/reporting/events/{ids['evaluation_failed']}").json()[
        "item"
    ]
    assert failed["event"]["action"] is None
    assert failed["event"]["findings"] == []
    assert failed["event"]["semantic_status"] == "failed"
    assert failed["invocation_status"] == "not_invoked"
    assert len(calls) == before
    assert len(store.list_events()) == 7
    all_replies = (
        json.dumps([result, events, older, details]) + stream.getvalue() + caplog.text
    )
    for canary in (
        INPUT_CANARY,
        OUTPUT_CANARY,
        EXCEPTION_CANARY,
        SEMANTIC_CANARY,
        "alex@example.invalid",
        "SYNTHETIC_SECRET_CANARY",
        "[REDACTED]",
    ):
        assert canary not in all_replies

    # Closed DTOs must not gain payload-shaped fields on any branch.
    def walk(value):
        if isinstance(value, dict):
            assert (
                not {
                    "content",
                    "prompt",
                    "output",
                    "metadata",
                    "span",
                    "scores",
                    "response",
                }
                & value.keys()
            )
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk([result, events, details])


@pytest.mark.parametrize("endpoint", ["summary", "events"])
@pytest.mark.parametrize(
    "params",
    [
        {"from_time": "2026-10-04T00:00:00Z"},
        {"from_time": "2026-10-05T00:00:00Z", "to_time": "2026-10-04T00:00:00Z"},
        {"from_time": "2026-09-01T00:00:00Z", "to_time": "2026-10-04T00:00:00Z"},
        {
            "from_time": "2026-10-04T00:00:00+01:00",
            "to_time": "2026-10-05T00:00:00+01:00",
        },
        {"from_time": "2026-10-04", "to_time": "2026-10-05"},
        {"from_time": "2026-02-30T00:00:00Z", "to_time": "2026-03-01T00:00:00Z"},
        {"action": "CANARY_SECRET"},
        {"target_id": "x' OR 1=1--"},
        {"target_id": "x" * 65},
        {"invocation_status": "success"},
        {"unknown": "CANARY_SECRET"},
        [("action", "ALLOW"), ("action", "BLOCK")],
    ],
)
def test_invalid_filters_are_fixed_without_reflection(evidence, endpoint, params):
    client, store, calls, _, _ = evidence
    before = len(calls)
    response = client.get(f"/v1/reporting/{endpoint}", params=params)
    assert response.status_code == 422
    assert response.json() == {"error_code": "invalid_reporting_query"}
    assert response.headers["cache-control"] == "no-store"
    assert len(calls) == before and len(store.list_events()) == 7


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("path", ["summary", "events", "events/not-a-uuid"])
def test_reporting_slash_paths_never_redirect_or_reflect(evidence, method, path):
    client, store, calls, _, _ = evidence
    before = len(calls)
    response = client.request(
        method,
        f"/v1/reporting/{path}/?unknown=CANARY_SECRET",
        follow_redirects=False,
    )
    assert response.status_code == 404
    assert response.json() == {"error_code": "not_found"}
    assert response.headers["cache-control"] == "no-store"
    assert "location" not in response.headers
    assert "CANARY_SECRET" not in str(response.headers) + response.text
    assert len(calls) == before and len(store.list_events()) == 7
    # The guard is confined to reporting; interaction routing stays compatible.
    assert client.post("/v1/interactions/", follow_redirects=False).status_code == 307


@pytest.mark.parametrize(
    "key,value",
    [
        ("limit", "0"),
        ("limit", "101"),
        ("limit", "01"),
        ("limit", "true"),
        ("before_sequence", "0"),
        ("before_sequence", "-1"),
        ("before_sequence", str(2**63)),
        ("before_sequence", "9" * 1000),
        ("before_sequence", "1.0"),
    ],
)
def test_http_pagination_bounds(evidence, key, value):
    response = evidence[0].get("/v1/reporting/events", params={key: value})
    assert response.status_code == 422
    assert response.json() == {"error_code": "invalid_reporting_query"}


def test_filtering_half_open_ranges_and_empty(evidence):
    client, store, _, _, _ = evidence
    for key, value, count in [
        ("action", "BLOCK", 2),
        ("target_id", "local-ollama", 7),
        ("invocation_status", "unknown", 1),
    ]:
        assert (
            client.get("/v1/reporting/summary", params={key: value}).json()["overall"][
                "interaction_total"
            ]
            == count
        )
        assert (
            len(client.get("/v1/reporting/events", params={key: value}).json()["items"])
            == count
        )
    params = {"target_id": "historical-target"}
    empty = client.get("/v1/reporting/summary", params=params).json()["overall"]
    assert empty["interaction_total"] == 0
    assert (
        empty["evaluation"]["samples"] == 0 and empty["evaluation"]["mean_ms"] is None
    )
    event = store.list_events()[0].event
    params = {
        "from_time": (event.timestamp - timedelta(seconds=1)).isoformat(),
        "to_time": event.timestamp.isoformat(),
    }
    assert (
        client.get("/v1/reporting/summary", params=params).json()["overall"][
            "interaction_total"
        ]
        == 0
    )
    now = datetime.now(UTC)
    params = {
        "from_time": (now - timedelta(days=31)).isoformat(),
        "to_time": now.isoformat(),
    }
    assert client.get("/v1/reporting/summary", params=params).status_code == 200
    assert client.get("/v1/reporting/summary", params={"limit": 1}).status_code == 422


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_reporting_methods_read_only(evidence, method):
    client, store, calls, _, ids = evidence
    before = len(calls)
    for path in ("summary", "events", f"events/{ids['allowed']}"):
        response = getattr(client, method)(f"/v1/reporting/{path}")
        assert response.status_code == 405
        assert response.json() == {"error_code": "method_not_allowed"}
    assert len(calls) == before and len(store.list_events()) == 7


def test_detail_validation_and_missing(evidence):
    client, _, _, _, ids = evidence
    assert client.get(f"/v1/reporting/events/{uuid4()}").json() == {
        "error_code": "not_found"
    }
    assert client.get(f"/v1/reporting/events/{uuid4()}").status_code == 404
    for invalid in ("SECRET_CANARY", "0" * 32):
        result = client.get(f"/v1/reporting/events/{invalid}")
        assert result.status_code == 422
        assert result.json() == {"error_code": "invalid_reporting_query"}
    assert (
        client.get(
            f"/v1/reporting/events/{ids['allowed']}", params={"unknown": "secret"}
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "method,path",
    [
        ("summarize", "summary"),
        ("list_recent_events", "events"),
        ("get_event", "detail"),
    ],
)
@pytest.mark.parametrize(
    "exception", [ReportingError(), RuntimeError(EXCEPTION_CANARY)]
)
def test_read_errors_never_return_zeros(evidence, monkeypatch, method, path, exception):
    client, store, calls, _, ids = evidence

    def fail(*_args, **_kwargs):
        raise exception

    monkeypatch.setattr(store, method, fail)
    before = len(calls)
    url = f"events/{ids['allowed']}" if path == "detail" else path
    result = client.get(f"/v1/reporting/{url}")
    assert result.status_code == 503
    assert result.json() == {"error_code": "reporting_unavailable"}
    assert store.health == "healthy" and len(calls) == before


def test_write_gate_health_is_separate(evidence):
    client, store, calls, _, ids = evidence
    store.poison()
    response = client.get("/v1/reporting/summary")
    assert response.status_code == 200
    assert response.json()["reporting_health"] == "reporting_write_failed"
    assert response.json()["overall"]["interaction_total"] == 7
    assert (
        client.get(f"/v1/reporting/events/{ids['unknown']}").json()["item"][
            "invocation_status"
        ]
        == "unknown"
    )
    before = len(calls)
    failed = client.post(
        "/v1/interactions", json={"target_id": "local-ollama", "content": "benign"}
    )
    assert failed.status_code == 503 and failed.json()["error_code"] == "audit_failed"
    assert len(calls) == before


def test_completion_write_failure_preserves_result_and_unknown(evidence, monkeypatch):
    client, store, calls, _, _ = evidence

    def fail(_completion):
        raise ReportingError()

    monkeypatch.setattr(store, "_append_completion", fail)
    response = client.post(
        "/v1/interactions", json={"target_id": "local-ollama", "content": "benign"}
    )
    assert response.status_code == 200
    assert response.json()["result"]["content"] == OUTPUT_CANARY
    item = client.get(
        f"/v1/reporting/events/{response.json()['interaction_id']}"
    ).json()["item"]
    assert item["invocation_status"] == "unknown"
    assert item["completion"] is None
    assert OUTPUT_CANARY not in json.dumps(item)
    assert (
        client.get("/v1/reporting/summary").json()["reporting_health"]
        == "reporting_write_failed"
    )
    assert store.get_event(UUID(response.json()["interaction_id"])) is not None


def test_local_dashboard_assets_and_no_execution_surface(evidence):
    client, store, calls, _, _ = evidence
    before = len(calls)
    page = client.get("/dashboard")
    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    for asset in ("dashboard.css", "dashboard.js", "api.js", "detail.js"):
        assert client.get(f"/dashboard/assets/{asset}").status_code == 200
    assert "/v1/interactions" not in client.get("/dashboard/assets/dashboard.js").text
    assert "/v1/reporting/" in client.get("/dashboard/assets/api.js").text
    assert "sqlite" not in page.text.lower()
    assert "Attack Lab" not in page.text
    assert "WebSocket" not in client.get("/dashboard/assets/dashboard.js").text
    assert len(calls) == before and len(store.list_events()) == 7
