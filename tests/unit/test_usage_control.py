"""Usage-budget control: allowed, boundary, over-limit, reset, concurrency."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from app.control_layer.domain import EvaluationError, Interaction, PolicyError
from app.control_layer.usage_control import (
    CODES,
    REQUEST_LIMIT,
    REQUEST_SIZE,
    TOKEN_LIMIT,
    UsageBudgetControl,
    UsageLimits,
    UsageMeter,
    estimate_tokens,
    parse_limits,
)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def limits(**overrides):
    values = {
        "window_seconds": 60,
        "max_requests": 3,
        "max_estimated_tokens": 100,
        "max_request_tokens": 20,
    }
    values.update(overrides)
    return UsageLimits(**values)


def control(clock=None, **overrides):
    return UsageBudgetControl(UsageMeter(clock or Clock()), limits(**overrides))


def codes(evaluator, text="hello"):
    return [f.code for f in evaluator.evaluate(Interaction.create("local-echo", text))]


@pytest.mark.parametrize(
    ("text", "tokens"),
    [("a", 1), ("abcd", 1), ("abcde", 2), ("x" * 16384, 4096), ("🙂" * 5, 2)],
)
def test_estimate_counts_unicode_scalars_once(text, tokens):
    assert estimate_tokens(text) == tokens


def test_within_budget_has_no_findings():
    assert codes(control()) == []


def test_request_limit_exact_boundary():
    evaluator = control(max_requests=3)
    assert [codes(evaluator) for _ in range(3)] == [[], [], []]
    assert codes(evaluator) == [REQUEST_LIMIT]


def test_oversized_request_is_flagged_regardless_of_window():
    evaluator = control(max_request_tokens=20)
    assert codes(evaluator, "x" * 80) == []
    assert codes(evaluator, "x" * 81) == [REQUEST_SIZE]


def test_token_window_exhaustion_still_charges():
    evaluator = control(max_estimated_tokens=10, max_request_tokens=10)
    assert codes(evaluator, "x" * 24) == []  # 6 tokens
    assert codes(evaluator, "x" * 24) == [TOKEN_LIMIT]  # 12 > 10, charged anyway
    assert codes(evaluator, "x") == [TOKEN_LIMIT]  # 13 > 10


def test_multiple_breaches_follow_catalogue_order():
    evaluator = control(max_requests=1, max_estimated_tokens=5, max_request_tokens=5)
    assert codes(evaluator, "x") == []
    assert codes(evaluator, "x" * 40) == [REQUEST_LIMIT, TOKEN_LIMIT, REQUEST_SIZE]


def test_window_resets_on_injected_clock():
    clock = Clock()
    evaluator = control(clock, max_requests=1)
    assert codes(evaluator) == []
    assert codes(evaluator) == [REQUEST_LIMIT]
    clock.now += 59.9
    assert codes(evaluator) == [REQUEST_LIMIT]
    clock.now += 0.1
    assert codes(evaluator) == []


def test_snapshot_reads_without_charging_and_reports_reset():
    clock = Clock()
    meter = UsageMeter(clock)
    configured = limits()
    empty = meter.snapshot(configured)
    assert (empty.requests_used, empty.tokens_used, empty.resets_in_seconds) == (
        0,
        0,
        60,
    )
    evaluator = UsageBudgetControl(meter, configured)
    codes(evaluator, "x" * 8)
    clock.now += 10.5
    first = meter.snapshot(configured)
    assert meter.snapshot(configured) == first
    assert (first.requests_used, first.tokens_used) == (1, 2)
    assert first.resets_in_seconds == 50
    clock.now += 100
    expired = meter.snapshot(configured)
    assert (expired.requests_used, expired.tokens_used) == (0, 0)
    assert dict(expired.breaches) == dict.fromkeys(CODES, 0)


def test_breach_counters_are_lifetime():
    clock = Clock()
    evaluator = control(clock, max_requests=1)
    codes(evaluator)
    codes(evaluator)
    clock.now += 1000
    codes(evaluator)
    codes(evaluator)
    breaches = dict(evaluator.meter.snapshot(evaluator.limits).breaches)
    assert breaches[REQUEST_LIMIT] == 2


def test_concurrent_burst_never_over_admits():
    evaluator = control(max_requests=25, max_estimated_tokens=10**6)
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda _: codes(evaluator), range(200)))
    assert sum(1 for r in results if r == []) == 25
    assert sum(1 for r in results if r == [REQUEST_LIMIT]) == 175


def test_unbound_control_fails_closed():
    with pytest.raises(EvaluationError):
        UsageBudgetControl().evaluate(Interaction.create("local-echo", "x"))


def test_fresh_meters_are_independent_and_share_clock():
    clock = Clock()
    meter = UsageMeter(clock)
    other = meter.fresh()
    UsageBudgetControl(meter, limits()).evaluate(Interaction.create("local-echo", "x"))
    assert other.snapshot(limits()).requests_used == 0
    assert other.clock is clock


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"window_seconds": 60},
        {
            "window_seconds": 60,
            "max_requests": 1,
            "max_estimated_tokens": 1,
            "max_request_tokens": 1,
            "extra": 1,
        },
        {
            "window_seconds": True,
            "max_requests": 1,
            "max_estimated_tokens": 1,
            "max_request_tokens": 1,
        },
        {
            "window_seconds": 1.5,
            "max_requests": 1,
            "max_estimated_tokens": 1,
            "max_request_tokens": 1,
        },
        {
            "window_seconds": 0,
            "max_requests": 1,
            "max_estimated_tokens": 1,
            "max_request_tokens": 1,
        },
        {
            "window_seconds": 60,
            "max_requests": 1,
            "max_estimated_tokens": 1,
            "max_request_tokens": 4097,
        },
        "limits",
        None,
    ],
)
def test_parse_limits_rejects_invalid_values(bad):
    with pytest.raises(PolicyError):
        parse_limits(bad)


def test_parse_limits_accepts_exact_bounds():
    parsed = parse_limits(
        {
            "window_seconds": 86400,
            "max_requests": 1_000_000,
            "max_estimated_tokens": 100_000_000,
            "max_request_tokens": 4096,
        }
    )
    assert parsed.as_pairs()[-1] == ("max_request_tokens", 4096)
