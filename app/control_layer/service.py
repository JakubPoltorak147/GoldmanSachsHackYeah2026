"""Synchronous evaluation, audit gate, and exactly-once eligible dispatch."""

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID

from app.control_layer.audit import AuditEvent, AuditSink
from app.control_layer.controls import PRODUCTION_CODES, EmailAddressControl
from app.control_layer.domain import Control, Decision, EvaluationError, Interaction
from app.control_layer.policy import (
    Policy,
    decide,
    forwarded_interaction,
    validate_findings,
)
from app.control_layer.targets import TargetAdapter, TargetResult


@dataclass(frozen=True)
class ServiceOutcome:
    interaction_id: UUID
    decision: Decision | None = None
    target_result: TargetResult | None = None
    error_code: str | None = None


class InteractionService:
    def __init__(
        self,
        policy: Policy,
        audit_sink: AuditSink,
        target: TargetAdapter,
        controls: tuple[Control, ...] | None = None,
    ) -> None:
        self.policy = policy
        self.audit_sink = audit_sink
        self.target = target
        self.controls = controls if controls is not None else (EmailAddressControl(),)

    def _event(
        self,
        interaction: Interaction,
        started: float,
        evaluated: tuple[str, ...],
        decision: Decision | None = None,
    ) -> AuditEvent:
        counts = (
            Counter(r.finding.code for r in decision.resolutions) if decision else {}
        )
        return AuditEvent(
            event_type="decision" if decision else "operational_failure",
            interaction_id=interaction.id,
            timestamp=datetime.now(UTC),
            target_id="local-echo",
            policy_digest=self.policy.digest,
            evaluated_controls=evaluated,
            control_status=tuple(
                (c.control_id, c.enabled) for c in self.policy.controls
            ),
            action=decision.action if decision else None,
            finding_counts=tuple(sorted(counts.items())),
            forwarding_eligible=decision is not None and decision.action != "BLOCK",
            evaluation_duration_ms=max(0, (perf_counter() - started) * 1000),
            error_code=None if decision else "evaluation_failed",
        )

    def evaluate(self, interaction: Interaction) -> ServiceOutcome:
        started = perf_counter()
        evaluated = []
        try:
            if interaction.target_id != "local-echo":
                raise EvaluationError()
            registry = {control.id: control for control in self.controls}
            if set(registry) != set(PRODUCTION_CODES) or len(registry) != len(
                self.controls
            ):
                raise EvaluationError()
            findings = []
            for config in self.policy.controls:
                if (
                    config.control_id not in registry
                    or type(config.enabled) is not bool
                ):
                    raise EvaluationError()
                if config.enabled:
                    control = registry[config.control_id]
                    output = control.evaluate(interaction)
                    validated = validate_findings(
                        output, config.control_id, interaction.content, PRODUCTION_CODES
                    )
                    evaluated.append(config.control_id)
                    findings.extend(validated)
            decision = decide(
                interaction, tuple(findings), tuple(evaluated), self.policy
            )
            forwarded = forwarded_interaction(interaction, decision)
            event = self._event(interaction, started, tuple(evaluated), decision)
        except Exception:
            try:
                self.audit_sink.emit(
                    self._event(interaction, started, tuple(evaluated))
                )
            except Exception:
                pass
            return ServiceOutcome(interaction.id, error_code="evaluation_failed")
        try:
            self.audit_sink.emit(event)
        except Exception:
            return ServiceOutcome(interaction.id, error_code="audit_failed")
        if forwarded is None:
            return ServiceOutcome(interaction.id, decision=decision)
        try:
            result = self.target.invoke(forwarded)
            if type(result) is not TargetResult or type(result.content) is not str:
                raise EvaluationError()
        except Exception:
            return ServiceOutcome(
                interaction.id, decision=decision, error_code="target_failed"
            )
        return ServiceOutcome(interaction.id, decision=decision, target_result=result)
