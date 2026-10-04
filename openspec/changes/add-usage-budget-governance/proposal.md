# Proposal

## Why

The challenge requires "budget and resource governance" (token consumption, spend, compute, resource access) and expects evaluators to "exceed configured budgets". `docs/requirements/traceability.md` records this area as NOT IMPLEMENTED: today any caller can send unlimited requests of any size, and a flood of inputs can exhaust the local model and the semantic evaluator. The traceability matrix also lists the sample configuration as missing "budget rules" and telemetry as missing token/cost/resource data.

This change adds one focused, convincing control family — usage budgets — and makes it easy for an evaluator to configure, exceed, observe and verify.

## What Changes

- Add a deterministic `usage-budget` control, registered in the production registry, that enforces three centrally configured limits over a fixed time window: maximum requests, maximum estimated input tokens, and maximum estimated tokens for a single request.
- It emits three spanless findings — `budget.request_limit`, `budget.token_limit`, `budget.request_size` — mapped by policy to `ALLOW` (observe-only / shadow mode) or `BLOCK`. REDACT is unsupported. Enforcement stays central; the control owns no action.
- Extend the strict version-1 policy format with an optional `limits` mapping, accepted only for `usage-budget` and required when that control is enabled. Limits are validated, normalised and included in the policy digest.
- Estimate tokens deterministically (`ceil(unicode_scalars / 4)`); no tokenizer, provider or network dependency. Document it as an estimate, not billing-grade metering.
- Add a read-only, content-free `GET /v1/usage` endpoint exposing configured limits, current-window consumption, remaining budget, seconds until reset and lifetime counts of budget findings, and show it as a "Usage and budget" panel on the dashboard overview.
- Ship policies that demonstrate the settings: baseline and semantic-demo policies enable the control with generous limits; a new `config/policy-evaluation.yaml` enables every control with small limits so an evaluator can exceed them in seconds.
- Add `scripts/evaluate_gateway.py`, a dependency-light evaluator harness that drives a running gateway through allowed, redacted, blocked, bypass-attempt and budget-exhaustion cases and prints a PASS/FAIL table with a non-zero exit code on failure.
- Add adversarial unit/integration tests: allowed, exact-boundary, over-limit, window reset, unicode/non-BMP size, concurrency without over-admission, shadow mode and fail-closed misconfiguration.

Out of scope: per-principal or authenticated budgets (there is no verified identity), output-token or monetary-cost accounting from model metadata, persistence of counters across restart, distributed/shared counters, policy hot reload, short-circuiting expensive controls after a budget breach, a new HTTP status code for budget blocks, and new demo scenario cards. These are listed in design.md as deferred decisions.

## Capabilities

### New Capabilities

- `usage-budget-governance`: the control, its findings, window/charging semantics, usage endpoint, dashboard panel and evaluator harness.

### Modified Capabilities

- `policy-decisions`: optional validated `limits` configuration for `usage-budget`, included in the digest; every selected policy gains an explicit `usage-budget` entry.

## Impact

Touches shared integration hotspots, so one primary agent owns the whole change and no parallel change may edit them concurrently: `policy.py` (limits schema and digest), `composition.py` (registration and startup binding, mirroring semantic threshold binding), `api.py` (usage route), `reporting_api.py`-style projection for the usage DTO, dashboard assets, policy files under `config/`, and `docs/`. New files: `usage_control.py`, `scripts/evaluate_gateway.py`, tests. Reporting schema stays version 2; budget findings flow through existing finding-code reporting unchanged. Default registry expansion invalidates old policy files until they add a `usage-budget` entry (explicit migration, no implicit default), consistent with previous control additions.

Challenge grounding: `docs/requirements/challenge-requirements.md` — budget and resource governance, sample configuration "budget rules", resource-consumption dashboard metrics, evaluator "exceed configured budgets". Update `docs/requirements/traceability.md` to PARTIAL (input-token and request-rate budgets only) after accepted implementation; do not claim monetary spend, compute-time or output-token governance.

The user instruction (2026-10-04) "dorób jeszcze jeden feature, który będzie powiązany z control usage" requests this feature but is not approval to apply: explicit approval of the reviewed artifacts is required before implementation.
