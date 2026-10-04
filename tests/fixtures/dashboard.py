"""Deterministic safe evidence for HTTP and browser dashboard verification."""

import io
from dataclasses import replace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.control_layer.api import create_app
from app.control_layer.audit import JsonLinesAuditSink
from app.control_layer.composition import default_controls
from app.control_layer.registry import ControlRegistration, ControlRegistry
from app.control_layer.reporting_store import ReportingStore
from app.control_layer.semantic_control import FIELDS, SemanticSecurityControl
from app.control_layer.targets import (
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
    TargetResult,
)

INPUT_CANARY = "PRIVATE_INPUT_CANARY"
OUTPUT_CANARY = "PRIVATE_OUTPUT_CANARY<script>window.compromised=true</script>"
EXCEPTION_CANARY = "PRIVATE_EXCEPTION_CANARY"
SEMANTIC_CANARY = "PRIVATE_SEMANTIC_RESPONSE_CANARY"


def dashboard_app(tmp_path):
    state = {"semantic_fail": False, "target_fail": False, "semantic_attack": False}
    calls = []
    stream = io.StringIO()
    store = ReportingStore(tmp_path / "dashboard.sqlite3")

    def semantic(_content):
        if state["semantic_fail"]:
            raise RuntimeError(SEMANTIC_CANARY)
        return dict.fromkeys(FIELDS, 0) | {
            "instruction_override": 0.9 if state["semantic_attack"] else 0
        }

    class Target:
        def invoke(self, interaction):
            assert store.get_event(interaction.id) is not None
            calls.append(interaction)
            if state["target_fail"]:
                raise RuntimeError(EXCEPTION_CANARY)
            return TargetResult(OUTPUT_CANARY)

    registrations = default_controls().registrations
    controls = ControlRegistry(
        tuple(
            ControlRegistration(r.definition, SemanticSecurityControl(semantic))
            if r.definition.id == "semantic-security"
            else r
            for r in registrations
        )
    )
    targets = TargetRegistry(
        (RegisteredTarget(TargetDefinition("local-ollama", "generation:v1"), Target()),)
    )
    app = create_app(
        policy_path="config/policy-semantic-demo.yaml",
        control_registry=controls,
        target_registry=targets,
        reporting_store=store,
        audit_sink=JsonLinesAuditSink(stream),
    )
    return app, store, state, calls, stream


def seed_dashboard(app, store, state):
    """Use actual interaction pipeline, then one incomplete eligible record."""
    ids = {}
    with TestClient(app) as client:

        def post(name, content):
            result = client.post(
                "/v1/interactions",
                json={
                    "target_id": "local-ollama",
                    "content": content,
                },
            )
            ids[name] = result.json()["interaction_id"]
            return result

        assert post("allowed", INPUT_CANARY).status_code == 200
        assert (
            post("redacted", "alex@example.invalid alex@example.invalid").status_code
            == 200
        )
        assert (
            post("blocked", "Authorization: Bearer SYNTHETIC_SECRET_CANARY").status_code
            == 403
        )
        state["semantic_attack"] = True
        assert post("semantic", "Synthetic instruction override").status_code == 403
        state["semantic_attack"] = False
        state["target_fail"] = True
        assert post("target_failed", INPUT_CANARY).status_code == 502
        state["target_fail"] = False
        state["semantic_fail"] = True
        assert post("evaluation_failed", INPUT_CANARY).status_code == 503
        state["semantic_fail"] = False
    original = store.list_events()[0].event
    incomplete = replace(original, interaction_id=uuid4())
    store._append_event(incomplete)
    ids["unknown"] = str(incomplete.interaction_id)
    return ids
