# Challenge Requirement Traceability

## Purpose

This document tracks coverage of the external challenge requirements against the
current repository.

It is a coverage ledger, not an implementation plan.

It does not authorize product changes and must not duplicate task planning from
OpenSpec.

Implementation status must be based on behavior that actually exists in the
repository.

## Status definitions

- `IMPLEMENTED` — the current repository provides the required capability for
  the stated scope.
- `PARTIAL` — part of the capability exists, but the challenge-level requirement
  is not yet fully demonstrated.
- `NOT IMPLEMENTED` — the repository does not currently provide the capability.

## Current coverage

| Challenge area | Status | Current repository coverage |
| --- | --- | --- |
| Functional control-layer boundary | IMPLEMENTED | `POST /v1/interactions` intercepts requests before a target and applies centralized control and policy evaluation. Current production target is local echo only. |
| Provider-independent integration boundary | PARTIAL | A `TargetAdapter` boundary exists and the foundation is independent of a commercial provider, but only the local echo implementation exists. |
| Architecture documentation | PARTIAL | Implemented architecture is documented in `docs/architecture.md`, and conceptual product direction exists in `docs/project-context.md`. A final challenge-oriented architecture diagram is still required. |
| Centralized policy engine | PARTIAL | Strict startup YAML policy controls enablement and finding-to-action mappings. Model restrictions, budgets, richer thresholds, and other planned policy domains are not implemented. |
| Configurable ALLOW / REDACT / BLOCK enforcement | IMPLEMENTED | Central policy resolves findings with `BLOCK > REDACT > ALLOW`; redaction is centrally applied. |
| Deterministic controls | PARTIAL | One deliberately bounded ASCII email-address detector is implemented. Broader PII, secret detection, attack signatures, and other deterministic controls are not implemented. |
| Semantic / AI-based controls | NOT IMPLEMENTED | No semantic security control or local security model is currently executed. |
| Input data-loss prevention | PARTIAL | Supported email addresses can be detected and redacted. General PII and secret protection are not implemented. |
| Output inspection / output DLP | NOT IMPLEMENTED | Target responses are not currently inspected by security controls. |
| Budget and resource governance | NOT IMPLEMENTED | No token, compute, request, resource, or financial budget enforcement exists. |
| Historical attack mitigation | NOT IMPLEMENTED | No attack-signature feed or historical exploit control exists. |
| Allowed model restrictions | NOT IMPLEMENTED | Policy cannot currently restrict model selection. |
| Tool and resource restrictions | NOT IMPLEMENTED | Tool and resource authorization policy is not currently implemented. |
| Authentication / authorization | NOT IMPLEMENTED | The foundation intentionally has no verified caller identity or authorization system. |
| Decision auditing | PARTIAL | Safe decision and operational events are emitted and flushed before eligible dispatch. Retention, querying, completion telemetry, and management reporting are not implemented. |
| Performance telemetry | PARTIAL | Evaluation duration is recorded in audit events, but there is no aggregate performance reporting. |
| Security metrics | PARTIAL | Individual audit records contain useful security metadata, but there is no metrics aggregation or reporting API. |
| Interactive dashboard | NOT IMPLEMENTED | No UI exists. |
| Sample configuration | PARTIAL | A strict policy file exists, but it does not yet demonstrate the full challenge configuration surface such as semantic thresholds and budget rules. |
| Runtime policy changes | PARTIAL | Policy is administrator-selected and strictly validated, but it is fixed until process restart. |
| Automated positive and negative tests | PARTIAL | The implemented foundation has deterministic unit and HTTP integration coverage. Challenge-level coverage for future budgets, semantic controls, exploit mitigation, and other capabilities does not yet exist. |
| Commercial-service independence | IMPLEMENTED | The current foundation runs without an external model, provider, database, or paid commercial service. |
| Ad-hoc control-layer demonstration | PARTIAL | The HTTP endpoint can be exercised interactively, but it currently demonstrates only the local echo target and bounded email control. |

## Stable evidence

Current implementation details are described in:

- `docs/architecture.md`;
- `docs/system-summary.md`;
- `config/policy.yaml`;
- `tests/unit/`;
- `tests/integration/`.

Completed verification evidence is recorded in:

- `docs/worklog.md`.

OpenSpec defines required behavior and must be consulted before treating planned
capabilities as implemented.

## Update rule

Update this document after an OpenSpec change has been implemented, verified,
independently reviewed, and accepted as current behavior.

Do not mark a requirement `IMPLEMENTED` because:

- a proposal exists;
- code exists on an unmerged branch;
- an OpenSpec task is merely marked complete;
- a capability exists only in conceptual documentation.

Do not use this file as a substitute for an OpenSpec proposal, design, spec, or
task list.
