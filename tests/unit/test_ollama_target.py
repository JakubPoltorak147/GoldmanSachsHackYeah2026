import json
from dataclasses import FrozenInstanceError, replace

import httpx
import pytest

from app.control_layer.domain import Interaction, TargetError
from app.control_layer.ollama_target import (
    TARGET_SYSTEM_PROMPT,
    OllamaSettings,
    OllamaTextTarget,
    load_ollama_settings,
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
    body=b'{"done":true,"response":"answer"}',
    status=200,
    headers=None,
    settings=None,
    fail=False,
):
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

    target = OllamaTextTarget(settings or OllamaSettings(), client_factory=factory)
    return target, calls, clients, options, streams


def invoke(target):
    return target.invoke(Interaction.create("local-ollama", " RAW_PROMPT 😀 "))


def test_defaults_loader_and_frozen_settings():
    settings = load_ollama_settings({})
    assert settings == OllamaSettings(
        "http://127.0.0.1:11434", "qwen2.5:0.5b", 2, 60, 65536, 16384
    )
    with pytest.raises(FrozenInstanceError):
        settings.model = "other:tag"
    overrides = {
        "BASE_URL": "http://[::1]:1/",
        "MODEL": "a-b.c_d:0.1",
        "CONNECT_TIMEOUT_SECONDS": "0.1",
        "RESPONSE_TIMEOUT_SECONDS": "120",
        "MAX_RESPONSE_BYTES": "1024",
        "MAX_OUTPUT_CHARACTERS": "65536",
    }
    loaded = load_ollama_settings(
        {"CONTROL_LAYER_OLLAMA_" + k: v for k, v in overrides.items()}
    )
    assert loaded == OllamaSettings(
        "http://[::1]:1/", "a-b.c_d:0.1", 0.1, 120, 1024, 65536
    )


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
    "response_timeout_seconds": [True, "60", float("-inf"), 0, 120.01],
    "max_response_bytes": [True, "1024", 1024.0, 1023, 1048577],
    "max_output_characters": [False, "1", 1.0, 0, 65537],
}


@pytest.mark.parametrize(
    "field,value", [(k, v) for k, vs in INVALID.items() for v in vs]
)
def test_invalid_typed_settings_are_sanitized(field, value):
    with pytest.raises(ValueError) as caught:
        replace(OllamaSettings(), **{field: value})
    assert str(caught.value) == "invalid_target_configuration"
    assert caught.value.__cause__ is None and caught.value.__suppress_context__


@pytest.mark.parametrize("field", OllamaSettings.__dataclass_fields__)
@pytest.mark.parametrize("value", ["", "RAW_SECRET", "nan", "inf", " 2 "])
def test_invalid_environment(field, value):
    with pytest.raises(ValueError, match="^invalid_target_configuration$") as caught:
        load_ollama_settings({"CONTROL_LAYER_OLLAMA_" + field.upper(): value})
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
    with pytest.raises(ValueError, match="^invalid_target_configuration$"):
        load_ollama_settings({"CONTROL_LAYER_OLLAMA_" + field.upper(): value})


@pytest.mark.parametrize(
    "field,values",
    [
        ("connect_timeout_seconds", (0.1, 10)),
        ("response_timeout_seconds", (0.1, 120)),
        ("max_response_bytes", (1024, 1048576)),
        ("max_output_characters", (1, 65536)),
    ],
)
def test_inclusive_numeric_bounds(field, values):
    for value in values:
        assert getattr(replace(OllamaSettings(), **{field: value}), field) == value


def test_exact_request_timeouts_and_closed_resources(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://private:1234")
    target, calls, clients, options, streams = target_for()
    assert invoke(target).content == "answer"
    assert len(calls) == 1
    assert str(calls[0].url) == "http://127.0.0.1:11434/api/generate"
    assert calls[0].method == "POST"
    assert json.loads(calls[0].content) == {
        "model": "qwen2.5:0.5b",
        "system": TARGET_SYSTEM_PROMPT,
        "prompt": " RAW_PROMPT 😀 ",
        "stream": False,
    }
    assert calls[0].headers["accept-encoding"] == "identity"
    assert calls[0].extensions["timeout"] == {
        "connect": 2,
        "read": 60,
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
    with pytest.raises(TargetError) as caught:
        invoke(target)
    assert str(caught.value) == "target_failed"
    assert caught.value.__cause__ is None and caught.value.__suppress_context__
    assert len(calls) == 1 and clients[0].is_closed and streams[0].closed
    assert "local model target failed" in caplog.text
    assert "RAW_" not in caplog.text
    assert any(
        record.__dict__.get("stage") == "response_validation"
        for record in caplog.records
    )


@pytest.mark.parametrize("status", [301, 302, 307, 400, 404, 429, 500])
def test_status_failure_no_retry_or_leak(status, caplog):
    target, calls, clients, _, streams = target_for(
        b"RAW_PROMPT RAW_OUTPUT", status, {"Location": "http://private/"}
    )
    with pytest.raises(TargetError, match="^target_failed$"):
        invoke(target)
    assert len(calls) == 1 and clients[0].is_closed and streams[0].closed
    assert "RAW_" not in caplog.text


def test_content_bearing_client_exception(caplog):
    target, calls, clients, _, _ = target_for(fail=True)
    with pytest.raises(TargetError) as caught:
        invoke(target)
    assert str(caught.value) == "target_failed" and caught.value.__cause__ is None
    assert caught.value.__suppress_context__
    assert len(calls) == 1 and clients[0].is_closed
    assert "RAW_" not in caplog.text


@pytest.mark.parametrize("text", ["", "😀", "RAW_OUTPUT"])
def test_only_completed_text_returned_ignoring_metadata(text):
    body = json.dumps(
        {
            "done": True,
            "response": text,
            "context": [1],
            "thinking": "private",
            "model": "untrusted",
        }
    ).encode()
    assert invoke(target_for(body)[0]).content == text


@pytest.mark.parametrize("length", [1024, 1025])
@pytest.mark.parametrize(
    "headers", [{}, {"Content-Length": "1"}, {"Transfer-Encoding": "chunked"}]
)
def test_raw_byte_cap_independent_of_length(length, headers):
    body = b'{"done":true,"response":"x"}'
    body += b" " * (length - len(body))
    target, _, clients, _, streams = target_for(
        body,
        headers=headers,
        settings=replace(OllamaSettings(), max_response_bytes=1024),
    )
    if length == 1024:
        assert invoke(target).content == "x"
    else:
        with pytest.raises(TargetError):
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
        headers=headers, settings=replace(OllamaSettings(), max_response_bytes=1024)
    )
    with pytest.raises(TargetError):
        invoke(target)
    assert clients[0].is_closed and streams[0].closed


@pytest.mark.parametrize("length", [3, 4])
def test_output_scalar_cap(length):
    target = target_for(
        json.dumps({"done": True, "response": "😀" * length}).encode(),
        settings=replace(OllamaSettings(), max_output_characters=3),
    )[0]
    if length == 3:
        assert invoke(target).content == "😀" * 3
    else:
        with pytest.raises(TargetError):
            invoke(target)
