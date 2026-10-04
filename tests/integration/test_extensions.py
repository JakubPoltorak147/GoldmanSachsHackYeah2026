import io
import json
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.control_layer.api import DecisionResponse, create_app
from app.control_layer.audit import JsonLinesAuditSink
from app.control_layer.domain import Finding, PolicyError
from app.control_layer.registry import (
    ControlDefinition,
    ControlRegistration,
    ControlRegistry,
    FindingDefinition,
)
from app.control_layer.targets import (
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
    TargetResult,
)


class Evaluator:
    def __init__(self, output=()):
        self.output = output
        self.calls = 0

    def evaluate(self, interaction):
        self.calls += 1
        return self.output


class Target:
    def __init__(self):
        self.calls = []

    def invoke(self, interaction):
        self.calls.append(interaction)
        return TargetResult(interaction.content)


def setup(tmp_path, outputs=((), ())):
    controls = [Evaluator(output) for output in outputs]
    registry = ControlRegistry(
        [
            ControlRegistration(
                ControlDefinition(
                    identifier, [FindingDefinition(f"{identifier}.code", False, False)]
                ),
                evaluator,
            )
            for identifier, evaluator in zip(("first", "second"), controls, strict=True)
        ]
    )
    path = tmp_path / "policy.yaml"
    raw = {
        "version": 1,
        "policy_id": "injected",
        "controls": {
            identifier: {"enabled": True, "findings": {f"{identifier}.code": "ALLOW"}}
            for identifier in ("first", "second")
        },
    }
    path.write_text(yaml.safe_dump(raw))
    targets = [Target(), Target()]
    target_registry = TargetRegistry(
        [
            RegisteredTarget(TargetDefinition(identifier), adapter)
            for identifier, adapter in zip(
                ("local-echo", "internal"), targets, strict=True
            )
        ]
    )
    stream = io.StringIO()
    app = create_app(
        policy_path=path,
        control_registry=registry,
        target_registry=target_registry,
        audit_sink=JsonLinesAuditSink(stream),
    )
    return app, path, raw, controls, targets, stream


def test_multiple_controls_startup_same_bindings_reused(tmp_path):
    app, _, _, controls, targets, stream = setup(tmp_path)
    with TestClient(app) as client:
        entries = app.state.service.policy.entries
        for _ in range(2):
            response = client.post(
                "/v1/interactions",
                json={"target_id": "local-echo", "content": " exact "},
            )
            assert response.status_code == 200
            assert response.json()["result"] == {"content": " exact "}
            assert app.state.service.policy.entries is entries
    assert [c.calls for c in controls] == [2, 2]
    assert [len(t.calls) for t in targets] == [2, 0]
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert all(r["evaluated_controls"] == ["first", "second"] for r in records)


def test_incomplete_injected_policy_fails_startup(tmp_path):
    app, path, raw, controls, targets, stream = setup(tmp_path)
    del raw["controls"]["second"]
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(PolicyError):
        with TestClient(app):
            pytest.fail("startup accepted incomplete policy")
    assert all(c.calls == 0 for c in controls)
    assert all(t.calls == [] for t in targets)
    assert stream.getvalue() == ""


@pytest.mark.parametrize(
    "argument,value,error",
    [("control_registry", (), PolicyError), ("target_registry", (), ValueError)],
)
def test_invalid_injected_registry_has_no_default_fallback(argument, value, error):
    with pytest.raises(error):
        with TestClient(create_app(**{argument: value})):
            pytest.fail("startup accepted invalid registry")


def test_generic_codes_order_and_multiplicity(tmp_path):
    app, _, _, _, targets, stream = setup(
        tmp_path,
        (
            (Finding("first", "first.code"), Finding("first", "first.code")),
            (Finding("second", "second.code"),),
        ),
    )
    with TestClient(app) as client:
        response = client.post(
            "/v1/interactions", json={"target_id": "local-echo", "content": "text"}
        )
    assert response.status_code == 200
    assert response.json()["finding_codes"] == [
        "first.code",
        "first.code",
        "second.code",
    ]
    assert response.json()["result"] == {"content": "text"}
    assert len(targets[0].calls) == 1
    assert json.loads(stream.getvalue())["finding_counts"] == {
        "first.code": 2,
        "second.code": 1,
    }


def test_internal_registered_target_stays_private(tmp_path):
    app, _, _, controls, targets, stream = setup(tmp_path)
    with TestClient(app) as client:
        response = client.post(
            "/v1/interactions", json={"target_id": "internal", "content": "RAW_SECRET"}
        )
    assert response.status_code == 422
    assert response.json() == {"error_code": "invalid_request"}
    assert all(c.calls == 0 for c in controls)
    assert all(t.calls == [] for t in targets)
    assert stream.getvalue() == ""


@pytest.mark.parametrize(
    "output", [(Finding("second", "second.code"),), (Finding("first", "RAW_SECRET"),)]
)
def test_actual_producer_forgery_fails_before_response(tmp_path, output):
    app, _, _, controls, targets, stream = setup(tmp_path, (output, ()))
    with TestClient(app) as client:
        response = client.post(
            "/v1/interactions", json={"target_id": "local-echo", "content": "text"}
        )
    assert response.status_code == 503
    assert response.json()["error_code"] == "evaluation_failed"
    assert "finding_codes" not in response.json()
    assert all(t.calls == [] for t in targets)
    assert controls[1].calls == 0
    record = json.loads(stream.getvalue())
    assert "finding_counts" not in record
    assert "RAW_SECRET" not in stream.getvalue() + response.text


FOUNDATION_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "foundation"


def test_openapi_only_approved_finding_code_and_target_differences():
    baseline = json.loads((FOUNDATION_FIXTURES / "baseline-openapi.json").read_text())
    actual = create_app().openapi()
    baseline_item = baseline["components"]["schemas"]["DecisionResponse"]["properties"][
        "finding_codes"
    ]["items"]
    actual_item = actual["components"]["schemas"]["DecisionResponse"]["properties"][
        "finding_codes"
    ]["items"]
    assert actual_item == {"type": "string"}
    assert baseline_item == {"type": "string", "const": "pii.email"}
    baseline["components"]["schemas"]["DecisionResponse"]["properties"][
        "finding_codes"
    ]["items"] = actual_item
    target = actual["components"]["schemas"]["InteractionRequest"]["properties"][
        "target_id"
    ]
    old_target = baseline["components"]["schemas"]["InteractionRequest"]["properties"][
        "target_id"
    ]
    assert old_target == {"type": "string", "const": "local-echo", "title": "Target Id"}
    assert target == {
        "type": "string",
        "enum": ["local-echo", "local-ollama"],
        "title": "Target Id",
    }
    baseline["components"]["schemas"]["InteractionRequest"]["properties"][
        "target_id"
    ] = target
    # Reporting and opt-in demo GETs are isolated additions. The approved
    # scenario alternative retains the ordinary request and response schemas.
    added_paths = set(actual["paths"]) - set(baseline["paths"])
    assert added_paths == {
        "/v1/reporting/summary",
        "/v1/reporting/events",
        "/v1/reporting/events/{interaction_id}",
        "/v1/demo/scenarios",
        "/v1/demo/workspace",
    }
    for path in added_paths:
        assert set(actual["paths"].pop(path)) == {"get"}
    added_schemas = set(actual["components"]["schemas"]) - set(
        baseline["components"]["schemas"]
    )
    assert added_schemas == {
        "CompletionDTO",
        "DetailResponse",
        "EventDTO",
        "EventViewDTO",
        "EventsResponse",
        "FindingDTO",
        "FindingSummaryDTO",
        "InvocationStatus",
        "ReportingErrorDTO",
        "SummaryDTO",
        "SummaryResponse",
        "TimingDTO",
        "WindowDTO",
        "ScenarioRequest",
    }
    request_schema = actual["paths"]["/v1/interactions"]["post"]["requestBody"][
        "content"
    ]["application/json"]["schema"]
    assert request_schema == {
        "anyOf": [
            {"$ref": "#/components/schemas/InteractionRequest"},
            {"$ref": "#/components/schemas/ScenarioRequest"},
        ],
        "title": "Body",
    }
    scenario_schema = actual["components"]["schemas"]["ScenarioRequest"]
    assert scenario_schema["additionalProperties"] is False
    assert scenario_schema["required"] == ["scenario_id"]
    assert set(scenario_schema["properties"]) == {"scenario_id"}
    actual["paths"]["/v1/interactions"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"] = {"$ref": "#/components/schemas/InteractionRequest"}
    for name in added_schemas:
        actual["components"]["schemas"].pop(name)
    assert actual == baseline


def test_response_codes_are_strict_strings():
    from uuid import uuid4

    from pydantic import ValidationError

    from app.control_layer.domain import Action

    with pytest.raises(ValidationError):
        DecisionResponse(
            interaction_id=uuid4(),
            action=Action.ALLOW,
            reason_code="no_findings",
            finding_codes=[1],
        )


BASELINE = json.loads((FOUNDATION_FIXTURES / "baseline-http.json").read_text())["cases"]


@pytest.mark.parametrize("case", BASELINE, ids=lambda case: case["name"])
def test_recorded_foundation_http_compatibility(tmp_path, case):
    from uuid import UUID

    from app.control_layer.composition import default_controls

    name = case["name"]
    stream = io.StringIO()
    target = Target()
    controls = ControlRegistry((default_controls().registrations[0],))
    if name == "evaluation_failed":

        class FailedControl:
            def evaluate(self, interaction):
                raise RuntimeError("RAW_SECRET")

        controls = ControlRegistry(
            [ControlRegistration(controls.registrations[0].definition, FailedControl())]
        )
    sink = JsonLinesAuditSink(stream)
    if name == "audit_failed":

        class FailedSink:
            def emit(self, event):
                raise RuntimeError("RAW_SECRET")

        sink = FailedSink()
    if name == "target_failed":

        def fail(interaction):
            target.calls.append(interaction)
            raise RuntimeError("RAW_SECRET")

        target.invoke = fail
    path = tmp_path / "baseline.yaml"
    mapping = case["policy_mapping"].split()[0]
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "policy_id": "baseline",
                "controls": {
                    "email-address": {
                        "enabled": True,
                        "findings": {"pii.email": mapping},
                    }
                },
            }
        )
    )
    app = create_app(
        policy_path=path,
        control_registry=controls,
        target_registry=TargetRegistry(
            [RegisteredTarget(TargetDefinition("local-echo"), target)]
        ),
        audit_sink=sink,
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        if name == "service_unavailable":

            def unexpected(interaction):
                raise RuntimeError("RAW_SECRET")

            app.state.service.evaluate = unexpected
        request = dict(case["request"])
        method, route = request.pop("method"), request.pop("path")
        response = client.request(method, route, **request)
    body = response.json()
    if "interaction_id" in body:
        UUID(body["interaction_id"])
        body["interaction_id"] = "<server-generated-uuid>"
    assert response.status_code == case["status"]
    assert body == case["response"]
    assert len(target.calls) == case["target_calls"]
    assert [i.content for i in target.calls] == case["forwarded_content"]
    assert len(stream.getvalue().splitlines()) == case["audit_record_count"]
