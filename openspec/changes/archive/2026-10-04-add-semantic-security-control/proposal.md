# Proposal

## Why

The implemented defense pack is deterministic; it cannot demonstrate the AI-based half of the challenge's hybrid architecture. One local classifier can add useful semantic detection of prompt injection, instruction override and related exfiltration intent while preserving central enforcement and content-free evidence.

## What Changes

- Add one input-only `semantic-security` control using the existing synchronous Control contract and explicit registration. It emits only three fixed, spanless findings, never actions.
- Add a dedicated bounded Ollama evaluator adapter, separate from target dispatch, with a closed score response schema, no streaming or external services, and deterministic fake-runtime tests.
- Add a strict policy threshold for this control, included in the policy digest; keep action mappings and BLOCK > REDACT > ALLOW in central policy. Semantic codes support ALLOW/BLOCK only.
- Register the control after the six deterministic controls. Keep it explicitly disabled in the baseline policy and provide a complete enabled demo policy with threshold 0.75 and all semantic codes mapped to BLOCK. Enabled runtime failures fail closed as operational evaluation failures.
- Report semantic duration and trusted evaluator model identity separately from target inference through a small closed audit/reporting extension; preserve durable audit gates and historical evidence with an exact version-1 to version-2 storage migration.
- **BREAKING:** administrator-selected policies used with the expanded default registry need an explicit semantic-control entry. Enabled policies need a threshold and all three mappings. Explicit historical registries retain their policy behavior/digests.
- Clarify existing local-model specifications: evaluator calls occur during evaluation; target generation still occurs only after successful required decision audit.

## Capabilities

### New Capabilities

- `semantic-security-detection`: one local input classifier, trusted bounded configuration, strict output validation, threshold semantics, fail-closed behavior and focused adversarial verification.

### Modified Capabilities

- `policy-decisions`: strict semantic threshold configuration bound into immutable policy and digest; unchanged central action resolution.
- `interaction-gateway`: expanded explicit composition, runtime-independent startup with semantic disabled, unchanged public wire contracts and semantic failure outcomes.
- `decision-audit`: closed semantic timing/model evidence, including failed attempts, without submitted or evaluator content.
- `security-reporting`: durable semantic timing/model evidence and minimal non-destructive storage version upgrade.
- `local-model-target`: distinguish evaluator requests from audited target generation and remove the now-obsolete absence-of-semantic-control documentation claim.

## Impact

Primary additions are flat semantic control/runtime modules, their unit/integration tests and an enabled demo policy. Narrow integration touches policy binding, composition, service timing, audit/reporting projection/storage and startup configuration; no new dependency beyond existing HTTPX is expected. Public interaction/decision schemas, targets, deterministic detectors and Finding shape remain unchanged. Implementation documentation will describe configuration, failure behavior, latency and demo limits.

Excluded: output inspection, generic semantic framework, multi-provider support, tools/agents, RAG, memory, model governance, policy reload, dashboard work, runtime/model installation and unrelated refactoring. This request authorizes planning only.
