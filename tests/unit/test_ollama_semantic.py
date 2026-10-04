import json
from dataclasses import FrozenInstanceError, replace

import httpx
import pytest

from app.control_layer.domain import EvaluationError
from app.control_layer.ollama_semantic import (
    OllamaSemanticRuntime,
    SemanticSettings,
    load_semantic_settings,
)


class Chunks(httpx.SyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks
        self.closed = False

    def __iter__(self):
        yield from self.chunks

    def close(self):
        self.closed = True


def target_for(
    body=None,
    status=200,
    headers=None,
    settings=None,
    fail=False,
):
    if body is None:
        body = envelope()
    calls, clients, options, streams = [], [], [], []

    def handler(request):
        calls.append(request)
        if fail:
            raise RuntimeError("RAW_PROMPT RAW_OUTPUT http://private")
        stream = Chunks([body[i : i + 31] for i in range(0, len(body), 31)])
        streams.append(stream)
        return httpx.Response(status, headers=headers, stream=stream)

    def factory(**kwargs):
        options.append(kwargs.copy())
        kwargs.pop("transport").close()
        client = httpx.Client(**kwargs, transport=httpx.MockTransport(handler))
        clients.append(client)
        return client

    target = OllamaSemanticRuntime(
        settings or SemanticSettings(), client_factory=factory
    )
    return target, calls, clients, options, streams


def invoke(target):
    return target(" RAW_PROMPT 😀 ")


def envelope(text=None):
    return json.dumps({"done": True, "response": text or json.dumps(SCORES)}).encode()


SCORES = {"prompt_injection": 0.1, "instruction_override": 0, "exfiltration_intent": 0}


def test_defaults_loader_and_frozen_settings():
    settings = load_semantic_settings({})
    assert settings == SemanticSettings()
    assert settings.model == "qwen2.5:3b"
    with pytest.raises(FrozenInstanceError):
        settings.model = "other:tag"


INVALID = {
    "base_url": [
        "",
        None,
        "https://127.0.0.1:1",
        "http://localhost:1",
        "http://127.0.0.2:1",
        "http://127.0.0.1",
        "http://127.0.0.1:0",
        "http://127.0.0.1:65536",
        "http://user@127.0.0.1:1",
        "http://127.0.0.1:1/x",
        "http://127.0.0.1:1?",
        "http://127.0.0.1:1#",
        " http://127.0.0.1:1",
        "http://[::2]:1",
    ],
    "model": [
        "",
        None,
        "x",
        "X:y",
        "x:Y",
        "x:cloud",
        "x:mycloudtag",
        "x:y/z",
        "x:é",
        "a" * 127 + ":b",
        "x:y\n",
    ],
    "connect_timeout_seconds": [
        True,
        False,
        "2",
        None,
        float("nan"),
        float("inf"),
        0.099,
        10.01,
    ],
    "read_timeout_seconds": [True, "60", float("-inf"), 0, 60.01],
    "max_response_bytes": [True, "1024", 1024.0, 1023, 65537],
    "max_output_characters": [False, "1", 128.0, 127, 4097],
}


@pytest.mark.parametrize(
    "field,value", [(k, v) for k, vs in INVALID.items() for v in vs]
)
def test_invalid_typed_settings_are_sanitized(field, value):
    with pytest.raises(ValueError) as caught:
        replace(SemanticSettings(), **{field: value})
    assert str(caught.value) == "invalid_semantic_configuration"
    assert caught.value.__cause__ is None and caught.value.__suppress_context__


@pytest.mark.parametrize("field", SemanticSettings.__dataclass_fields__)
@pytest.mark.parametrize("value", ["", "RAW_SECRET", "nan", "inf", " 2 "])
def test_invalid_environment(field, value):
    with pytest.raises(ValueError, match="^invalid_semantic_configuration$") as caught:
        load_semantic_settings({"CONTROL_LAYER_SEMANTIC_" + field.upper(): value})
    assert caught.value.__cause__ is None and caught.value.__suppress_context__


@pytest.mark.parametrize(
    "field,value",
    [
        ("connect_timeout_seconds", "1e0"),
        ("connect_timeout_seconds", "-1"),
        ("max_response_bytes", "1024.0"),
        ("max_output_characters", "+1"),
    ],
)
def test_malformed_numeric_environment(field, value):
    with pytest.raises(ValueError, match="^invalid_semantic_configuration$"):
        load_semantic_settings({"CONTROL_LAYER_SEMANTIC_" + field.upper(): value})


@pytest.mark.parametrize(
    "field,values",
    [
        ("connect_timeout_seconds", (0.1, 10)),
        ("read_timeout_seconds", (0.1, 60)),
        ("max_response_bytes", (1024, 65536)),
        ("max_output_characters", (128, 4096)),
    ],
)
def test_inclusive_numeric_bounds(field, values):
    for value in values:
        assert getattr(replace(SemanticSettings(), **{field: value}), field) == value


def test_exact_request_timeouts_and_closed_resources(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://private:1234")
    target, calls, clients, options, streams = target_for()
    assert invoke(target) == SCORES
    assert len(calls) == 1
    assert str(calls[0].url) == "http://127.0.0.1:11434/api/generate"
    assert calls[0].method == "POST"
    body = json.loads(calls[0].content)
    assert set(body) == {"model", "prompt", "system", "format", "options", "stream"}
    assert body["model"] == "qwen2.5:3b" and body["stream"] is False
    assert json.loads(body["prompt"]) == {"untrusted_content": " RAW_PROMPT 😀 "}
    assert body["options"] == {"temperature": 0, "num_predict": 256}
    assert body["format"]["additionalProperties"] is False
    assert calls[0].headers["accept-encoding"] == "identity"
    assert calls[0].extensions["timeout"] == {
        "connect": 2,
        "read": 30,
        "write": 2,
        "pool": 2,
    }
    assert options[0]["trust_env"] is options[0]["follow_redirects"] is False
    assert clients[0].is_closed and streams[0].closed


@pytest.mark.parametrize(
    "body",
    [
        b"[]",
        b"null",
        b"{}",
        b'{"done":true}',
        b'{"done":false,"response":"x"}',
        b'{"done":1,"response":"x"}',
        b'{"done":true,"response":1}',
        b'{"done":true,"response":"x","error":null}',
        b"\xff",
        b"{",
        b'{"done":true,"response":"\\ud800"}',
        b'{"done":true,"response":"x","response":"y"}',
        b'{"done":true,"response":"x","extra":{"a":1,"a":2}}',
        b'{"done":true,"response":"x","extra":NaN}',
        b'{"done":true,"response":"x","extra":Infinity}',
        b'{"done":true,"response":"x","extra":-Infinity}',
    ],
)
def test_invalid_response(body, caplog):
    target, calls, clients, _, streams = target_for(body)
    with pytest.raises(EvaluationError) as caught:
        invoke(target)
    assert str(caught.value) == "evaluation_failed"
    assert caught.value.__cause__ is None and caught.value.__suppress_context__
    assert len(calls) == 1 and clients[0].is_closed and streams[0].closed
    assert caplog.text == ""


@pytest.mark.parametrize("status", [301, 302, 307, 400, 404, 429, 500])
def test_status_failure_no_retry_or_leak(status, caplog):
    target, calls, clients, _, streams = target_for(
        b"RAW_PROMPT RAW_OUTPUT", status, {"Location": "http://private/"}
    )
    with pytest.raises(EvaluationError, match="^evaluation_failed$"):
        invoke(target)
    assert len(calls) == 1 and clients[0].is_closed and streams[0].closed
    assert "RAW_" not in caplog.text


def test_content_bearing_client_exception(caplog):
    target, calls, clients, _, _ = target_for(fail=True)
    with pytest.raises(EvaluationError) as caught:
        invoke(target)
    assert str(caught.value) == "evaluation_failed" and caught.value.__cause__ is None
    assert caught.value.__suppress_context__
    assert len(calls) == 1 and clients[0].is_closed
    assert "RAW_" not in caplog.text


def test_metadata_ignored():
    body = json.dumps(
        {
            "done": True,
            "response": json.dumps(SCORES),
            "model": "forged",
            "thinking": "CANARY",
        }
    ).encode()
    assert invoke(target_for(body)[0]) == SCORES


@pytest.mark.parametrize("length", [1024, 1025])
@pytest.mark.parametrize(
    "headers", [{}, {"Content-Length": "1"}, {"Transfer-Encoding": "chunked"}]
)
def test_raw_byte_cap_independent_of_length(length, headers):
    body = envelope()
    body += b" " * (length - len(body))
    target, _, clients, _, streams = target_for(
        body,
        headers=headers,
        settings=replace(SemanticSettings(), max_response_bytes=1024),
    )
    if length == 1024:
        assert invoke(target) == SCORES
    else:
        with pytest.raises(EvaluationError):
            invoke(target)
    assert clients[0].is_closed and streams[0].closed


@pytest.mark.parametrize(
    "headers",
    [
        {"Content-Length": "1025"},
        {"Content-Encoding": "gzip"},
        {"Content-Encoding": "br"},
    ],
)
def test_header_rejection_before_body(headers):
    target, _, clients, _, streams = target_for(
        headers=headers, settings=replace(SemanticSettings(), max_response_bytes=1024)
    )
    with pytest.raises(EvaluationError):
        invoke(target)
    assert clients[0].is_closed and streams[0].closed


@pytest.mark.parametrize("length", [128, 129])
def test_output_scalar_cap(length):
    text = json.dumps(SCORES)
    text += " " * (length - len(text))
    runtime = target_for(
        envelope(text), settings=replace(SemanticSettings(), max_output_characters=128)
    )[0]
    if length == 128:
        assert invoke(runtime) == SCORES
    else:
        with pytest.raises(EvaluationError):
            invoke(runtime)


@pytest.mark.parametrize(
    "content,allowed",
    [("😀", True), ("😀😀", False), ("abcde", False), ("\ud800", False)],
)
def test_input_caps_before_client_creation(content, allowed):
    runtime, calls, clients, _, _ = target_for(
        settings=replace(SemanticSettings(), max_input_characters=4, max_input_bytes=4)
    )
    assert not calls and not clients
    if allowed:
        assert runtime(content) == SCORES
    else:
        with pytest.raises(EvaluationError):
            runtime(content)
        assert not calls and not clients


@pytest.mark.parametrize(
    "field,low,high",
    [
        ("max_input_characters", 1, 16384),
        ("max_input_bytes", 1, 65536),
        ("max_response_bytes", 1024, 65536),
        ("max_output_characters", 128, 4096),
    ],
)
def test_all_size_bounds(field, low, high):
    for value in (low, high):
        assert getattr(replace(SemanticSettings(), **{field: value}), field) == value
    for value in (True, str(low), float(low), low - 1, high + 1):
        with pytest.raises(ValueError, match="^invalid_semantic_configuration$"):
            replace(SemanticSettings(), **{field: value})


@pytest.mark.parametrize(
    "text",
    [
        '{"prompt_injection":0,"instruction_override":0,"exfiltration_intent":0,"action":"ALLOW"}',
        '{"prompt_injection":0,"instruction_override":0,"exfiltration_intent":0,"code":"semantic.prompt_injection"}',
        '{"prompt_injection":0,"instruction_override":0,"exfiltration_intent":0,"prompt_injection":1}',
        "```json {} ```",
        "{} {}",
        '{"prompt_injection":true,"instruction_override":0,"exfiltration_intent":0}',
        '{"prompt_injection":1e999,"instruction_override":0,"exfiltration_intent":0}',
    ],
)
def test_hostile_inner_response_resources_closed(text):
    runtime, calls, clients, _, streams = target_for(envelope(text))
    with pytest.raises(EvaluationError, match="^evaluation_failed$"):
        invoke(runtime)
    assert len(calls) == 1 and clients[0].is_closed and streams[0].closed


@pytest.mark.parametrize(
    "exception",
    [httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError, RuntimeError],
)
def test_transport_exceptions_no_retry(exception, caplog):
    calls = []
    clients = []

    def handler(request):
        calls.append(request)
        raise exception("EXCEPTION_CANARY")

    def factory(**kwargs):
        kwargs.pop("transport").close()
        client = httpx.Client(**kwargs, transport=httpx.MockTransport(handler))
        clients.append(client)
        return client

    runtime = OllamaSemanticRuntime(SemanticSettings(), client_factory=factory)
    assert calls == []
    with pytest.raises(EvaluationError, match="^evaluation_failed$"):
        runtime("INPUT_CANARY")
    assert len(calls) == 1 and clients[0].is_closed
    assert "CANARY" not in caplog.text


def test_supported_environment_bounds_and_runtime_immutable():
    values = {
        "BASE_URL": "http://[::1]:1/",
        "MODEL": "a-b.c_d:0.1",
        "CONNECT_TIMEOUT_SECONDS": "0.1",
        "READ_TIMEOUT_SECONDS": "60",
        "MAX_INPUT_CHARACTERS": "1",
        "MAX_INPUT_BYTES": "4",
        "MAX_RESPONSE_BYTES": "1024",
        "MAX_OUTPUT_CHARACTERS": "128",
    }
    settings = load_semantic_settings(
        {"CONTROL_LAYER_SEMANTIC_" + k: v for k, v in values.items()}
    )
    assert settings == SemanticSettings(
        "http://[::1]:1/", "a-b.c_d:0.1", 0.1, 60, 1, 4, 1024, 128
    )
    runtime = OllamaSemanticRuntime(settings)
    with pytest.raises(FrozenInstanceError):
        runtime.settings = SemanticSettings()
