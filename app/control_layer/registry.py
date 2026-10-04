"""Immutable server-owned extension metadata; no discovery or dynamic loading."""

import re
from dataclasses import dataclass

from app.control_layer.domain import Control


def machine_id(value: object, *, code: bool = False) -> bool:
    pattern = r"[a-z][a-z0-9_.-]{0,63}" if code else r"[a-z][a-z0-9_-]{0,63}"
    return type(value) is str and re.fullmatch(pattern, value) is not None


@dataclass(frozen=True)
class FindingDefinition:
    code: str
    span_required: bool
    supports_redaction: bool

    def __post_init__(self):
        if (
            not machine_id(self.code, code=True)
            or type(self.span_required) is not bool
            or type(self.supports_redaction) is not bool
            or (self.supports_redaction and not self.span_required)
        ):
            raise ValueError("invalid_registration")


@dataclass(frozen=True)
class ControlDefinition:
    id: str
    findings: tuple[FindingDefinition, ...]
    model_id: str | None = None

    def __post_init__(self):
        findings = tuple(self.findings)
        if (
            not machine_id(self.id)
            or (
                self.model_id is not None
                and (
                    type(self.model_id) is not str
                    or re.fullmatch(r"[a-z0-9][a-z0-9._:-]{0,127}", self.model_id)
                    is None
                )
            )
            or not findings
            or any(type(f) is not FindingDefinition for f in findings)
            or len({f.code for f in findings}) != len(findings)
        ):
            raise ValueError("invalid_registration")
        object.__setattr__(self, "findings", findings)


@dataclass(frozen=True)
class ControlRegistration:
    definition: ControlDefinition
    evaluator: Control

    def __post_init__(self):
        if type(self.definition) is not ControlDefinition or not callable(
            getattr(self.evaluator, "evaluate", None)
        ):
            raise ValueError("invalid_registration")
        if hasattr(self.evaluator, "id") and (
            type(self.evaluator.id) is not str
            or self.evaluator.id != self.definition.id
        ):
            raise ValueError("invalid_registration")


@dataclass(frozen=True)
class ControlRegistry:
    registrations: tuple[ControlRegistration, ...]

    def __post_init__(self):
        registrations = tuple(self.registrations)
        ids, codes = set(), set()
        for registration in registrations:
            if type(registration) is not ControlRegistration:
                raise ValueError("invalid_registration")
            definition = registration.definition
            if definition.id in ids:
                raise ValueError("invalid_registration")
            ids.add(definition.id)
            for finding in definition.findings:
                if finding.code in codes:
                    raise ValueError("invalid_registration")
                codes.add(finding.code)
        object.__setattr__(self, "registrations", registrations)

    def resolve(self, control_id: str) -> ControlRegistration:
        if type(control_id) is str:
            for registration in self.registrations:
                if registration.definition.id == control_id:
                    return registration
        raise KeyError("unknown_control")
