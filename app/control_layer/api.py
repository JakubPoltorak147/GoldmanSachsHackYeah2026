"""Strict HTTP adapter around the policy-governed interaction service."""

import os
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.exceptions import HTTPException

from app.control_layer.audit import AuditSink, JsonLinesAuditSink
from app.control_layer.composition import (
    bind_semantic_policy,
    default_controls,
    default_targets,
)
from app.control_layer.demo import DemoSettings, build_demo, load_demo_settings
from app.control_layer.domain import Action, Interaction
from app.control_layer.policy import load_policy
from app.control_layer.registry import ControlRegistry
from app.control_layer.reporting import ReportingProjection
from app.control_layer.reporting_api import reporting_error
from app.control_layer.reporting_api import router as reporting_router
from app.control_layer.reporting_store import PersistentAuditSink, ReportingStore
from app.control_layer.service import InteractionService
from app.control_layer.targets import TargetRegistry


class InteractionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    target_id: Literal["local-echo", "local-ollama"]
    content: str = Field(min_length=1, max_length=16384)

    @field_validator("content")
    @classmethod
    def unicode_scalars(cls, value: str) -> str:
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise ValueError("invalid_unicode")
        return value


class EchoResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    content: str


class ScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    scenario_id: str = Field(min_length=1, max_length=64)


class DecisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    interaction_id: UUID
    action: Action
    reason_code: Literal["no_findings", "policy_resolved"]
    finding_codes: list[str]
    result: EchoResult | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    error_code: Literal[
        "invalid_request",
        "evaluation_failed",
        "audit_failed",
        "target_failed",
        "service_unavailable",
        "not_found",
        "method_not_allowed",
    ]
    interaction_id: UUID | None = None


def _error(status: int, code: str, interaction_id: UUID | None = None) -> JSONResponse:
    payload = ErrorResponse(error_code=code, interaction_id=interaction_id)
    return JSONResponse(
        status_code=status, content=payload.model_dump(mode="json", exclude_none=True)
    )


def demo_error(status: int, code: str) -> JSONResponse:
    response = _error(status, code)
    response.headers["Cache-Control"] = "no-store"
    return response


def _origin(value: str):
    if not value or re.search(r"[\s\\%?#]", value) or value.endswith(":"):
        raise ValueError()
    parsed = urlsplit(value)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
        or re.fullmatch(r"[a-zA-Z0-9.:-]+", parsed.hostname) is None
    ):
        raise ValueError()
    port = (
        parsed.port
        if parsed.port is not None
        else (443 if parsed.scheme == "https" else 80)
    )
    if not 1 <= port <= 65535:
        raise ValueError()
    return parsed.scheme, parsed.hostname.lower(), port


def valid_origin(request: Request, *, required: bool) -> bool:
    origins = request.headers.getlist("origin")
    if not origins:
        return not required
    if len(origins) != 1:
        return False
    try:
        return _origin(origins[0]) == _origin(
            f"{request.url.scheme}://{request.url.netloc}"
        )
    except ValueError:
        return False


def create_app(
    *,
    policy_path: str | Path | None = None,
    audit_sink: AuditSink | None = None,
    target_registry: TargetRegistry | None = None,
    control_registry: ControlRegistry | None = None,
    reporting_store: ReportingStore | None = None,
    demo_settings: DemoSettings | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        controls = default_controls() if control_registry is None else control_registry
        settings = load_demo_settings() if demo_settings is None else demo_settings
        if type(settings) is not DemoSettings:
            raise ValueError("invalid_demo_configuration")
        policy = load_policy(
            policy_path
            if policy_path is not None
            else os.environ.get("CONTROL_LAYER_POLICY", "config/policy.yaml"),
            controls,
        )
        policy = bind_semantic_policy(policy)
        targets = default_targets() if target_registry is None else target_registry
        if type(targets) is not TargetRegistry:
            raise ValueError("invalid_composition")
        store = (
            reporting_store
            if reporting_store is not None
            else ReportingStore(
                os.environ.get(
                    "CONTROL_LAYER_REPORTING_DB", "var/security-reporting.sqlite3"
                )
            )
        )
        try:
            sink = PersistentAuditSink(
                audit_sink
                if audit_sink is not None
                else JsonLinesAuditSink(sys.stdout),
                store,
                ReportingProjection(policy, targets),
            )
            application.state.reporting = store
            application.state.service = InteractionService(policy, sink, targets)
            application.state.demo = build_demo(
                settings, application.state.service, controls
            )
            yield
        finally:
            if reporting_store is None:
                store.close()

    application = FastAPI(lifespan=lifespan)
    application.include_router(reporting_router)

    @application.middleware("http")
    async def reporting_slash_guard(request: Request, call_next):
        # Router redirects reflect the entire URL before route validation.
        # Reject noncanonical reporting paths without changing interaction routing.
        if request.url.path.startswith("/v1/reporting/") and request.url.path.endswith(
            "/"
        ):
            return reporting_error(404, "not_found")
        if request.url.path.startswith("/v1/demo/") and request.url.path.endswith("/"):
            return demo_error(404, "not_found")
        return await call_next(request)

    dashboard_root = Path(__file__).resolve().parents[1] / "dashboard"
    application.mount(
        "/dashboard/assets",
        StaticFiles(directory=dashboard_root),
        name="dashboard-assets",
    )

    @application.get("/dashboard", include_in_schema=False)
    def dashboard():
        return FileResponse(dashboard_root / "index.html")

    @application.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, _exception: RequestValidationError):
        if _request.url.path.startswith("/v1/demo/"):
            return demo_error(422, "invalid_request")
        return _error(422, "invalid_request")

    @application.exception_handler(HTTPException)
    async def http_failure(_request: Request, exception: HTTPException):
        if _request.url.path.startswith("/v1/demo/"):
            code = {404: "not_found", 405: "method_not_allowed"}.get(
                exception.status_code, "service_unavailable"
            )
            return demo_error(
                exception.status_code if exception.status_code in (404, 405) else 503,
                code,
            )
        if _request.url.path == "/v1/reporting" or _request.url.path.startswith(
            "/v1/reporting/"
        ):
            if exception.status_code == 404:
                return reporting_error(404, "not_found")
            if exception.status_code == 405:
                return reporting_error(405, "method_not_allowed")
            return reporting_error(503, "reporting_unavailable")
        # Starlette reports invalid UTF-8 JSON bodies as HTTP 400.
        if exception.status_code in (400, 422):
            return _error(422, "invalid_request")
        if exception.status_code == 404:
            return _error(404, "not_found")
        if exception.status_code == 405:
            return _error(405, "method_not_allowed")
        return _error(503, "service_unavailable")

    @application.exception_handler(Exception)
    async def unexpected_failure(_request: Request, _exception: Exception):
        if _request.url.path.startswith("/v1/demo/"):
            return demo_error(503, "service_unavailable")
        return _error(503, "service_unavailable")

    def demo_metadata(request: Request, kind: str):
        demo = request.app.state.demo
        if demo is None:
            return demo_error(404, "not_found")
        if request.query_params:
            return demo_error(422, "invalid_request")
        payload = demo.catalog() if kind == "scenarios" else demo.workspace
        return JSONResponse(
            payload.model_dump(mode="json"), headers={"Cache-Control": "no-store"}
        )

    @application.get("/v1/demo/scenarios")
    def catalog(request: Request):
        return demo_metadata(request, "scenarios")

    @application.get("/v1/demo/workspace")
    def workspace(request: Request):
        return demo_metadata(request, "workspace")

    @application.post(
        "/v1/interactions",
        response_model=DecisionResponse,
        response_model_exclude_none=True,
    )
    def interact(body: InteractionRequest | ScenarioRequest, request: Request):
        scenario = isinstance(body, ScenarioRequest)
        if not valid_origin(request, required=scenario):
            return _error(422, "invalid_request")
        service = request.app.state.service
        if scenario:
            demo = request.app.state.demo
            if demo is None:
                return _error(422, "invalid_request")
            try:
                definition, service = demo.resolve(body.scenario_id)
            except ValueError:
                return _error(422, "invalid_request")
            interaction = Interaction.create("local-ollama", definition.content)
        else:
            interaction = Interaction.create(body.target_id, body.content)
        outcome = service.evaluate(interaction)
        if outcome.error_code is not None:
            status = 502 if outcome.error_code == "target_failed" else 503
            return _error(status, outcome.error_code, outcome.interaction_id)
        decision = outcome.decision
        if decision is None:
            return _error(503, "service_unavailable", outcome.interaction_id)
        payload = DecisionResponse(
            interaction_id=outcome.interaction_id,
            action=decision.action,
            reason_code=decision.reason_code,
            finding_codes=[
                resolution.finding.code for resolution in decision.resolutions
            ],
            result=(
                EchoResult(content=outcome.target_result.content)
                if outcome.target_result is not None
                else None
            ),
        )
        return JSONResponse(
            status_code=403 if decision.action == Action.BLOCK else 200,
            content=payload.model_dump(mode="json", exclude_none=True),
        )

    return application
