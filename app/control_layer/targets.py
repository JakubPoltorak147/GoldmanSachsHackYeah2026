"""Target boundary and the only production target: local echo."""

from dataclasses import dataclass
from typing import Protocol

from app.control_layer.domain import Interaction
from app.control_layer.registry import machine_id


@dataclass(frozen=True)
class TargetResult:
    content: str


class TargetAdapter(Protocol):
    def invoke(self, interaction: Interaction) -> TargetResult: ...


class LocalEchoTarget:
    def invoke(self, interaction: Interaction) -> TargetResult:
        return TargetResult(interaction.content)


@dataclass(frozen=True)
class TargetDefinition:
    target_id: str

    def __post_init__(self):
        if not machine_id(self.target_id) or self.target_id == "unresolved":
            raise ValueError("invalid_registration")


@dataclass(frozen=True)
class RegisteredTarget:
    definition: TargetDefinition
    adapter: TargetAdapter

    def __post_init__(self):
        if type(self.definition) is not TargetDefinition or not callable(
            getattr(self.adapter, "invoke", None)
        ):
            raise ValueError("invalid_registration")


class TargetResolver(Protocol):
    def resolve(self, target_id: str) -> RegisteredTarget: ...


@dataclass(frozen=True)
class TargetRegistry:
    registrations: tuple[RegisteredTarget, ...]

    def __post_init__(self):
        registrations = tuple(self.registrations)
        if any(type(r) is not RegisteredTarget for r in registrations):
            raise ValueError("invalid_registration")
        ids = [r.definition.target_id for r in registrations]
        if len(set(ids)) != len(ids):
            raise ValueError("invalid_registration")
        object.__setattr__(self, "registrations", registrations)

    def resolve(self, target_id: str) -> RegisteredTarget:
        if type(target_id) is str:
            for registration in self.registrations:
                if registration.definition.target_id == target_id:
                    return registration
        raise KeyError("unknown_target")
