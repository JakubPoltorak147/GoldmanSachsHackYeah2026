"""Synchronous evaluation, audit gate, and exactly-once eligible dispatch."""

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID

from app.control_layer.audit import AuditEvent, AuditSink
from app.control_layer.domain import Decision, EvaluationError, Interaction
from app.control_layer.policy import (
    BoundPolicy,
    decide,
    forwarded_interaction,
    validate_findings,
)
from app.control_layer.reporting import InvocationStatus
from app.control_layer.reporting_store import PersistentAuditSink
from app.control_layer.targets import TargetRegistry, TargetResult


@dataclass(frozen=True)
class ServiceOutcome:
    interaction_id: UUID
    decision: Decision | None = None
    target_result: TargetResult | None = None
    error_code: str | None = None


class InteractionService:
    def __init__(
        self,
        policy: BoundPolicy,
        audit_sink: AuditSink,
        targets: TargetRegistry,
    ) -> None:
        if type(policy) is not BoundPolicy or type(targets) is not TargetRegistry:
            raise ValueError("invalid_composition")
        self.policy = policy
        self.audit_sink = audit_sink
        self.targets = targets

    def _event(
        self,
        interaction: Interaction,
        started: float,
        evaluated: tuple[str, ...],
        target_id: str,
        policy: BoundPolicy,
        decision: Decision | None = None,
        semantic: tuple = (None, None, None),
    ) -> AuditEvent:
        counts = (
            Counter(r.finding.code for r in decision.resolutions) if decision else {}
        )
        return AuditEvent(
            event_type="decision" if decision else "operational_failure",
            interaction_id=interaction.id,
            timestamp=datetime.now(UTC),
            target_id=target_id,
            policy_digest=policy.digest,
            evaluated_controls=evaluated,
            control_status=tuple((c.control_id, c.enabled) for c in policy.entries),
            action=decision.action if decision else None,
            finding_counts=tuple(sorted(counts.items())),
            forwarding_eligible=decision is not None and decision.action != "BLOCK",
            evaluation_duration_ms=max(0, (perf_counter() - started) * 1000),
            error_code=None if decision else "evaluation_failed",
            semantic_duration_ms=semantic[0],
            semantic_model_id=semantic[1],
            semantic_status=semantic[2],
        )

    def evaluate(self, interaction: Interaction) -> ServiceOutcome:
        started = perf_counter()
        evaluated = []
        semantic = (None, None, None)
        target_id = "unresolved"
        policy = self.policy
        try:
            binding = self.targets.resolve(interaction.target_id)
            target_id = binding.definition.target_id
            findings = []
            for entry in policy.entries:
                if type(entry.enabled) is not bool:
                    raise EvaluationError()
                if entry.enabled:
                    semantic_attempt = entry.control_id == "semantic-security"
                    if semantic_attempt:
                        semantic_started = perf_counter()
                    succeeded = False
                    try:
                        output = entry.registration.evaluator.evaluate(interaction)
                        validated = validate_findings(
                            output, entry.registration, interaction.content
                        )
                        succeeded = True
                    finally:
                        if semantic_attempt:
                            semantic = (
                                max(0, (perf_counter() - semantic_started) * 1000),
                                entry.registration.definition.model_id,
                                "succeeded" if succeeded else "failed",
                            )
                    evaluated.append(entry.control_id)
                    findings.extend(validated)
            decision = decide(interaction, tuple(findings), tuple(evaluated), policy)
            forwarded = forwarded_interaction(interaction, decision)
            event = self._event(
                interaction,
                started,
                tuple(evaluated),
                target_id,
                policy,
                decision,
                semantic,
            )
        except Exception:
            try:
                self.audit_sink.emit(
                    self._event(
                        interaction,
                        started,
                        tuple(evaluated),
                        target_id,
                        policy,
                        semantic=semantic,
                    )
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
        invocation_started = perf_counter()
        try:
            result = binding.adapter.invoke(forwarded)
            if type(result) is not TargetResult or type(result.content) is not str:
                raise EvaluationError()
        except Exception:
            self._complete(
                interaction.id, InvocationStatus.FAILED, invocation_started, started
            )
            return ServiceOutcome(
                interaction.id, decision=decision, error_code="target_failed"
            )
        self._complete(
            interaction.id, InvocationStatus.SUCCEEDED, invocation_started, started
        )
        return ServiceOutcome(interaction.id, decision=decision, target_result=result)

    def _complete(self, identity, status, invocation_started, started):
        finished = perf_counter()
        if isinstance(self.audit_sink, PersistentAuditSink):
            self.audit_sink.complete(
                identity,
                status,
                max(0, (finished - invocation_started) * 1000),
                max(0, (finished - started) * 1000),
            )
