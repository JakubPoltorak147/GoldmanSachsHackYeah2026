from dataclasses import FrozenInstanceError

import pytest

from app.control_layer.composition import default_targets
from app.control_layer.domain import Interaction
from app.control_layer.targets import (
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
    TargetResult,
)


class Spy:
    def __init__(self):
        self.calls = []

    def invoke(self, interaction):
        self.calls.append(interaction)
        return TargetResult(interaction.content)


@pytest.mark.parametrize(
    "identifier",
    [None, 1, True, "", "A", "a:b", "https://host", "a" * 65, "é", "unresolved"],
)
def test_invalid_target_id(identifier):
    with pytest.raises(ValueError):
        TargetDefinition(identifier)


def test_exact_immutable_lookup_without_invocation():
    first = RegisteredTarget(TargetDefinition("first"), Spy())
    second = RegisteredTarget(TargetDefinition("second"), Spy())
    inputs = [first, second]
    registry = TargetRegistry(inputs)
    inputs.clear()
    assert registry.resolve("first") is first
    assert registry.resolve("second") is second
    for unknown in ("FIRST", "https://host/first", "first/", "local-echo", None, []):
        with pytest.raises(KeyError):
            registry.resolve(unknown)
    assert first.adapter.calls == second.adapter.calls == []
    with pytest.raises(FrozenInstanceError):
        registry.registrations = ()
    with pytest.raises(ValueError):
        TargetRegistry([first, first])
    with pytest.raises(ValueError):
        TargetRegistry([object()])
    with pytest.raises(ValueError):
        RegisteredTarget(first.definition, object())
    with pytest.raises(ValueError):
        RegisteredTarget(object(), first.adapter)


def test_default_target_is_only_local_echo():
    registry = default_targets()
    assert len(registry.registrations) == 1
    binding = registry.resolve("local-echo")
    interaction = Interaction.create("local-echo", " exact text ")
    assert binding.adapter.invoke(interaction) == TargetResult(interaction.content)
