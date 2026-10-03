"""Target boundary and the only production target: local echo."""

from dataclasses import dataclass
from typing import Protocol

from app.control_layer.domain import Interaction


@dataclass(frozen=True)
class TargetResult:
    content: str


class TargetAdapter(Protocol):
    def invoke(self, interaction: Interaction) -> TargetResult: ...


class LocalEchoTarget:
    def invoke(self, interaction: Interaction) -> TargetResult:
        return TargetResult(interaction.content)
