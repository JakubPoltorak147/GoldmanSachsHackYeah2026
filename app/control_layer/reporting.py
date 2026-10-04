"""Closed, content-free reporting contracts and startup-bound projection."""

import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID

from app.control_layer.audit import AuditEvent
from app.control_layer.domain import Action
from app.control_layer.policy import BoundPolicy
from app.control_layer.registry import machine_id
from app.control_layer.targets import TargetRegistry


class ReportingError(Exception):
    def __init__(self, code: str = "reporting_unavailable") -> None:
        super().__init__(code)


class InvocationStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"
    NOT_INVOKED = "not_invoked"


class GroupBy(StrEnum):
    ACTION = "action"
    TARGET = "target_id"


def duration(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def utc(value: object) -> bool:
    return (
        type(value) is datetime
        and value.tzinfo is not None
        and value.utcoffset() == timedelta(0)
    )


@dataclass(frozen=True, slots=True)
class FindingCount:
    control_id: str
    code: str
    action: Action
    count: int


@dataclass(frozen=True, slots=True)
class ReportingEvent:
    interaction_id: UUID
    timestamp: datetime
    event_type: str
    target_id: str
    model_id: str | None
    policy_digest: str
    action: Action | None
    reason_code: str | None
    error_code: str | None
    forwarding_eligible: bool
    evaluation_duration_ms: float
    evaluated_controls: tuple[str, ...]
    control_status: tuple[tuple[str, bool], ...]
    findings: tuple[FindingCount, ...]


@dataclass(frozen=True, slots=True)
class Completion:
    interaction_id: UUID
    completed_at: datetime
    status: InvocationStatus
    invocation_duration_ms: float
    total_duration_ms: float

    def __post_init__(self):
        if (
            type(self.interaction_id) is not UUID
            or not utc(self.completed_at)
            or type(self.status) is not InvocationStatus
            or self.status not in (InvocationStatus.SUCCEEDED, InvocationStatus.FAILED)
            or not duration(self.invocation_duration_ms)
            or not duration(self.total_duration_ms)
            or self.total_duration_ms < self.invocation_duration_ms
        ):
            raise ReportingError("invalid_reporting_record")

    @property
    def error_code(self) -> str | None:
        return "target_failed" if self.status == InvocationStatus.FAILED else None


@dataclass(frozen=True, slots=True)
class EventView:
    sequence: int
    event: ReportingEvent
    invocation_status: InvocationStatus
    completion: Completion | None
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class EventFilter:
    from_time: datetime | None = None
    to_time: datetime | None = None
    action: Action | None = None
    target_id: str | None = None
    invocation_status: InvocationStatus | None = None

    def __post_init__(self):
        if (
            (self.from_time is None) != (self.to_time is None)
            or (
                self.from_time is not None
                and (
                    not utc(self.from_time)
                    or not utc(self.to_time)
                    or self.from_time >= self.to_time
                )
            )
            or (self.action is not None and type(self.action) is not Action)
            or (self.target_id is not None and not machine_id(self.target_id))
            or (
                self.invocation_status is not None
                and type(self.invocation_status) is not InvocationStatus
            )
        ):
            raise ReportingError("invalid_reporting_query")


@dataclass(frozen=True, slots=True)
class TimingSummary:
    samples: int
    sum_ms: float
    min_ms: float | None
    max_ms: float | None
    mean_ms: float | None


@dataclass(frozen=True, slots=True)
class FindingSummary:
    control_id: str
    code: str
    occurrences: int
    affected_interactions: int


@dataclass(frozen=True, slots=True)
class Summary:
    interaction_total: int
    actions: tuple[tuple[Action, int], ...]
    operational_failure_total: int
    invocations: tuple[tuple[InvocationStatus, int], ...]
    findings: tuple[FindingSummary, ...]
    evaluation: TimingSummary
    invocation: TimingSummary
    total: TimingSummary


@dataclass(frozen=True, slots=True)
class GroupSummary:
    key: str | None
    summary: Summary


@dataclass(frozen=True, slots=True)
class SummaryResult:
    overall: Summary
    groups: tuple[GroupSummary, ...]


class ReportingProjection:
    def __init__(self, policy: BoundPolicy, targets: TargetRegistry):
        if type(policy) is not BoundPolicy or type(targets) is not TargetRegistry:
            raise ReportingError("invalid_reporting_configuration")
        self.policy = policy
        self.targets = targets

    def project(self, event: AuditEvent) -> ReportingEvent:
        try:
            if (
                type(event) is not AuditEvent
                or type(event.interaction_id) is not UUID
                or not utc(event.timestamp)
                or type(event.policy_digest) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", event.policy_digest)
                or event.policy_digest != self.policy.digest
                or not duration(event.evaluation_duration_ms)
                or type(event.forwarding_eligible) is not bool
                or type(event.control_status) is not tuple
                or any(
                    type(x) is not tuple
                    or len(x) != 2
                    or type(x[0]) is not str
                    or type(x[1]) is not bool
                    for x in event.control_status
                )
                or event.control_status
                != tuple((e.control_id, e.enabled) for e in self.policy.entries)
                or type(event.evaluated_controls) is not tuple
                or any(type(x) is not str for x in event.evaluated_controls)
                or type(event.finding_counts) is not tuple
                or type(event.target_id) is not str
                or type(event.event_type) is not str
            ):
                raise ValueError()
            enabled = tuple(e.control_id for e in self.policy.entries if e.enabled)
            decision = event.event_type == "decision"
            if decision:
                if (
                    event.evaluated_controls != enabled
                    or type(event.action) is not Action
                    or event.error_code is not None
                ):
                    raise ValueError()
            elif (
                event.event_type != "operational_failure"
                or type(event.error_code) is not str
                or event.error_code != "evaluation_failed"
                or event.action is not None
                or event.finding_counts
                or event.evaluated_controls != enabled[: len(event.evaluated_controls)]
            ):
                raise ValueError()
            model = None
            if event.target_id == "unresolved":
                if decision or event.evaluated_controls:
                    raise ValueError()
            else:
                model = self.targets.resolve(event.target_id).definition.model_id
            catalogue = {
                code: (e.control_id, action)
                for e in self.policy.entries
                if e.enabled
                for code, action in e.mappings
            }
            findings = []
            seen = set()
            for pair in event.finding_counts:
                if type(pair) is not tuple or len(pair) != 2:
                    raise ValueError()
                code, count = pair
                if (
                    type(code) is not str
                    or code not in catalogue
                    or code in seen
                    or type(count) is not int
                    or count <= 0
                ):
                    raise ValueError()
                control, action = catalogue[code]
                if control not in event.evaluated_controls:
                    raise ValueError()
                findings.append(FindingCount(control, code, action, count))
                seen.add(code)
            rank = {Action.ALLOW: 0, Action.REDACT: 1, Action.BLOCK: 2}
            if decision and event.action != max(
                (f.action for f in findings), key=rank.get, default=Action.ALLOW
            ):
                raise ValueError()
            if event.forwarding_eligible != (decision and event.action != Action.BLOCK):
                raise ValueError()
            return ReportingEvent(
                event.interaction_id,
                event.timestamp.astimezone(UTC),
                event.event_type,
                event.target_id,
                model,
                self.policy.digest,
                event.action,
                ("policy_resolved" if findings else "no_findings")
                if decision
                else None,
                None if decision else "evaluation_failed",
                event.forwarding_eligible,
                float(event.evaluation_duration_ms),
                event.evaluated_controls,
                event.control_status,
                tuple(findings),
            )
        except Exception:
            raise ReportingError("invalid_reporting_record") from None
