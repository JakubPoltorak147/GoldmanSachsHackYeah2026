from dataclasses import FrozenInstanceError

import pytest
import yaml

from app.control_layer.composition import default_controls
from app.control_layer.domain import PolicyError
from app.control_layer.policy import load_policy
from app.control_layer.registry import (
    ControlDefinition,
    ControlRegistration,
    ControlRegistry,
    FindingDefinition,
)


class Empty:
    def evaluate(self, interaction):
        return ()


def registry():
    return ControlRegistry(
        [
            ControlRegistration(
                ControlDefinition(
                    "second",
                    [
                        FindingDefinition("second.one", False, False),
                        FindingDefinition("second.two", True, True),
                    ],
                ),
                Empty(),
            ),
            default_controls().registrations[0],
        ]
    )


def config():
    return {
        "version": 1,
        "policy_id": "test",
        "controls": {
            "email-address": {"enabled": True, "findings": {"pii.email": "REDACT"}},
            "second": {
                "enabled": True,
                "findings": {"second.one": "BLOCK", "second.two": "ALLOW"},
            },
        },
    }


def load(tmp_path, raw, controls=None):
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False))
    return load_policy(path, registry() if controls is None else controls)


def test_complete_bound_policy_retains_exact_registrations(tmp_path):
    controls = registry()
    bound = load(tmp_path, config(), controls)
    assert tuple(e.registration for e in bound.entries) == controls.registrations
    assert all(
        e.registration is r
        for e, r in zip(bound.entries, controls.registrations, strict=True)
    )
    assert [e.control_id for e in bound.entries] == ["second", "email-address"]
    with pytest.raises(FrozenInstanceError):
        bound.entries = ()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda c: c.pop("second"),
        lambda c: c.update(unknown={"enabled": False}),
        lambda c: c["second"].update(enabled=1),
        lambda c: c["second"].update(extra=True),
        lambda c: c["second"].pop("findings"),
        lambda c: c["second"]["findings"].pop("second.two"),
        lambda c: c["second"]["findings"].update(unknown="ALLOW"),
        lambda c: c["second"]["findings"].update({"second.one": "REDACT"}),
        lambda c: c["second"]["findings"].update({"second.one": True}),
        lambda c: c["second"]["findings"].update({"second.one": "unknown"}),
    ],
)
def test_incomplete_invalid_policy(tmp_path, mutation):
    raw = config()
    mutation(raw["controls"])
    with pytest.raises(PolicyError, match="^invalid_policy$"):
        load(tmp_path, raw)


@pytest.mark.parametrize(
    "findings", [None, {}, {"second.one": "ALLOW"}, {"second.two": "REDACT"}]
)
def test_disabled_omitted_or_subset(tmp_path, findings):
    raw = config()
    raw["controls"]["second"] = {"enabled": False}
    if findings is not None:
        raw["controls"]["second"]["findings"] = findings
    bound = load(tmp_path, raw)
    assert bound.entries[0].enabled is False


def test_unsupported_disabled_redaction(tmp_path):
    raw = config()
    raw["controls"]["second"] = {"enabled": False, "findings": {"second.one": "REDACT"}}
    with pytest.raises(PolicyError):
        load(tmp_path, raw)


def test_existing_digest(tmp_path):
    path = tmp_path / "historical-policy.yaml"
    path.write_text(
        "version: 1\npolicy_id: foundation-default\ncontrols:\n"
        "  email-address:\n    enabled: true\n    findings:\n"
        "      pii.email: REDACT\n"
    )
    assert (
        load_policy(
            path, ControlRegistry((default_controls().registrations[0],))
        ).digest
        == "5416596669594e811989eb6cfba7311737e80922f2fb4c2171837038aa427ec4"
    )


def test_key_order_does_not_change_digest_or_registration_order(tmp_path):
    controls = registry()
    raw = config()
    first = load(tmp_path, raw, controls)
    raw["controls"] = dict(reversed(list(raw["controls"].items())))
    raw["controls"]["second"]["findings"] = dict(
        reversed(list(raw["controls"]["second"]["findings"].items()))
    )
    second = load(tmp_path, raw, controls)
    assert first.digest == second.digest
    assert first.entries == second.entries or [e.control_id for e in first.entries] == [
        e.control_id for e in second.entries
    ]
    for bound in (first, second):
        assert all(
            e.registration is r
            for e, r in zip(bound.entries, controls.registrations, strict=True)
        )


def test_repeated_plan_invocation_and_disabled_skip(tmp_path):
    calls = []

    class Counting:
        def evaluate(self, interaction):
            calls.append(interaction)
            return ()

    controls = registry()
    evaluator = Counting()
    first = controls.registrations[0]
    controls = ControlRegistry(
        [ControlRegistration(first.definition, evaluator), controls.registrations[1]]
    )
    raw = config()
    raw["controls"]["email-address"]["enabled"] = False
    bound = load(tmp_path, raw, controls)
    for interaction in ("first", "second"):
        for entry in bound.entries:
            if entry.enabled:
                assert entry.registration is controls.registrations[0]
                entry.registration.evaluator.evaluate(interaction)
    assert calls == ["first", "second"]
    assert bound.entries[1].enabled is False


@pytest.mark.parametrize("action", ["ALLOW", "REDACT", "BLOCK"])
def test_span_required_under_every_action(tmp_path, action):
    from app.control_layer.domain import EvaluationError, Finding, Interaction
    from app.control_layer.policy import decide

    raw = config()
    raw["controls"]["second"]["findings"]["second.two"] = action
    bound = load(tmp_path, raw)
    with pytest.raises(EvaluationError):
        decide(
            Interaction.create("local-echo", "abcdefghij"),
            (Finding("second", "second.two"),),
            ("second", "email-address"),
            bound,
        )


@pytest.mark.parametrize("action", ["ALLOW", "BLOCK"])
def test_spanless_non_redactable_resolution(tmp_path, action):
    from app.control_layer.domain import Finding, Interaction
    from app.control_layer.policy import decide

    raw = config()
    raw["controls"]["second"]["findings"]["second.one"] = action
    bound = load(tmp_path, raw)
    decision = decide(
        Interaction.create("local-echo", "text"),
        (Finding("second", "second.one"),),
        ("second", "email-address"),
        bound,
    )
    assert decision.action.value == action


def test_cross_control_selective_original_spans_and_precedence(tmp_path):
    from app.control_layer.domain import Action, Finding, Interaction, Span
    from app.control_layer.policy import decide, forwarded_interaction

    raw = config()
    raw["controls"]["second"]["findings"]["second.one"] = "ALLOW"
    raw["controls"]["second"]["findings"]["second.two"] = "REDACT"
    interaction = Interaction.create("local-echo", "abcdefghij")
    findings = (
        Finding("second", "second.one", Span(0, 1)),
        Finding("second", "second.two", Span(2, 5)),
        Finding("email-address", "pii.email", Span(4, 6)),
        Finding("email-address", "pii.email", Span(6, 7)),
    )
    bound = load(tmp_path, raw)
    decision = decide(interaction, findings, ("second", "email-address"), bound)
    forwarded = forwarded_interaction(interaction, decision)
    assert forwarded.content == "ab[REDACTED]hij"
    assert (
        forwarded.id == interaction.id and forwarded.target_id == interaction.target_id
    )
    assert interaction.content == "abcdefghij"
    assert (
        decide(interaction, (), ("second", "email-address"), bound).action
        == Action.ALLOW
    )
    raw["controls"]["second"]["findings"]["second.one"] = "BLOCK"
    decision = decide(
        interaction, findings, ("second", "email-address"), load(tmp_path, raw)
    )
    assert decision.action == Action.BLOCK
    assert forwarded_interaction(interaction, decision) is None
