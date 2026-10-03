import pytest

from app.control_layer.domain import EvaluationError, Finding, Span
from app.control_layer.policy import validate_findings
from app.control_layer.registry import (
    ControlDefinition,
    ControlRegistration,
    FindingDefinition,
)


class Empty:
    def evaluate(self, interaction):
        return ()


def producer(required=True, redact=True):
    return ControlRegistration(
        ControlDefinition(
            "actual", [FindingDefinition("actual.code", required, redact)]
        ),
        Empty(),
    )


@pytest.mark.parametrize(
    "output",
    [
        [],
        None,
        ("secret",),
        (Finding("other", "actual.code", Span(0, 1)),),
        (Finding("actual", "other.code", Span(0, 1)),),
        (Finding(1, "actual.code", Span(0, 1)),),
        (Finding("actual", 1, Span(0, 1)),),
        (Finding("actual", "actual.code"),),
    ],
)
def test_malformed_or_forged_output(output):
    with pytest.raises(EvaluationError, match="^evaluation_failed$"):
        validate_findings(output, producer(), "text")


@pytest.mark.parametrize(
    "span",
    [
        Span(True, 2),
        Span(0, False),
        Span(-1, 1),
        Span(0, 5),
        Span(1, 1),
        Span(2, 1),
        Span(0.0, 1),
        (0, 1),
    ],
)
@pytest.mark.parametrize("required", [True, False])
def test_every_supplied_span_is_strict(span, required):
    with pytest.raises(EvaluationError):
        validate_findings(
            (Finding("actual", "actual.code", span),),
            producer(required, required),
            "text",
        )


def test_spanless_non_redactable_and_registration_owned_identity():
    registration = producer(False, False)
    original = Finding("actual", "actual.code")
    validated = validate_findings((original,), registration, "text")
    assert validated == (original,)
    assert validated[0] is not original
    assert validated[0].control_id is registration.definition.id
    assert validate_findings((), registration, "text") == ()
