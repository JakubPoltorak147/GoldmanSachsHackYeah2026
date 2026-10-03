"""Optional separately provisioned Ollama smoke; never installs or pulls models."""

import sys
from pathlib import Path
from time import perf_counter

# Direct invocation from the repository root in non-package Poetry mode.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.control_layer.api import create_app  # noqa: E402
from app.control_layer.composition import default_targets  # noqa: E402
from app.control_layer.targets import (  # noqa: E402
    RegisteredTarget,
    TargetRegistry,
)


class RecordingSink:
    def __init__(self):
        self.records = []

    def emit(self, event):
        self.records.append(event.safe_record())


class ObservedTarget:
    def __init__(self, binding, sink):
        self.binding, self.sink = binding, sink
        self.calls = 0

    def invoke(self, interaction):
        records = [
            r for r in self.sink.records if r["interaction_id"] == str(interaction.id)
        ]
        if (
            len(records) != 1
            or not records[0]["forwarding_eligible"]
            or (records[0]["target_id"] != self.binding.definition.target_id)
        ):
            raise ValueError("smoke_failed")
        self.calls += 1
        return self.binding.adapter.invoke(interaction)


def check_result(response, action, sink, *, text=None):
    if response.status_code != (403 if action == "BLOCK" else 200):
        raise ValueError("smoke_failed")
    body = response.json()
    if body.get("action") != action:
        raise ValueError("smoke_failed")
    records = [
        r for r in sink.records if r["interaction_id"] == body.get("interaction_id")
    ]
    if (
        len(records) != 1
        or records[0].get("action") != action
        or (records[0]["forwarding_eligible"] is not (action != "BLOCK"))
    ):
        raise ValueError("smoke_failed")
    if action == "BLOCK":
        if "result" in body:
            raise ValueError("smoke_failed")
        return 0
    result = body.get("result")
    if type(result) is not dict or set(result) != {"content"}:
        raise ValueError("smoke_failed")
    content = result["content"]
    if type(content) is not str or any(0xD800 <= ord(c) <= 0xDFFF for c in content):
        raise ValueError("smoke_failed")
    if text is not None and content != text:
        raise ValueError("smoke_failed")
    return len(content)


def run_smoke(target_registry=None):
    sink = RecordingSink()
    targets = default_targets() if target_registry is None else target_registry
    observed = {
        r.definition.target_id: ObservedTarget(r, sink) for r in targets.registrations
    }
    registry = TargetRegistry(
        tuple(
            RegisteredTarget(r.definition, observed[r.definition.target_id])
            for r in targets.registrations
        )
    )
    started = perf_counter()
    with TestClient(create_app(audit_sink=sink, target_registry=registry)) as client:
        response = client.post(
            "/v1/interactions",
            json={
                "target_id": "local-ollama",
                "content": "Describe a sunrise in one sentence.",
            },
        )
        length = check_result(response, "ALLOW", sink)
        if observed["local-ollama"].calls != 1:
            raise ValueError("smoke_failed")
        response = client.post(
            "/v1/interactions",
            json={"target_id": "local-echo", "content": "smoke echo"},
        )
        check_result(response, "ALLOW", sink, text="smoke echo")
        if observed["local-echo"].calls != 1:
            raise ValueError("smoke_failed")
        response = client.post(
            "/v1/interactions",
            json={
                "target_id": "local-ollama",
                "content": "Authorization: Bearer synthetic",
            },
        )
        check_result(response, "BLOCK", sink)
        if observed["local-ollama"].calls != 1 or len(sink.records) != 3:
            raise ValueError("smoke_failed")
    return length, perf_counter() - started


def main(target_registry=None):
    try:
        length, duration = run_smoke(target_registry)
    except Exception:
        print("SMOKE FAIL — prerequisites unavailable or verification failed")
        return 1
    print(
        f"SMOKE PASS status=200 action=ALLOW length={length} "
        f"elapsed_seconds={duration:.3f}; echo=PASS block=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
