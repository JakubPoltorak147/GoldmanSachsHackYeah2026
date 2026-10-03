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
| Functional control-layer boundary | IMPLEMENTED | `POST /v1/interactions` intercepts requests before a target and applies centralized control and policy evaluation. Production targets are local echo and bounded loopback Ollama text generation; accepted after fresh correctness/security PASS; evidence is in worklog. |
| Provider-independent integration boundary | PARTIAL | A `TargetAdapter` boundary exists and the foundation is independent of a commercial provider, with local echo and a bounded local Ollama adapter; remote/agent/MCP integrations remain deferred. |
| Architecture documentation | PARTIAL | Implemented architecture is documented in `docs/architecture.md`, and conceptual product direction exists in `docs/project-context.md`. A final challenge-oriented architecture diagram is still required. |
| Centralized policy engine | PARTIAL | Strict startup YAML policy controls enablement and finding-to-action mappings. Model restrictions, budgets, richer thresholds, and other planned policy domains are not implemented. |
| Configurable ALLOW / REDACT / BLOCK enforcement | IMPLEMENTED | Central policy resolves findings with `BLOCK > REDACT > ALLOW`; redaction is centrally applied. |
| Deterministic controls | PARTIAL | Six independent deterministic controls are centrally registered: existing ASCII email, whole-line bearer, supported PEM private-key envelopes, classic GitHub PAT/OAuth shapes, labelled US SSN and bounded known-attack literals. Broader deterministic coverage remains deferred. |
| Semantic / AI-based controls | NOT IMPLEMENTED | No semantic security control or local security model is currently executed. |
| Input data-loss prevention | PARTIAL | Supported email/labelled US SSN and bearer/PEM/classic GitHub credentials have validated original spans and configurable ALLOW/REDACT/BLOCK. Default PII REDACT and credential BLOCK are verified. General PII, arbitrary secrets and output protection remain deferred. |
| Output inspection / output DLP | NOT IMPLEMENTED | Target responses are not currently inspected by security controls. |
| Budget and resource governance | NOT IMPLEMENTED | No token, compute, request, resource, or financial budget enforcement exists. |
| Historical attack mitigation | PARTIAL | Five exact repository-owned literals/four codes identify bounded pickle-global and Python execution indicators; default policy BLOCK prevents dispatch. Versioned strict local catalog supports reviewed future file delivery. Binary scanning, generalized injection, external feeds and remote updates are not implemented. |
| Allowed model restrictions | NOT IMPLEMENTED | One operator-fixed model is a deployment restriction outside policy, not centralized allowed-model governance. |
| Tool and resource restrictions | NOT IMPLEMENTED | Tool and resource authorization policy is not currently implemented. |
| Authentication / authorization | NOT IMPLEMENTED | The foundation intentionally has no verified caller identity or authorization system. |
| Decision auditing | PARTIAL | Safe decision and operational events are emitted and flushed before eligible dispatch. Retention, querying, completion telemetry, and management reporting are not implemented. |
| Performance telemetry | PARTIAL | Evaluation duration is recorded in audit events, but there is no aggregate performance reporting. |
| Security metrics | PARTIAL | Individual audit records contain useful security metadata, but there is no metrics aggregation or reporting API. |
| Interactive dashboard | NOT IMPLEMENTED | No UI exists. |
| Sample configuration | PARTIAL | A strict policy file exists, but it does not yet demonstrate the full challenge configuration surface such as semantic thresholds and budget rules. |
| Runtime policy changes | PARTIAL | Policy is administrator-selected and strictly validated, but it is fixed until process restart. |
| Automated positive and negative tests | PARTIAL | Deterministic local unit/integration tests cover the implemented foundation, extension contracts and security pack, including adversarial near misses, multi-control policy/redaction, audit privacy/failures, migration and concurrency. Transport doubles and a threaded fake runtime verify model dispatch, limits, failures, privacy and concurrency without Ollama. Future budgets/semantic controls lack coverage. |
| Commercial-service independence | IMPLEMENTED | The current foundation runs without an external model, provider, database, or paid commercial service. |
| Ad-hoc control-layer demonstration | PARTIAL | The HTTP endpoint demonstrates six deterministic controls and configurable enforcement with local echo. A fixed local model now receives centrally approved content; semantic security and remote targets remain deferred. |

## Stable evidence

Current implementation details are described in:

- `docs/architecture.md`;
- `docs/system-summary.md`;
- `config/policy.yaml`;
- `tests/unit/`;
- `tests/integration/`.

Completed verification evidence is recorded in:

- `docs/worklog.md`;
- `openspec/changes/archive/2026-10-03-add-deterministic-security-controls/evidence/final-implementation-verification.json`;
- `openspec/changes/archive/2026-10-03-add-deterministic-security-controls/evidence/implementation-reviews.md`.

The deterministic pack was explicitly approved for apply, fully verified and
accepted after fresh correctness and security reviews both returned PASS on
2026-10-03. It was subsequently archived after authorized finalization.
This acceptance adds only bounded deterministic/PII/credential/historical-signature
coverage; it does not satisfy semantic, budget, reporting or dashboard requirements.

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


Local-model integration preserves unchanged deterministic enforcement and policy
digest, required eligibility audit and centrally redacted-only submission. Its
transport/output caps are adapter defenses, not token/compute budget governance.
Generated output is uninspected; reporting, semantic controls, authorization and
budgets remain absent. README records settings, trusted cloud-disabled loopback
runtime preparation, synchronous thread/latency limits and optional real smoke.
Final acceptance is supported by fresh independent correctness/security PASS and
1001 unit/122 integration tests; exact evidence is in worklog. The optional real
Ollama smoke was NOT RUN because runtime prerequisites were absent.
