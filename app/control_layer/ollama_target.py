"""Bounded synchronous generation against an operator-owned loopback runtime."""

import json
import math
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass

import httpx

from app.control_layer.domain import Interaction, TargetError
from app.control_layer.targets import TargetResult


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5:0.5b"
    connect_timeout_seconds: float = 2.0
    response_timeout_seconds: float = 60.0
    max_response_bytes: int = 65536
    max_output_characters: int = 16384

    def __post_init__(self):
        try:
            if type(self.base_url) is not str:
                raise ValueError()
            origin = re.fullmatch(
                r"http://(127\.0\.0\.1|\[::1\]):([0-9]{1,5})/?", self.base_url
            )
            if origin is None or not 1 <= int(origin[2]) <= 65535:
                raise ValueError()
            if (
                type(self.model) is not str
                or not 1 <= len(self.model) <= 128
                or re.fullmatch(
                    r"[a-z0-9][a-z0-9._-]*:[a-z0-9][a-z0-9._-]*", self.model
                )
                is None
                or "cloud" in self.model.split(":")[1]
            ):
                raise ValueError()
            for value, upper in (
                (self.connect_timeout_seconds, 10),
                (self.response_timeout_seconds, 120),
            ):
                if (
                    type(value) not in (int, float)
                    or not math.isfinite(value)
                    or not 0.1 <= value <= upper
                ):
                    raise ValueError()
            for value, lower, upper in (
                (self.max_response_bytes, 1024, 1048576),
                (self.max_output_characters, 1, 65536),
            ):
                if type(value) is not int or not lower <= value <= upper:
                    raise ValueError()
        except Exception:
            raise ValueError("invalid_target_configuration") from None


def load_ollama_settings(environ: Mapping[str, str] | None = None) -> OllamaSettings:
    source = os.environ if environ is None else environ
    defaults = OllamaSettings()
    values = {}
    try:
        for name in defaults.__dataclass_fields__:
            raw = source.get("CONTROL_LAYER_OLLAMA_" + name.upper())
            if raw is None:
                continue
            if type(raw) is not str or not raw:
                raise ValueError()
            if name.endswith("_seconds"):
                if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", raw) is None:
                    raise ValueError()
                values[name] = float(raw)
            elif name.startswith("max_"):
                if re.fullmatch(r"[0-9]+", raw) is None:
                    raise ValueError()
                values[name] = int(raw)
            else:
                values[name] = raw
        return OllamaSettings(**values)
    except Exception:
        raise ValueError("invalid_target_configuration") from None


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError()
        result[key] = value
    return result


def _invalid_constant(_value):
    raise ValueError()


class OllamaTextTarget:
    def __init__(
        self,
        settings: OllamaSettings,
        *,
        client_factory: Callable[..., httpx.Client] = httpx.Client,
    ) -> None:
        if type(settings) is not OllamaSettings:
            raise ValueError("invalid_target_configuration") from None
        self.settings = settings
        self._client_factory = client_factory

    def invoke(self, interaction: Interaction) -> TargetResult:
        settings = self.settings
        try:
            timeout = httpx.Timeout(
                connect=settings.connect_timeout_seconds,
                read=settings.response_timeout_seconds,
                write=settings.connect_timeout_seconds,
                pool=settings.connect_timeout_seconds,
            )
            with self._client_factory(
                timeout=timeout,
                trust_env=False,
                follow_redirects=False,
                transport=httpx.HTTPTransport(retries=0),
            ) as client:
                with client.stream(
                    "POST",
                    settings.base_url.rstrip("/") + "/api/generate",
                    headers={"Accept-Encoding": "identity"},
                    json={
                        "model": settings.model,
                        "prompt": interaction.content,
                        "stream": False,
                    },
                ) as response:
                    if response.status_code != 200:
                        raise ValueError()
                    if response.headers.get("content-encoding", "identity").lower() != (
                        "identity"
                    ):
                        raise ValueError()
                    length = response.headers.get("content-length")
                    if length is not None and (
                        re.fullmatch(r"[0-9]+", length) is None
                        or int(length) > settings.max_response_bytes
                    ):
                        raise ValueError()
                    body = bytearray()
                    for chunk in response.iter_raw():
                        if len(body) + len(chunk) > settings.max_response_bytes:
                            raise ValueError()
                        body.extend(chunk)
                    data = json.loads(
                        body.decode("utf-8"),
                        object_pairs_hook=_object,
                        parse_constant=_invalid_constant,
                    )
                    if (
                        type(data) is not dict
                        or "error" in data
                        or data.get("done") is not True
                        or type(data.get("response")) is not str
                    ):
                        raise ValueError()
                    content = data["response"]
                    if len(content) > settings.max_output_characters or any(
                        0xD800 <= ord(c) <= 0xDFFF for c in content
                    ):
                        raise ValueError()
                    return TargetResult(content)
        except Exception:
            raise TargetError() from None
