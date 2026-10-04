"""Closed, content-free projection of the bound usage budget."""

from pydantic import BaseModel, ConfigDict

from app.control_layer.policy import BoundPolicy
from app.control_layer.usage_control import (
    CODES,
    USAGE_ID,
    UsageBudgetControl,
    UsageMeter,
)


class _Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Counter(_Closed):
    used: int
    limit: int


class Breaches(_Closed):
    request_limit: int
    token_limit: int
    request_size: int


class UsageResponse(_Closed):
    enabled: bool
    window_seconds: int | None = None
    resets_in_seconds: int | None = None
    requests: Counter | None = None
    estimated_tokens: Counter | None = None
    max_request_tokens: int | None = None
    breaches: Breaches | None = None


def usage_response(policy: BoundPolicy) -> UsageResponse:
    """Read the bound meter without charging it; absent or disabled is not an error."""
    for entry in policy.entries:
        if entry.control_id != USAGE_ID:
            continue
        evaluator = entry.registration.evaluator
        if (
            not entry.enabled
            or type(evaluator) is not UsageBudgetControl
            or type(evaluator.meter) is not UsageMeter
            or evaluator.limits is None
        ):
            break
        limits, snapshot = evaluator.limits, evaluator.meter.snapshot(evaluator.limits)
        breaches = dict(snapshot.breaches)
        return UsageResponse(
            enabled=True,
            window_seconds=snapshot.window_seconds,
            resets_in_seconds=snapshot.resets_in_seconds,
            requests=Counter(used=snapshot.requests_used, limit=limits.max_requests),
            estimated_tokens=Counter(
                used=snapshot.tokens_used, limit=limits.max_estimated_tokens
            ),
            max_request_tokens=limits.max_request_tokens,
            breaches=Breaches(
                request_limit=breaches[CODES[0]],
                token_limit=breaches[CODES[1]],
                request_size=breaches[CODES[2]],
            ),
        )
    return UsageResponse(enabled=False)
