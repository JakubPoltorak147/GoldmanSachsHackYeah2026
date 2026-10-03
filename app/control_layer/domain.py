"""Immutable core contracts; no transport or provider dependencies."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4


class Action(StrEnum):
    ALLOW = "ALLOW"
    REDACT = "REDACT"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class Interaction:
    id: UUID
    target_id: str
    content: str

    @classmethod
    def create(cls, target_id: str, content: str) -> "Interaction":
        return cls(uuid4(), target_id, content)


@dataclass(frozen=True)
class Span:
    start: int
    end: int


@dataclass(frozen=True)
class Finding:
    control_id: str
    code: str
    span: Span | None = None


@dataclass(frozen=True)
class FindingResolution:
    finding: Finding
    rule_id: str
    action: Action


@dataclass(frozen=True)
class Decision:
    action: Action
    evaluated_controls: tuple[str, ...]
    resolutions: tuple[FindingResolution, ...]
    reason_code: str


class Control(Protocol):
    id: str

    def evaluate(self, interaction: Interaction) -> tuple[Finding, ...]: ...


class EvaluationError(Exception):
    def __init__(self) -> None:
        super().__init__("evaluation_failed")


class PolicyError(Exception):
    def __init__(self) -> None:
        super().__init__("invalid_policy")


class AuditError(Exception):
    def __init__(self) -> None:
        super().__init__("audit_failed")


class TargetError(Exception):
    def __init__(self) -> None:
        super().__init__("target_failed")
