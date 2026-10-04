"""Deterministic usage budgets: window counters emit fixed spanless findings.

The control owns counters, never actions; central policy maps its findings.
"""

import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

from app.control_layer.domain import EvaluationError, Finding, Interaction, PolicyError

USAGE_ID = "usage-budget"
REQUEST_LIMIT = "budget.request_limit"
TOKEN_LIMIT = "budget.token_limit"
REQUEST_SIZE = "budget.request_size"
CODES = (REQUEST_LIMIT, TOKEN_LIMIT, REQUEST_SIZE)
LIMIT_BOUNDS = (
    ("window_seconds", 1, 86_400),
    ("max_requests", 1, 1_000_000),
    ("max_estimated_tokens", 1, 100_000_000),
    ("max_request_tokens", 1, 4096),
)


def estimate_tokens(content: str) -> int:
    """Documented heuristic: one token per four Unicode scalars, rounded up."""
    return -(-len(content) // 4)


@dataclass(frozen=True)
class UsageLimits:
    window_seconds: int
    max_requests: int
    max_estimated_tokens: int
    max_request_tokens: int

    def __post_init__(self):
        for name, low, high in LIMIT_BOUNDS:
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError("invalid_usage_limits")

    def as_pairs(self) -> tuple[tuple[str, int], ...]:
        return tuple((name, getattr(self, name)) for name, _, _ in LIMIT_BOUNDS)


def parse_limits(raw: object) -> UsageLimits:
    """Strict policy parsing: exactly the four integer keys, nothing else."""
    try:
        if type(raw) is not dict or set(raw) != {n for n, _, _ in LIMIT_BOUNDS}:
            raise ValueError()
        return UsageLimits(**raw)
    except Exception:
        raise PolicyError() from None


@dataclass(frozen=True)
class UsageSnapshot:
    window_seconds: int
    resets_in_seconds: int
    requests_used: int
    tokens_used: int
    breaches: tuple[tuple[str, int], ...]


class UsageMeter:
    """Lock-protected fixed-window counters with an injectable monotonic clock."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        if not callable(clock):
            raise ValueError("invalid_usage_clock")
        self.clock = clock
        self._lock = Lock()
        self._start: float | None = None
        self._requests = 0
        self._tokens = 0
        self._breaches = dict.fromkeys(CODES, 0)

    def fresh(self) -> "UsageMeter":
        """Independent counters for one bound policy, keeping the same clock."""
        return UsageMeter(self.clock)

    def _expired(self, now: float, limits: UsageLimits) -> bool:
        return self._start is None or now - self._start >= limits.window_seconds

    def charge(self, estimate: int, limits: UsageLimits) -> tuple[str, ...]:
        """Atomically check, then charge, every attempt that reaches the control."""
        with self._lock:
            now = self.clock()
            if self._expired(now, limits):
                self._start, self._requests, self._tokens = now, 0, 0
            codes = tuple(
                code
                for code, exceeded in (
                    (REQUEST_LIMIT, self._requests + 1 > limits.max_requests),
                    (
                        TOKEN_LIMIT,
                        self._tokens + estimate > limits.max_estimated_tokens,
                    ),
                    (REQUEST_SIZE, estimate > limits.max_request_tokens),
                )
                if exceeded
            )
            self._requests += 1
            self._tokens += estimate
            for code in codes:
                self._breaches[code] += 1
            return codes

    def snapshot(self, limits: UsageLimits) -> UsageSnapshot:
        """Read without charging or resetting; an elapsed window reads as empty."""
        with self._lock:
            now = self.clock()
            breaches = tuple(self._breaches.items())
            if self._expired(now, limits):
                return UsageSnapshot(
                    limits.window_seconds, limits.window_seconds, 0, 0, breaches
                )
            remaining = limits.window_seconds - (now - self._start)
            return UsageSnapshot(
                limits.window_seconds,
                max(0, math.ceil(remaining)),
                self._requests,
                self._tokens,
                breaches,
            )


@dataclass(frozen=True)
class UsageBudgetControl:
    meter: UsageMeter | None = None
    limits: UsageLimits | None = None
    id = USAGE_ID

    def evaluate(self, interaction: Interaction) -> tuple[Finding, ...]:
        try:
            if (
                type(self.meter) is not UsageMeter
                or type(self.limits) is not UsageLimits
            ):
                raise ValueError()
            content = interaction.content
            if type(content) is not str:
                raise ValueError()
            codes = self.meter.charge(estimate_tokens(content), self.limits)
            return tuple(Finding(USAGE_ID, code) for code in codes)
        except Exception:
            raise EvaluationError() from None
