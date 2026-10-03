"""Strict HTTP adapter around the policy-governed interaction service."""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.exceptions import HTTPException

from app.control_layer.audit import AuditSink, JsonLinesAuditSink
from app.control_layer.composition import default_controls, default_targets
from app.control_layer.domain import Action, Interaction
from app.control_layer.policy import load_policy
from app.control_layer.registry import ControlRegistry
from app.control_layer.service import InteractionService
from app.control_layer.targets import TargetRegistry


class InteractionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    target_id: Literal["local-echo"]
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


def create_app(
    *,
    policy_path: str | Path | None = None,
    audit_sink: AuditSink | None = None,
    target_registry: TargetRegistry | None = None,
    control_registry: ControlRegistry | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        policy = load_policy(
            policy_path
            if policy_path is not None
            else os.environ.get("CONTROL_LAYER_POLICY", "config/policy.yaml"),
            default_controls() if control_registry is None else control_registry,
        )
        application.state.service = InteractionService(
            policy,
            audit_sink if audit_sink is not None else JsonLinesAuditSink(sys.stdout),
            default_targets() if target_registry is None else target_registry,
        )
        yield

    application = FastAPI(lifespan=lifespan)

    @application.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, _exception: RequestValidationError):
        return _error(422, "invalid_request")

    @application.exception_handler(HTTPException)
    async def http_failure(_request: Request, exception: HTTPException):
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
        return _error(503, "service_unavailable")

    @application.post(
        "/v1/interactions",
        response_model=DecisionResponse,
        response_model_exclude_none=True,
    )
    def interact(body: InteractionRequest, request: Request):
        interaction = Interaction.create(body.target_id, body.content)
        outcome = request.app.state.service.evaluate(interaction)
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
