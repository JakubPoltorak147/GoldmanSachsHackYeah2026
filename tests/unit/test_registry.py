from dataclasses import FrozenInstanceError

import pytest

from app.control_layer.composition import default_controls
from app.control_layer.registry import (
    ControlDefinition,
    ControlRegistration,
    ControlRegistry,
    FindingDefinition,
)


class Evaluator:
    id = "sample"

    def evaluate(self, interaction):
        return ()


def registration(control_id="sample", code="sample.code"):
    evaluator = Evaluator()
    evaluator.id = control_id
    return ControlRegistration(
        ControlDefinition(control_id, [FindingDefinition(code, True, True)]), evaluator
    )


@pytest.mark.parametrize(
    "identifier", [None, 1, True, "", "A", "a:b", "a/", "a" * 65, "é"]
)
def test_unsafe_control_ids(identifier):
    with pytest.raises(ValueError):
        ControlDefinition(identifier, [FindingDefinition("sample.code", True, True)])


@pytest.mark.parametrize("code", [None, 1, True, "", "A", "a:b", "a/", "a" * 65, "é"])
def test_unsafe_codes(code):
    with pytest.raises(ValueError):
        FindingDefinition(code, True, True)


@pytest.mark.parametrize("required, redaction", [(0, False), (True, 1), (False, True)])
def test_invalid_capabilities(required, redaction):
    with pytest.raises(ValueError):
        FindingDefinition("sample.code", required, redaction)


def test_duplicate_ids_and_global_codes():
    for entries in (
        [registration(), registration()],
        [registration(), registration("second")],
    ):
        with pytest.raises(ValueError):
            ControlRegistry(entries)
    definition = FindingDefinition("sample.code", True, True)
    for findings in ([], [object()], [definition, definition]):
        with pytest.raises(ValueError):
            ControlDefinition("sample", findings)
    with pytest.raises(ValueError):
        ControlRegistry([object()])


def test_inconsistent_evaluator_assertion_and_bad_evaluator():
    definition = registration().definition
    for evaluator in (
        object(),
        type("Bad", (), {"id": "other", "evaluate": lambda s, i: ()})(),
    ):
        with pytest.raises(ValueError):
            ControlRegistration(definition, evaluator)


def test_input_copying_order_exact_lookup_and_frozen_bindings():
    first, second = registration(), registration("second", "second.code")
    entries = [first, second]
    registry = ControlRegistry(entries)
    entries.clear()
    first.evaluator.id = "other"
    assert registry.registrations == (first, second)
    assert registry.resolve("sample") is first
    assert registry.resolve("second") is second
    with pytest.raises(KeyError):
        registry.resolve("other")
    with pytest.raises(FrozenInstanceError):
        first.definition.id = "other"
    findings = [FindingDefinition("copied.code", False, False)]
    definition = ControlDefinition("copied", findings)
    findings.clear()
    assert len(definition.findings) == 1
    with pytest.raises(FrozenInstanceError):
        registry.registrations = ()


def test_production_preserves_email_first_in_expanded_pack():
    registry = default_controls()
    assert [r.definition.id for r in registry.registrations] == [
        "email-address",
        "bearer-credential",
        "pem-private-key",
        "github-token",
        "us-ssn",
        "known-attack-signatures",
        "semantic-security",
    ]
    assert registry.registrations[0].definition.findings == (
        FindingDefinition("pii.email", True, True),
    )
