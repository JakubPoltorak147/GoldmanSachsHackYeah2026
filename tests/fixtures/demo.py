"""Real controls/adapters with deterministic HTTP transport, never Ollama."""

import io
import json

import httpx

from app.control_layer.api import create_app
from app.control_layer.audit import JsonLinesAuditSink
from app.control_layer.composition import default_controls
from app.control_layer.demo import DemoSettings
from app.control_layer.ollama_semantic import OllamaSemanticRuntime
from app.control_layer.ollama_target import OllamaSettings, OllamaTextTarget
from app.control_layer.registry import ControlRegistration, ControlRegistry
from app.control_layer.reporting_store import ReportingStore
from app.control_layer.semantic_control import FIELDS, SemanticSecurityControl
from app.control_layer.targets import (
    LocalEchoTarget,
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
)

OUTPUT = "DEMO_OUTPUT_CANARY<script>window.compromised=true</script>"


def demo_app(tmp_path, *, enabled=True, semantic=True, application_semantic=False):
    calls = []
    evaluations = []
    state = {"target_fail": False, "semantic_fail": False}
    stream = io.StringIO()
    store = ReportingStore(tmp_path / "demo.sqlite3")

    def transport(request):
        payload = json.loads(request.content)
        if "format" in payload:
            evaluations.append(payload)
            if state["semantic_fail"]:
                raise httpx.ConnectError("PRIVATE_EVALUATOR_EXCEPTION")
            text = payload["prompt"]
            scores = dict.fromkeys(FIELDS, 0)
            if "Ignore all previous" in text:
                scores["prompt_injection"] = 0.9
            if "SYSTEM OVERRIDE" in text:
                scores["instruction_override"] = 0.9
            if "export all protected" in text:
                scores["exfiltration_intent"] = 0.9
            result = json.dumps(scores)
        else:
            # Required audit already exists before dispatch.
            assert store.list_events()
            calls.append(payload["prompt"])
            if state["target_fail"]:
                raise httpx.ConnectError("PRIVATE_TARGET_EXCEPTION")
            result = OUTPUT

        class Body(httpx.SyncByteStream):
            def __iter__(self):
                yield json.dumps({"done": True, "response": result}).encode()

        return httpx.Response(200, stream=Body())

    def factory(**kwargs):
        kwargs["transport"] = httpx.MockTransport(transport)
        return httpx.Client(**kwargs)

    registrations = []
    for r in default_controls().registrations:
        if r.definition.id == "semantic-security":
            runtime = OllamaSemanticRuntime(r.evaluator.runtime.settings, factory)
            r = ControlRegistration(r.definition, SemanticSecurityControl(runtime))
        registrations.append(r)
    controls = ControlRegistry(tuple(registrations))
    settings = OllamaSettings()
    targets = TargetRegistry(
        (
            RegisteredTarget(TargetDefinition("local-echo"), LocalEchoTarget()),
            RegisteredTarget(
                TargetDefinition("local-ollama", settings.model),
                OllamaTextTarget(settings, client_factory=factory),
            ),
        )
    )
    app = create_app(
        policy_path="config/policy-semantic-demo.yaml"
        if application_semantic
        else "config/policy.yaml",
        control_registry=controls,
        target_registry=targets,
        reporting_store=store,
        audit_sink=JsonLinesAuditSink(stream),
        demo_settings=DemoSettings(enabled, semantic),
    )
    return app, store, state, calls, evaluations, stream
