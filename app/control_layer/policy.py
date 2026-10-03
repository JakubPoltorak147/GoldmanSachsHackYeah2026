"""Strict startup configuration and pure central decision/redaction rules."""

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

import yaml

from app.control_layer.controls import EMAIL_CODE, EMAIL_CONTROL_ID, PRODUCTION_CODES
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


def load_policy(path: str | Path) -> Policy:
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
        controls = _keys(root["controls"], {EMAIL_CONTROL_ID})
        email = _keys(controls[EMAIL_CONTROL_ID], {"enabled"}, {"findings"})
        if type(email["enabled"]) is not bool:
            raise PolicyError()
        findings = _keys(email.get("findings", {}), set(), {EMAIL_CODE})
        if email["enabled"] and EMAIL_CODE not in findings:
            raise PolicyError()
        mappings = tuple((code, Action(action)) for code, action in findings.items())
        canonical = {
            "version": 1,
            "policy_id": policy_id,
            "controls": {
                EMAIL_CONTROL_ID: {
                    "enabled": email["enabled"],
                    "findings": dict(mappings),
                }
            },
        }
        digest = hashlib.sha256(
            json.dumps(canonical, sort_keys=True).encode()
        ).hexdigest()
        return Policy(
            policy_id,
            digest,
            (ControlPolicy(EMAIL_CONTROL_ID, email["enabled"], mappings),),
        )
    except Exception:
        raise PolicyError() from None


def validate_findings(
    findings: object,
    control_id: str,
    content: str,
    trusted_codes: Mapping[str, frozenset[str]],
) -> tuple[Finding, ...]:
    if type(findings) is not tuple or control_id not in trusted_codes:
        raise EvaluationError()
    for finding in findings:
        if (
            type(finding) is not Finding
            or type(finding.control_id) is not str
            or finding.control_id != control_id
            or type(finding.code) is not str
            or finding.code not in trusted_codes[control_id]
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
        if control_id == EMAIL_CONTROL_ID and finding.span is None:
            raise EvaluationError()
    return findings


def decide(
    interaction: Interaction,
    findings: tuple[Finding, ...],
    evaluated_controls: tuple[str, ...],
    policy: Policy,
    trusted_codes: Mapping[str, frozenset[str]] = PRODUCTION_CODES,
) -> Decision:
    try:
        enabled = tuple(c.control_id for c in policy.controls if c.enabled)
        if enabled != evaluated_controls or len(set(enabled)) != len(enabled):
            raise EvaluationError()
        resolutions = []
        for finding in findings:
            validate_findings(
                (finding,), finding.control_id, interaction.content, trusted_codes
            )
            configs = [
                c
                for c in policy.controls
                if c.control_id == finding.control_id and c.enabled
            ]
            if len(configs) != 1:
                raise EvaluationError()
            actions = [
                action for code, action in configs[0].mappings if code == finding.code
            ]
            if len(actions) != 1 or type(actions[0]) is not Action:
                raise EvaluationError()
            action = actions[0]
            if action == Action.REDACT and finding.span is None:
                raise EvaluationError()
            resolutions.append(
                FindingResolution(
                    finding, f"{finding.control_id}:{finding.code}", action
                )
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
