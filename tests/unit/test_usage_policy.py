"""Strict `limits` policy parsing, digest, startup binding and migration."""

from pathlib import Path

import pytest
import yaml

from app.control_layer.composition import (
    bind_policy,
    bind_usage_policy,
    default_controls,
)
from app.control_layer.domain import Interaction, PolicyError
from app.control_layer.policy import load_policy
from app.control_layer.usage_control import UsageBudgetControl, UsageMeter

CONFIG = Path(__file__).resolve().parents[2] / "config"
DEFAULT = CONFIG / "policy.yaml"
LIMITS = {
    "window_seconds": 60,
    "max_requests": 5,
    "max_estimated_tokens": 500,
    "max_request_tokens": 50,
}


def write(tmp_path, mutate=None, source=DEFAULT):
    raw = yaml.safe_load(source.read_text())
    if mutate:
        mutate(raw)
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(raw))
    return path


def usage(raw):
    return raw["controls"]["usage-budget"]


def test_shipped_policies_bind_usage_budget_limits(tmp_path):
    for name in (
        "policy.yaml",
        "policy-semantic-demo.yaml",
        "policy-evaluation.yaml",
        "policy-evaluation-offline.yaml",
    ):
        bound = bind_policy(load_policy(CONFIG / name, default_controls()))
        entry = next(e for e in bound.entries if e.control_id == "usage-budget")
        assert entry.enabled and entry.limits is not None
        assert type(entry.registration.evaluator.meter) is UsageMeter
        assert entry.registration.evaluator.limits == entry.limits


def test_evaluation_profile_limits_are_small_and_documented():
    bound = load_policy(CONFIG / "policy-evaluation.yaml", default_controls())
    entry = next(e for e in bound.entries if e.control_id == "usage-budget")
    assert entry.limits.as_pairs() == (
        ("window_seconds", 60),
        ("max_requests", 20),
        ("max_estimated_tokens", 2000),
        ("max_request_tokens", 400),
    )


def test_limits_change_the_digest_and_are_part_of_it(tmp_path):
    base = load_policy(write(tmp_path), default_controls()).digest
    changed = load_policy(
        write(tmp_path, lambda r: usage(r)["limits"].update(max_requests=119)),
        default_controls(),
    ).digest
    assert base != changed
    assert base == load_policy(write(tmp_path), default_controls()).digest


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: usage(r).pop("limits"),
        lambda r: usage(r)["limits"].update(extra=1),
        lambda r: usage(r)["limits"].pop("max_requests"),
        lambda r: usage(r)["limits"].update(max_requests=True),
        lambda r: usage(r)["limits"].update(max_requests=1.5),
        lambda r: usage(r)["limits"].update(max_requests="5"),
        lambda r: usage(r)["limits"].update(max_requests=0),
        lambda r: usage(r)["limits"].update(window_seconds=86401),
        lambda r: usage(r)["limits"].update(max_request_tokens=4097),
        lambda r: usage(r)["limits"].update(max_estimated_tokens=100_000_001),
        lambda r: usage(r).update(limits=[1, 2, 3, 4]),
        lambda r: usage(r).update(limits=None),
        lambda r: r["controls"]["email-address"].update(limits=LIMITS),
        lambda r: r["controls"]["semantic-security"].update(limits=LIMITS),
        lambda r: usage(r).update(threshold=0.5),
        lambda r: usage(r)["findings"].pop("budget.token_limit"),
        lambda r: usage(r)["findings"].update({"budget.token_limit": "REDACT"}),
        lambda r: usage(r)["findings"].update({"budget.unknown": "BLOCK"}),
    ],
)
def test_invalid_limits_fail_closed(tmp_path, mutate):
    with pytest.raises(PolicyError):
        load_policy(write(tmp_path, mutate), default_controls())


def test_budget_redact_rejected_even_when_disabled(tmp_path):
    def mutate(raw):
        usage(raw)["enabled"] = False
        usage(raw)["findings"]["budget.request_size"] = "REDACT"

    with pytest.raises(PolicyError):
        load_policy(write(tmp_path, mutate), default_controls())


def test_disabled_entry_may_omit_limits_but_supplied_limits_are_validated(tmp_path):
    def omit(raw):
        raw["controls"]["usage-budget"] = {"enabled": False}

    bound = load_policy(write(tmp_path, omit), default_controls())
    entry = next(e for e in bound.entries if e.control_id == "usage-budget")
    assert not entry.enabled and entry.limits is None
    assert bind_usage_policy(bound) is not bound

    def invalid(raw):
        usage(raw)["enabled"] = False
        usage(raw)["limits"]["max_requests"] = 0

    with pytest.raises(PolicyError):
        load_policy(write(tmp_path, invalid), default_controls())


def test_policy_without_usage_entry_requires_explicit_migration(tmp_path):
    with pytest.raises(PolicyError):
        load_policy(
            write(tmp_path, lambda r: r["controls"].pop("usage-budget")),
            default_controls(),
        )


def test_shadow_mapping_is_accepted(tmp_path):
    def mutate(raw):
        for code in usage(raw)["findings"]:
            usage(raw)["findings"][code] = "ALLOW"

    bound = load_policy(write(tmp_path, mutate), default_controls())
    entry = next(e for e in bound.entries if e.control_id == "usage-budget")
    assert {action.value for _, action in entry.mappings} == {"ALLOW"}


def test_binding_gives_each_policy_independent_counters(tmp_path):
    registry = default_controls()
    first = bind_policy(load_policy(write(tmp_path), registry))
    second = bind_policy(load_policy(write(tmp_path), registry))

    def evaluator(bound):
        return next(
            e.registration.evaluator
            for e in bound.entries
            if e.control_id == "usage-budget"
        )

    interaction = Interaction.create("local-echo", "hello")
    evaluator(first).evaluate(interaction)
    assert evaluator(first).meter is not evaluator(second).meter
    assert evaluator(second).meter.snapshot(evaluator(second).limits).requests_used == 0
    # the registry's own prototype stays unbound and fails closed
    unbound = registry.resolve("usage-budget").evaluator
    assert type(unbound) is UsageBudgetControl and unbound.limits is None


def test_binding_rejects_tampered_registration(tmp_path):
    bound = load_policy(write(tmp_path), default_controls())
    forged = type("Other", (), {"id": "usage-budget", "evaluate": lambda s, i: ()})()
    entries = tuple(
        type(e)(
            type(e.registration)(e.registration.definition, forged),
            e.enabled,
            e.mappings,
            e.semantic_threshold,
            e.limits,
        )
        if e.control_id == "usage-budget"
        else e
        for e in bound.entries
    )
    from dataclasses import replace

    with pytest.raises(PolicyError):
        bind_usage_policy(replace(bound, entries=entries))
