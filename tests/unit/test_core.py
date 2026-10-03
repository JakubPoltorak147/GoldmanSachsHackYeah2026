from dataclasses import FrozenInstanceError, fields
from uuid import UUID

import pytest

from app.control_layer.domain import (
    Action,
    AuditError,
    Decision,
    EvaluationError,
    Finding,
    FindingResolution,
    Interaction,
    PolicyError,
    Span,
    TargetError,
)


def test_server_owned_identity_and_exact_text():
    first = Interaction.create("local-echo", "  é\n")
    second = Interaction.create("local-echo", first.content)
    assert isinstance(first.id, UUID) and first.id != second.id
    assert first.content == "  é\n"
    assert {f.name for f in fields(first)} == {"id", "target_id", "content"}


@pytest.mark.parametrize(
    "value, field",
    [
        (Interaction.create("local-echo", "test"), "content"),
        (Span(0, 1), "start"),
        (Finding("email-address", "pii.email", Span(0, 1)), "code"),
        (
            FindingResolution(
                Finding("email-address", "pii.email"), "rule", Action.ALLOW
            ),
            "action",
        ),
        (Decision(Action.ALLOW, (), (), "no_findings"), "action"),
    ],
)
def test_immutable_contracts(value, field):
    with pytest.raises(FrozenInstanceError):
        setattr(value, field, None)


def test_findings_have_no_sensitive_value_or_action():
    assert {f.name for f in fields(Finding)} == {"control_id", "code", "span"}
    for error in (EvaluationError(), PolicyError(), AuditError(), TargetError()):
        assert not isinstance(error, (Finding, Decision))
        assert not hasattr(error, "findings")
