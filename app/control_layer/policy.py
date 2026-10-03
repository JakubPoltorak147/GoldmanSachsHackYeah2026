"""Strict startup configuration and pure central decision/redaction rules."""

import hashlib
import json
import re
from dataclasses import dataclass, replace
from pathlib import Path

import yaml

from app.control_layer.domain import (
    Action,
    Decision,
    EvaluationError,
    Finding,
    FindingResolution,
    Interaction,
    PolicyError,
    Span,
)
from app.control_layer.registry import ControlRegistration, ControlRegistry


@dataclass(frozen=True)
class ControlPolicy:
    control_id: str
    enabled: bool
    mappings: tuple[tuple[str, Action], ...]


@dataclass(frozen=True)
class Policy:
    policy_id: str
    digest: str
    controls: tuple[ControlPolicy, ...]


@dataclass(frozen=True)
class ControlPlanEntry:
    registration: ControlRegistration
    enabled: bool
    mappings: tuple[tuple[str, Action], ...]

    @property
    def control_id(self) -> str:
        return self.registration.definition.id


@dataclass(frozen=True)
class BoundPolicy:
    snapshot: Policy
    entries: tuple[ControlPlanEntry, ...]

    @property
    def policy_id(self) -> str:
        return self.snapshot.policy_id

    @property
    def digest(self) -> str:
        return self.snapshot.digest

    @property
    def controls(self) -> tuple[ControlPlanEntry, ...]:
        return self.entries


class _UniqueLoader(yaml.SafeLoader):
    pass


def _mapping(loader: _UniqueLoader, node: yaml.MappingNode) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if key in result:
            raise PolicyError()
        result[key] = loader.construct_object(value_node, deep=True)
    return result


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _keys(value: object, required: set[str], optional: set[str] = frozenset()) -> dict:
    if type(value) is not dict or not required <= value.keys():
        raise PolicyError()
    if value.keys() - required - optional:
        raise PolicyError()
    return value


def load_policy(path: str | Path, registry: ControlRegistry) -> BoundPolicy:
    try:
        raw = yaml.load(Path(path).read_text(encoding="utf-8"), Loader=_UniqueLoader)
        root = _keys(raw, {"version", "policy_id", "controls"})
        if type(root["version"]) is not int or root["version"] != 1:
            raise PolicyError()
        policy_id = root["policy_id"]
        if type(policy_id) is not str or not re.fullmatch(
            r"[A-Za-z0-9_-]{1,64}", policy_id
        ):
            raise PolicyError()
        if type(registry) is not ControlRegistry:
            raise PolicyError()
        controls = _keys(
            root["controls"], {r.definition.id for r in registry.registrations}
        )
        entries = []
        canonical_controls = {}
        for registration in registry.registrations:
            definition = registration.definition
            config = _keys(controls[definition.id], {"enabled"}, {"findings"})
            if type(config["enabled"]) is not bool:
                raise PolicyError()
            codes = {f.code: f for f in definition.findings}
            findings = _keys(config.get("findings", {}), set(), set(codes))
            if config["enabled"] and set(findings) != set(codes):
                raise PolicyError()
            mappings = []
            for code, action in findings.items():
                if type(action) is not str:
                    raise PolicyError()
                action = Action(action)
                if action == Action.REDACT and not codes[code].supports_redaction:
                    raise PolicyError()
                mappings.append((code, action))
            mappings = tuple(mappings)
            entries.append(ControlPlanEntry(registration, config["enabled"], mappings))
            canonical_controls[definition.id] = {
                "enabled": config["enabled"],
                "findings": dict(mappings),
            }
        canonical = {
            "version": 1,
            "policy_id": policy_id,
            "controls": canonical_controls,
        }
        digest = hashlib.sha256(
            json.dumps(canonical, sort_keys=True).encode()
        ).hexdigest()
        snapshot = Policy(
            policy_id,
            digest,
            tuple(ControlPolicy(e.control_id, e.enabled, e.mappings) for e in entries),
        )
        return BoundPolicy(snapshot, tuple(entries))
    except Exception:
        raise PolicyError() from None


def validate_findings(
    findings: object,
    registration: ControlRegistration,
    content: str,
) -> tuple[Finding, ...]:
    try:
        if type(findings) is not tuple or type(registration) is not ControlRegistration:
            raise EvaluationError()
        definition = registration.definition
        codes = {f.code: f for f in definition.findings}
        validated = []
        for finding in findings:
            if (
                type(finding) is not Finding
                or type(finding.control_id) is not str
                or finding.control_id != definition.id
                or type(finding.code) is not str
                or finding.code not in codes
            ):
                raise EvaluationError()
            if finding.span is not None:
                span = finding.span
                if (
                    type(span) is not Span
                    or type(span.start) is not int
                    or type(span.end) is not int
                    or not 0 <= span.start < span.end <= len(content)
                ):
                    raise EvaluationError()
            if codes[finding.code].span_required and finding.span is None:
                raise EvaluationError()
            validated.append(
                Finding(definition.id, codes[finding.code].code, finding.span)
            )
        return tuple(validated)
    except Exception:
        raise EvaluationError() from None


def decide(
    interaction: Interaction,
    findings: tuple[Finding, ...],
    evaluated_controls: tuple[str, ...],
    policy: BoundPolicy,
) -> Decision:
    try:
        if type(policy) is not BoundPolicy or type(findings) is not tuple:
            raise EvaluationError()
        if type(policy.entries) is not tuple or type(evaluated_controls) is not tuple:
            raise EvaluationError()
        configs = {}
        for entry in policy.entries:
            if type(entry) is not ControlPlanEntry or type(entry.enabled) is not bool:
                raise EvaluationError()
            if type(entry.registration) is not ControlRegistration:
                raise EvaluationError()
            if entry.control_id in configs or type(entry.mappings) is not tuple:
                raise EvaluationError()
            definitions = {f.code: f for f in entry.registration.definition.findings}
            mappings = {}
            for mapping in entry.mappings:
                if type(mapping) is not tuple or len(mapping) != 2:
                    raise EvaluationError()
                code, action = mapping
                if (
                    type(code) is not str
                    or code not in definitions
                    or code in mappings
                    or type(action) is not Action
                    or (
                        action == Action.REDACT
                        and not definitions[code].supports_redaction
                    )
                ):
                    raise EvaluationError()
                mappings[code] = action
            if entry.enabled and set(mappings) != set(definitions):
                raise EvaluationError()
            configs[entry.control_id] = (entry, mappings)
        expected_snapshot = tuple(
            ControlPolicy(e.control_id, e.enabled, e.mappings) for e in policy.entries
        )
        if policy.snapshot.controls != expected_snapshot:
            raise EvaluationError()
        enabled = tuple(e.control_id for e in policy.entries if e.enabled)
        if enabled != evaluated_controls:
            raise EvaluationError()
        resolutions = []
        for finding in findings:
            if type(finding) is not Finding or type(finding.control_id) is not str:
                raise EvaluationError()
            entry, mappings = configs[finding.control_id]
            if not entry.enabled:
                raise EvaluationError()
            finding = validate_findings(
                (finding,), entry.registration, interaction.content
            )[0]
            action = mappings[finding.code]
            resolutions.append(
                FindingResolution(finding, f"{entry.control_id}:{finding.code}", action)
            )
        rank = {Action.ALLOW: 0, Action.REDACT: 1, Action.BLOCK: 2}
        action = max(
            (r.action for r in resolutions), key=rank.get, default=Action.ALLOW
        )
        reason = "no_findings" if not resolutions else "policy_resolved"
        return Decision(action, evaluated_controls, tuple(resolutions), reason)
    except Exception:
        raise EvaluationError() from None


def forwarded_interaction(
    interaction: Interaction, decision: Decision
) -> Interaction | None:
    if decision.action == Action.BLOCK:
        return None
    if decision.action == Action.ALLOW:
        return interaction
    if decision.action != Action.REDACT:
        raise EvaluationError()
    spans = []
    for resolution in decision.resolutions:
        if resolution.action == Action.REDACT:
            span = resolution.finding.span
            if (
                type(span) is not Span
                or type(span.start) is not int
                or type(span.end) is not int
                or not 0 <= span.start < span.end <= len(interaction.content)
            ):
                raise EvaluationError()
            spans.append(span)
    if not spans:
        raise EvaluationError()
    intervals = []
    for span in sorted(spans, key=lambda s: (s.start, s.end)):
        if intervals and span.start <= intervals[-1][1]:
            intervals[-1] = (intervals[-1][0], max(intervals[-1][1], span.end))
        else:
            intervals.append((span.start, span.end))
    parts, offset = [], 0
    for start, end in intervals:
        parts.extend((interaction.content[offset:start], "[REDACTED]"))
        offset = end
    parts.append(interaction.content[offset:])
    return replace(interaction, content="".join(parts))
