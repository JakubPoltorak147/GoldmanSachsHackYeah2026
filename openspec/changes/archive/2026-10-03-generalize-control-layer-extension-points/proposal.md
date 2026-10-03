# Proposal

## Why

The foundation already separates findings from enforcement, but email-specific policy validation and single-target orchestration prevent genuine extension through its generic domain contracts. Stabilizing registration, startup binding, and trusted metadata now enables independent controls and target development without weakening central policy or audited dispatch.

## What Changes

- Add immutable, server-owned control registrations with declared control IDs, globally unique finding codes, required-span metadata, and span-redaction capability.
- Validate startup policy against the exact control registry and produce an immutable bound policy/execution plan. Reuse those registrations during evaluation; never rebuild composition per request.
- Require explicit enabled/disabled configuration for every registered control and complete finding mappings for enabled controls. **BREAKING for future registry expansion:** registering another production control requires updating existing policy files, otherwise startup fails closed. This change adds no production controls, so existing foundation policy files remain valid.
- Validate findings against their actual producer registration; evaluator-asserted identity cannot select a producer or code catalogue. REDACT-capable definitions require valid original-text spans, regardless of the configured action.
- Add immutable target registration and exact resolution. Audit and dispatch use the same retained target binding; the public target remains `local-echo`.
- Generalize response finding codes to validated strings. The OpenAPI finding-code enum broadens; existing production response values and shapes remain unchanged.
- Move concrete default assembly to a composition root. Prefer the smallest refactor; module-to-package migrations are optional.
- Preserve all foundation security invariants, email semantics, default policy digest, HTTP outcomes, local echo, and audit privacy.

No new production controls, public targets, semantic AI, budgets, reporting, dashboard, authentication, policy reload, output inspection, or generic transformation framework are included.

## Capabilities

### New Capabilities

None; extension contracts belong to the existing policy, gateway, and audit capabilities.

### Modified Capabilities

- `policy-decisions`: immutable registration, registry-bound startup validation/execution, actual-producer finding validation, and span-redaction capability constraints.
- `interaction-gateway`: exact internal target registration/resolution, composition and test injection, generic response finding codes, and explicit public compatibility.
- `decision-audit`: trustworthy metadata from retained registrations and the bound plan, including sanitized unresolved-target operational records.

`email-address-detection` remains unchanged.

## Impact

Likely implementation areas are `app/control_layer/domain.py`, `controls.py`, `targets.py`, `policy.py`, `service.py`, `api.py`, optional dedicated registry/composition modules, and unit/integration tests. `audit.py` may need a small metadata-plumbing change; its sink guarantees remain intact. Default `config/policy.yaml` stays unchanged. No new runtime dependency is required.

Architecture and worklog documentation are updated only after implementation. One owner integrates shared contracts; dependent controls and target changes begin from this prerequisite after it merges. This request authorizes planning only, not apply or archive.
