"""Read-only, closed HTTP projections over the typed reporting store."""

import re
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict

from app.control_layer.domain import Action
from app.control_layer.reporting import (
    EventFilter,
    EventView,
    InvocationStatus,
    ReportingError,
    Summary,
    TimingSummary,
)


class ClosedDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class WindowDTO(ClosedDTO):
    from_time: datetime
    to_time: datetime


class TimingDTO(ClosedDTO):
    samples: int
    sum_ms: float
    min_ms: float | None
    max_ms: float | None
    mean_ms: float | None


class FindingSummaryDTO(ClosedDTO):
    control_id: str
    code: str
    occurrences: int
    affected_interactions: int


class SummaryDTO(ClosedDTO):
    interaction_total: int
    actions: dict[Action, int]
    operational_failure_total: int
    invocations: dict[InvocationStatus, int]
    findings: list[FindingSummaryDTO]
    evaluation: TimingDTO
    semantic: TimingDTO
    invocation: TimingDTO
    total: TimingDTO


class SummaryResponse(ClosedDTO):
    api_version: Literal[1] = 1
    window: WindowDTO
    generated_at: datetime
    reporting_health: Literal["healthy", "reporting_write_failed"]
    overall: SummaryDTO


class FindingDTO(ClosedDTO):
    control_id: str
    code: str
    action: Action
    count: int


class EventDTO(ClosedDTO):
    interaction_id: UUID
    timestamp: datetime
    event_type: Literal["decision", "operational_failure"]
    target_id: str
    model_id: str | None
    policy_digest: str
    action: Action | None
    reason_code: Literal["policy_resolved", "no_findings"] | None
    error_code: Literal["evaluation_failed"] | None
    forwarding_eligible: bool
    evaluation_duration_ms: float
    evaluated_controls: list[str]
    control_status: list[tuple[str, bool]]
    findings: list[FindingDTO]
    semantic_duration_ms: float | None
    semantic_model_id: str | None
    semantic_status: Literal["succeeded", "failed"] | None


class CompletionDTO(ClosedDTO):
    interaction_id: UUID
    completed_at: datetime
    status: Literal[InvocationStatus.SUCCEEDED, InvocationStatus.FAILED]
    invocation_duration_ms: float
    total_duration_ms: float
    error_code: Literal["target_failed"] | None


class EventViewDTO(ClosedDTO):
    sequence: int
    schema_version: Literal[2]
    event: EventDTO
    invocation_status: InvocationStatus
    completion: CompletionDTO | None


class EventsResponse(ClosedDTO):
    api_version: Literal[1] = 1
    window: WindowDTO
    items: list[EventViewDTO]
    next_before_sequence: int | None


class DetailResponse(ClosedDTO):
    api_version: Literal[1] = 1
    item: EventViewDTO


class ReportingErrorDTO(ClosedDTO):
    error_code: Literal[
        "invalid_reporting_query",
        "not_found",
        "reporting_unavailable",
        "method_not_allowed",
    ]


def reporting_error(status: int, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=ReportingErrorDTO(error_code=code).model_dump(mode="json"),
        headers={"Cache-Control": "no-store"},
    )


class ReportingRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def closed_errors(request: Request):
            try:
                return await handler(request)
            except ReportingError as error:
                if str(error) == "invalid_reporting_query":
                    return reporting_error(422, "invalid_reporting_query")
                return reporting_error(503, "reporting_unavailable")
            except Exception:
                # Never serialize query values, paths, provider text or causes.
                return reporting_error(503, "reporting_unavailable")

        return closed_errors


router = APIRouter(
    prefix="/v1/reporting",
    route_class=ReportingRoute,
    responses={status: {"model": ReportingErrorDTO} for status in (422, 404, 405, 503)},
)
_FILTER_KEYS = {"from_time", "to_time", "action", "target_id", "invocation_status"}
_UTC_TEXT = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|\+00:00)"
)


def _parameters(request: Request, allowed: set[str]) -> dict[str, str]:
    pairs = request.query_params.multi_items()
    if any(key not in allowed for key, _ in pairs) or len({k for k, _ in pairs}) != len(
        pairs
    ):
        raise ReportingError("invalid_reporting_query")
    return dict(pairs)


def _integer(value: str, maximum: int) -> int:
    if not re.fullmatch(r"[1-9][0-9]{0,18}", value) or int(value) > maximum:
        raise ReportingError("invalid_reporting_query")
    return int(value)


def _filters(params: dict[str, str]) -> EventFilter:
    try:
        lower, upper = params.get("from_time"), params.get("to_time")
        if lower is None and upper is None:
            to_time = datetime.now(UTC)
            from_time = to_time - timedelta(days=1)
        else:
            if (
                lower is None
                or upper is None
                or not all(_UTC_TEXT.fullmatch(v) for v in (lower, upper))
            ):
                raise ValueError()
            from_time, to_time = (
                datetime.fromisoformat(lower),
                datetime.fromisoformat(upper),
            )
        if to_time - from_time > timedelta(days=31):
            raise ValueError()
        return EventFilter(
            from_time,
            to_time,
            Action(params["action"]) if "action" in params else None,
            params.get("target_id"),
            InvocationStatus(params["invocation_status"])
            if "invocation_status" in params
            else None,
        )
    except Exception:
        raise ReportingError("invalid_reporting_query") from None


def _window(filters: EventFilter) -> WindowDTO:
    return WindowDTO(from_time=filters.from_time, to_time=filters.to_time)


def _timing(value: TimingSummary) -> TimingDTO:
    return TimingDTO(
        samples=value.samples,
        sum_ms=value.sum_ms,
        min_ms=value.min_ms,
        max_ms=value.max_ms,
        mean_ms=value.mean_ms,
    )


def _summary(value: Summary) -> SummaryDTO:
    return SummaryDTO(
        interaction_total=value.interaction_total,
        actions=dict(value.actions),
        operational_failure_total=value.operational_failure_total,
        invocations=dict(value.invocations),
        findings=[
            FindingSummaryDTO(
                control_id=f.control_id,
                code=f.code,
                occurrences=f.occurrences,
                affected_interactions=f.affected_interactions,
            )
            for f in value.findings
        ],
        evaluation=_timing(value.evaluation),
        semantic=_timing(value.semantic),
        invocation=_timing(value.invocation),
        total=_timing(value.total),
    )


def _view(value: EventView) -> EventViewDTO:
    event, completion = value.event, value.completion
    return EventViewDTO(
        sequence=value.sequence,
        schema_version=value.schema_version,
        invocation_status=value.invocation_status,
        event=EventDTO(
            interaction_id=event.interaction_id,
            timestamp=event.timestamp,
            event_type=event.event_type,
            target_id=event.target_id,
            model_id=event.model_id,
            policy_digest=event.policy_digest,
            action=event.action,
            reason_code=event.reason_code,
            error_code=event.error_code,
            forwarding_eligible=event.forwarding_eligible,
            evaluation_duration_ms=event.evaluation_duration_ms,
            evaluated_controls=list(event.evaluated_controls),
            control_status=list(event.control_status),
            findings=[
                FindingDTO(
                    control_id=f.control_id, code=f.code, action=f.action, count=f.count
                )
                for f in event.findings
            ],
            semantic_duration_ms=event.semantic_duration_ms,
            semantic_model_id=event.semantic_model_id,
            semantic_status=event.semantic_status,
        ),
        completion=CompletionDTO(
            interaction_id=completion.interaction_id,
            completed_at=completion.completed_at,
            status=completion.status,
            invocation_duration_ms=completion.invocation_duration_ms,
            total_duration_ms=completion.total_duration_ms,
            error_code=completion.error_code,
        )
        if completion
        else None,
    )


@router.get("/summary", response_model=SummaryResponse)
def summary(request: Request, response: Response):
    filters = _filters(_parameters(request, _FILTER_KEYS))
    store = request.app.state.reporting
    result = store.summarize(filters)
    response.headers["Cache-Control"] = "no-store"
    return SummaryResponse(
        window=_window(filters),
        generated_at=datetime.now(UTC),
        reporting_health=store.health,
        overall=_summary(result.overall),
    )


@router.get("/events", response_model=EventsResponse)
def events(request: Request, response: Response):
    params = _parameters(request, _FILTER_KEYS | {"limit", "before_sequence"})
    filters = _filters(params)
    limit = _integer(params.get("limit", "50"), 100)
    cursor = (
        _integer(params["before_sequence"], 2**63 - 1)
        if "before_sequence" in params
        else None
    )
    result = request.app.state.reporting.list_recent_events(
        filters, limit=limit, before_sequence=cursor
    )
    response.headers["Cache-Control"] = "no-store"
    return EventsResponse(
        window=_window(filters),
        items=[_view(item) for item in result],
        next_before_sequence=result[-1].sequence if len(result) == limit else None,
    )


@router.get("/events/{interaction_id}", response_model=DetailResponse)
def detail(interaction_id: str, request: Request, response: Response):
    _parameters(request, set())
    try:
        if not re.fullmatch(
            r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", interaction_id
        ):
            raise ValueError()
        identity = UUID(interaction_id)
    except ValueError:
        raise ReportingError("invalid_reporting_query") from None
    item = request.app.state.reporting.get_event(identity)
    if item is None:
        return reporting_error(404, "not_found")
    response.headers["Cache-Control"] = "no-store"
    return DetailResponse(item=_view(item))
