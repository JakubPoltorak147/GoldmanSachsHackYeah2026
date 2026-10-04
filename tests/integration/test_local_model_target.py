"""Deterministic real HTTP boundary; never contacts a real Ollama installation."""

import io
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Barrier, Event, Lock, Thread

import httpx
import pytest
from fastapi.testclient import TestClient

from app.control_layer.api import create_app
from app.control_layer.audit import JsonLinesAuditSink
from app.control_layer.composition import default_controls
from app.control_layer.domain import Interaction, TargetError
from app.control_layer.ollama_target import (
    TARGET_SYSTEM_PROMPT,
    OllamaSettings,
    OllamaTextTarget,
)
from app.control_layer.registry import ControlRegistration, ControlRegistry
from app.control_layer.targets import (
    LocalEchoTarget,
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
)


class Runtime:
    def __init__(self):
        self.calls = []
        self.lock = Lock()
        self.release = Event()
        self.respond = self.normal
        self.check = lambda payload: None

    def normal(self, handler, payload):
        handler.send_body(
            json.dumps(
                {
                    "done": True,
                    "response": "reply:" + payload["prompt"],
                    "model": "UNTRUSTED_MODEL",
                    "thinking": "PRIVATE",
                }
            ).encode()
        )


@pytest.fixture
def runtime():
    runtime = Runtime()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send_body(self, body, status=200, headers=None):
            self.send_response(status)
            for name, value in (headers or {"Content-Length": str(len(body))}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()

        def do_POST(self):
            try:
                payload = json.loads(
                    self.rfile.read(int(self.headers["Content-Length"]))
                )
                assert self.path == "/api/generate"
                assert self.headers["Accept-Encoding"] == "identity"
                runtime.check(payload)
                with runtime.lock:
                    runtime.calls.append(payload)
                runtime.respond(self, payload)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    server.block_on_close = False
    runtime.url = f"http://127.0.0.1:{server.server_port}"
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
    thread.start()
    try:
        yield runtime
    finally:
        runtime.release.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()


def adapter(runtime, **overrides):
    return OllamaTextTarget(
        OllamaSettings(
            base_url=runtime.url,
            connect_timeout_seconds=0.1,
            response_timeout_seconds=0.1,
            **overrides,
        )
    )


def call(target, content="safe"):
    return target.invoke(Interaction.create("local-ollama", content))


def test_real_client_exact_request_and_uninspected_output(runtime, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:1")
    runtime.respond = lambda h, p: h.send_body(
        b'{"done":true,"response":"RAW_OUTPUT alice@example.com"}'
    )
    assert (
        call(adapter(runtime), " exact 😀 ").content == "RAW_OUTPUT alice@example.com"
    )
    assert runtime.calls == [
        {
            "model": "qwen2.5:0.5b",
            "system": TARGET_SYSTEM_PROMPT,
            "prompt": " exact 😀 ",
            "stream": False,
        }
    ]


@pytest.mark.parametrize("status", [301, 307, 400, 404, 429, 500])
def test_real_status_failure_no_retry(runtime, status, caplog):
    runtime.respond = lambda h, p: h.send_body(
        b"RAW_PROMPT RAW_OUTPUT",
        status,
        {"Location": "http://127.0.0.1:1/", "Content-Length": "21"},
    )
    with pytest.raises(TargetError, match="^target_failed$"):
        call(adapter(runtime))
    assert len(runtime.calls) == 1 and "RAW_" not in caplog.text


@pytest.mark.parametrize("mode", ["reset", "headers", "body"])
def test_reset_and_delayed_headers_body(runtime, mode):
    def respond(handler, payload):
        if mode == "reset":
            handler.connection.shutdown(socket.SHUT_RDWR)
            handler.connection.close()
            return
        if mode == "body":
            handler.send_response(200)
            handler.send_header("Content-Length", "100")
            handler.end_headers()
            handler.wfile.flush()
        runtime.release.wait(timeout=2)

    runtime.respond = respond
    with pytest.raises(TargetError, match="^target_failed$"):
        call(adapter(runtime))
    assert len(runtime.calls) == 1


def test_runtime_absent_connection_refused():
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
        target = OllamaTextTarget(OllamaSettings(base_url=f"http://127.0.0.1:{port}"))
        with pytest.raises(TargetError, match="^target_failed$"):
            call(target)


@pytest.mark.parametrize(
    "body,headers,limits",
    [
        (b"\xff", None, {}),
        (b'{"done":false,"response":"x"}', None, {}),
        (b'{"done":true,"response":"\\udfff"}', None, {}),
        (b'{"done":true,"response":"x","response":"y"}', None, {}),
        (b'{"done":true,"response":"xx"}', None, {"max_output_characters": 1}),
        (b"x" * 1025, {"Content-Length": "1025"}, {"max_response_bytes": 1024}),
        (b"x" * 1025, {"Connection": "close"}, {"max_response_bytes": 1024}),
        (b"RAW_OUTPUT", {"Content-Encoding": "gzip"}, {}),
    ],
)
def test_real_invalid_bodies_and_bounds(runtime, body, headers, limits):
    runtime.respond = lambda h, p: h.send_body(body, headers=headers)
    with pytest.raises(TargetError):
        call(adapter(runtime, **limits))
    assert len(runtime.calls) == 1


def test_chunked_oversized_body(runtime):
    def respond(h, p):
        h.send_response(200)
        h.send_header("Transfer-Encoding", "chunked")
        h.end_headers()
        for chunk in (b"x" * 512, b"x" * 512, b"x"):
            h.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
            h.wfile.flush()
        h.wfile.write(b"0\r\n\r\n")

    runtime.respond = respond
    with pytest.raises(TargetError):
        call(adapter(runtime, max_response_bytes=1024))
    assert len(runtime.calls) == 1


class RecordingSink:
    def __init__(self):
        self.events = []
        self.lock = Lock()

    def emit(self, event):
        with self.lock:
            self.events.append(event.safe_record())


class BoundAdapter:
    """Test-only per-request association for inspecting pre-dispatch evidence."""

    def __init__(self, target, sink, runtime):
        self.target, self.sink = target, sink
        self.requests = {}
        self.lock = Lock()
        self.runtime = runtime
        runtime.check = self.check

    def check(self, payload):
        with self.lock:
            identifier = self.requests[payload["prompt"]]
        with self.sink.lock:
            assert any(
                e["interaction_id"] == identifier
                and e["forwarding_eligible"]
                and e["target_id"] == "local-ollama"
                for e in self.sink.events
            )

    def invoke(self, interaction):
        with self.lock:
            self.requests[interaction.content] = str(interaction.id)
        return self.target.invoke(interaction)


def gateway(runtime, *, sink=None, controls=None, target=None):
    sink = sink if sink is not None else RecordingSink()
    target = (
        target if target is not None else BoundAdapter(adapter(runtime), sink, runtime)
    )
    targets = TargetRegistry(
        (
            RegisteredTarget(TargetDefinition("local-echo"), LocalEchoTarget()),
            RegisteredTarget(TargetDefinition("local-ollama"), target),
        )
    )
    app = create_app(
        audit_sink=sink, target_registry=targets, control_registry=controls
    )
    return app, sink


def post(client, content="safe", target="local-ollama", **extra):
    return client.post(
        "/v1/interactions", json={"target_id": target, "content": content, **extra}
    )


@pytest.mark.parametrize(
    "content,action,forwarded,status",
    [
        (" exact 😀 ", "ALLOW", " exact 😀 ", 200),
        (
            "email alice@example.com SSN: 123-45-6789",
            "REDACT",
            "email [REDACTED] SSN: [REDACTED]",
            200,
        ),
        ("Authorization: Bearer abcdefghijklmnop", "BLOCK", None, 403),
        ("__import__('os').system(", "BLOCK", None, 403),
    ],
)
def test_governed_dispatch_and_audit_privacy(
    runtime, content, action, forwarded, status, caplog
):
    app, sink = gateway(runtime)
    with TestClient(app) as client:
        response = post(client, content)
    assert response.status_code == status
    assert response.json()["action"] == action
    assert len(sink.events) == 1 and len(sink.events[0]["evaluated_controls"]) == 6
    assert sink.events[0]["target_id"] == "local-ollama"
    assert sink.events[0]["forwarding_eligible"] is (forwarded is not None)
    assert len(runtime.calls) == (forwarded is not None)
    if forwarded is not None:
        assert runtime.calls[0]["prompt"] == forwarded
        assert response.json()["result"] == {"content": "reply:" + forwarded}
    else:
        assert "result" not in response.json()
    assert content not in json.dumps(sink.events) + caplog.text
    assert "alice@example.com" not in json.dumps(sink.events) + caplog.text
    assert "UNTRUSTED_MODEL" not in json.dumps(sink.events)


@pytest.mark.parametrize("gate", ["control", "policy", "audit", "poisoned"])
def test_failed_gates_zero_network(runtime, gate, monkeypatch, caplog):
    controls = default_controls()
    sink = RecordingSink()
    if gate == "control":

        class FailedControl:
            def evaluate(self, interaction):
                raise RuntimeError("RAW_PROMPT")

        first = controls.registrations[0]
        controls = ControlRegistry(
            (
                ControlRegistration(first.definition, FailedControl()),
                *controls.registrations[1:],
            )
        )
    if gate == "policy":

        def fail(*args):
            raise RuntimeError("RAW_PROMPT")

        monkeypatch.setattr("app.control_layer.service.decide", fail)
    if gate == "audit":

        def fail(event):
            raise RuntimeError("RAW_PROMPT")

        sink.emit = fail
    if gate == "poisoned":

        class BrokenStream(io.StringIO):
            def write(self, value):
                return 1

        sink = JsonLinesAuditSink(BrokenStream())
    app, _ = gateway(runtime, sink=sink, controls=controls, target=adapter(runtime))
    with TestClient(app) as client:
        for _ in range(2):
            result = post(client, "RAW_PROMPT")
            assert result.status_code == 503
            assert result.json()["error_code"] == (
                "evaluation_failed" if gate in ("control", "policy") else "audit_failed"
            )
    assert runtime.calls == [] and "RAW_PROMPT" not in caplog.text


def test_eligible_failure_preserves_only_decision(runtime, caplog):
    runtime.respond = lambda h, p: h.send_body(b"RAW_PROMPT RAW_OUTPUT", status=500)
    app, sink = gateway(runtime)
    with TestClient(app) as client:
        response = post(client, "RAW_PROMPT")
    assert (
        response.status_code == 502 and response.json()["error_code"] == "target_failed"
    )
    assert "result" not in response.json() and len(runtime.calls) == 1
    assert len(sink.events) == 1 and sink.events[0]["action"] == "ALLOW"
    assert sink.events[0]["forwarding_eligible"] is True
    assert "RAW_" not in json.dumps(sink.events) + response.text + caplog.text


def test_client_exception_privacy_at_gateway(runtime, caplog):
    def factory(**kwargs):
        kwargs["transport"].close()
        raise RuntimeError("RAW_PROMPT RAW_OUTPUT http://private")

    target = OllamaTextTarget(OllamaSettings(), client_factory=factory)
    app, sink = gateway(runtime, target=target)
    with TestClient(app) as client:
        response = post(client, "RAW_PROMPT")
    assert response.status_code == 502
    assert "RAW_" not in response.text + json.dumps(sink.events) + caplog.text
    assert runtime.calls == []


@pytest.mark.parametrize(
    "target",
    ["ollama", "http://127.0.0.1:11434", "RAW_SECRET", "qwen2.5:0.5b", "internal"],
)
def test_unknown_public_target_no_audit(runtime, target):
    app, sink = gateway(runtime)
    with TestClient(app) as client:
        response = post(client, "RAW_PROMPT", target)
    assert response.status_code == 422
    assert response.json() == {"error_code": "invalid_request"}
    assert sink.events == [] and runtime.calls == []


@pytest.mark.parametrize(
    "extra", [{"model": "other:tag"}, {"url": "http://private"}, {"timeout": 1}]
)
def test_caller_cannot_override_settings(runtime, extra):
    app, sink = gateway(runtime)
    with TestClient(app) as client:
        response = post(client, **extra)
    assert response.status_code == 422 and sink.events == [] and runtime.calls == []


def test_unresolved_internal_and_missing_public_registry(runtime):
    sink = RecordingSink()
    app = create_app(audit_sink=sink, target_registry=TargetRegistry(()))
    with TestClient(app) as client:
        response = post(client, "RAW_PROMPT")
        assert response.status_code == 503
        assert response.json()["error_code"] == "evaluation_failed"
        for identifier in ("RAW_SECRET", "http://private", "qwen2.5:0.5b"):
            outcome = app.state.service.evaluate(
                Interaction.create(identifier, "RAW_PROMPT")
            )
            assert outcome.error_code == "evaluation_failed"
    assert runtime.calls == []
    assert all(
        e["target_id"] == "unresolved"
        and e["evaluated_controls"] == []
        and "action" not in e
        and "finding_counts" not in e
        for e in sink.events
    )
    assert "RAW_" not in json.dumps(sink.events)


def test_retained_binding_after_audit_registry_replacement(runtime):
    app, sink = gateway(runtime)
    original_emit = sink.emit

    def emit(event):
        original_emit(event)
        app.state.service.targets = TargetRegistry(())

    sink.emit = emit
    with TestClient(app) as client:
        retained = app.state.service.targets.resolve("local-ollama")
        response = post(client)
        assert app.state.service.targets.registrations == ()
    assert response.status_code == 200 and len(runtime.calls) == 1
    assert retained.adapter.target.settings.base_url == runtime.url
    assert sink.events[0]["target_id"] == "local-ollama"


def test_concurrent_distinct_prompts_per_request_audit(runtime):
    barrier = Barrier(4)

    def respond(h, p):
        barrier.wait(timeout=5)
        runtime.normal(h, p)

    runtime.respond = respond
    # Longer inactivity allowance for deliberate barrier synchronization.
    target = OllamaTextTarget(
        replace(adapter(runtime).settings, response_timeout_seconds=5)
    )
    sink = RecordingSink()
    app, _ = gateway(runtime, sink=sink, target=BoundAdapter(target, sink, runtime))
    prompts = [f"distinct-{n}-😀" for n in range(4)]
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda p: post(client, p), prompts))
    assert len(runtime.calls) == len(sink.events) == 4
    assert {p["prompt"] for p in runtime.calls} == set(prompts)
    assert len({e["interaction_id"] for e in sink.events}) == 4
    for prompt, response in zip(prompts, responses, strict=True):
        assert response.status_code == 200
        assert response.json()["result"]["content"] == "reply:" + prompt
    assert all(p not in json.dumps(sink.events) for p in prompts)


def test_default_startup_and_echo_no_network_injected_registry_bypasses_settings(
    runtime, monkeypatch
):
    def fail(*args, **kwargs):
        pytest.fail("network at startup or echo")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fail)
    with TestClient(create_app(audit_sink=RecordingSink())) as client:
        assert post(client, "echo", "local-echo").json()["result"] == {
            "content": "echo"
        }
    monkeypatch.setenv("CONTROL_LAYER_OLLAMA_MODEL", "RAW_SECRET")
    app = create_app(
        audit_sink=RecordingSink(),
        target_registry=TargetRegistry(
            (RegisteredTarget(TargetDefinition("local-echo"), LocalEchoTarget()),)
        ),
    )
    with TestClient(app) as client:
        assert post(client, "echo", "local-echo").status_code == 200
    with pytest.raises(ValueError, match="^invalid_target_configuration$"):
        with TestClient(create_app()):
            pytest.fail("invalid defaults accepted")
