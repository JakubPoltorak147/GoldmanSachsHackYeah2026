from dataclasses import FrozenInstanceError

import pytest

from app.control_layer.controls import EmailAddressControl
from app.control_layer.domain import (
    Action,
    EvaluationError,
    Finding,
    Interaction,
    PolicyError,
    Span,
)
from app.control_layer.policy import (
    ControlPolicy,
    Policy,
    decide,
    forwarded_interaction,
    load_policy,
    validate_findings,
)


def config(action="REDACT", enabled="true", findings=True):
    return (
        "version: 1\npolicy_id: test_policy\ncontrols:\n  email-address:\n"
        f"    enabled: {enabled}\n"
        + (f"    findings:\n      pii.email: {action}\n" if findings else "")
    )


def load(tmp_path, text):
    path = tmp_path / "policy.yaml"
    path.write_text(text)
    return load_policy(path)


@pytest.mark.parametrize("action", list(Action))
def test_same_finding_three_mappings(tmp_path, action):
    policy = load(tmp_path, config(action))
    interaction = Interaction.create("local-echo", "Hi <a@example.com>!")
    findings = EmailAddressControl().evaluate(interaction)
    decision = decide(interaction, findings, ("email-address",), policy)
    assert decision.action == action
    assert decision.resolutions[0].rule_id == "email-address:pii.email"
    assert decision.resolutions[0].action == action
    forwarded = forwarded_interaction(interaction, decision)
    if action == Action.BLOCK:
        assert forwarded is None
    elif action == Action.REDACT:
        assert forwarded.content == "Hi <[REDACTED]>!"
        assert forwarded.id == interaction.id
    else:
        assert forwarded is interaction


def test_no_findings_and_disabled(tmp_path):
    for enabled in ("true", "false"):
        policy = load(tmp_path, config(enabled=enabled, findings=enabled == "true"))
        evaluated = ("email-address",) if enabled == "true" else ()
        decision = decide(
            Interaction.create("local-echo", "clean"), (), evaluated, policy
        )
        assert decision.action == Action.ALLOW and decision.reason_code == "no_findings"


def test_immutable_policy_and_stable_digest(tmp_path):
    policy = load(tmp_path, config())
    assert policy.digest == load(tmp_path, "# comment\n" + config()).digest
    assert policy.digest != load(tmp_path, config("BLOCK")).digest
    with pytest.raises(FrozenInstanceError):
        policy.policy_id = "changed"
    assert isinstance(policy.controls, tuple) and isinstance(
        policy.controls[0].mappings, tuple
    )


@pytest.mark.parametrize(
    "text",
    [
        "[",
        "",
        "[]",
        config().replace("version: 1", "version: true"),
        config().replace("version: 1", "version: 2"),
        config().replace("version: 1", "version: 1\nversion: 1"),
        config() + "unknown: secret@example.com\n",
        config().replace("email-address:", "unknown-control:"),
        config().replace("pii.email:", "test.only:"),
        config().replace(
            "pii.email: REDACT", "pii.email: REDACT\n      pii.email: BLOCK"
        ),
        config("allow"),
        config("NOPE"),
        config("[ALLOW]"),
        config(enabled="1"),
        config(enabled="null"),
        config(findings=False),
        config(enabled="false", action="NOPE"),
        config().replace("test_policy", '"secret@example.com"'),
        config().replace("findings:", "findings: null #"),
        config().replace("enabled: true", "enabled: true\n    unexpected: false"),
        "!!python/object:builtins.str {}",
        "? [unhashable]\n: 1",
    ],
)
def test_invalid_policy_rejected_without_details(tmp_path, text):
    with pytest.raises(PolicyError, match="^invalid_policy$"):
        load(tmp_path, text)


def test_unreadable_policy(tmp_path):
    with pytest.raises(PolicyError):
        load_policy(tmp_path / "missing")


def fixture_decision(actions, spans):
    interaction = Interaction.create("local-echo", "abcdefghij")
    codes = tuple(f"test.{i}" for i in range(len(actions)))
    policy = Policy(
        "test",
        "digest",
        (ControlPolicy("test-control", True, tuple(zip(codes, actions, strict=True))),),
    )
    findings = tuple(
        Finding("test-control", code, span)
        for code, span in zip(codes, spans, strict=True)
    )
    decision = decide(
        interaction,
        findings,
        ("test-control",),
        policy,
        {"test-control": frozenset(codes)},
    )
    return interaction, decision


def test_precedence():
    interaction, decision = fixture_decision(
        [Action.REDACT, Action.BLOCK, Action.ALLOW],
        [Span(0, 1), Span(2, 3), Span(4, 5)],
    )
    assert decision.action == Action.BLOCK
    assert forwarded_interaction(interaction, decision) is None


def test_selective_redaction_original_offsets_overlap_and_adjacency():
    interaction, decision = fixture_decision(
        [Action.ALLOW, Action.REDACT, Action.REDACT, Action.REDACT, Action.REDACT],
        [Span(0, 1), Span(2, 5), Span(4, 6), Span(6, 7), Span(9, 10)],
    )
    assert (
        forwarded_interaction(interaction, decision).content
        == "ab[REDACTED]hi[REDACTED]"
    )
    assert interaction.content == "abcdefghij"


@pytest.mark.parametrize(
    "span",
    [
        None,
        Span(-1, 2),
        Span(1, 1),
        Span(2, 1),
        Span(0, 11),
        Span(True, 2),
        Span(0, 1.0),
    ],
)
def test_invalid_redaction_spans_fail_closed(span):
    with pytest.raises(EvaluationError):
        fixture_decision([Action.REDACT], [span])


@pytest.mark.parametrize(
    "findings",
    [
        [],
        ("raw@example.com",),
        (Finding("spoofed", "pii.email", Span(0, 1)),),
        (Finding("email-address", "unknown", Span(0, 1)),),
        (Finding("email-address", "pii.email", None),),
        (Finding("email-address", "pii.email", Span(0, 99)),),
    ],
)
def test_invalid_control_contract(findings):
    with pytest.raises(EvaluationError):
        validate_findings(
            findings,
            "email-address",
            "text",
            {"email-address": frozenset({"pii.email"})},
        )


def test_inconsistent_resolution(tmp_path):
    interaction = Interaction.create("local-echo", "a@example.com")
    findings = EmailAddressControl().evaluate(interaction)
    for policy, evaluated in [
        (load(tmp_path, config()), ()),
        (
            Policy("test", "digest", (ControlPolicy("email-address", True, ()),)),
            ("email-address",),
        ),
        (load(tmp_path, config(enabled="false")), ()),
    ]:
        with pytest.raises(EvaluationError):
            decide(interaction, findings, evaluated, policy)
