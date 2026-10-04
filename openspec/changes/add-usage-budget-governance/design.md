# Design

## Context

Controls are stateless evaluators registered in `ControlRegistry`; central policy maps finding codes to actions; the service runs every enabled control on the original input and the decision engine resolves `BLOCK > REDACT > ALLOW`. Semantic thresholds are the one precedent for per-control numeric configuration (`ControlPolicy.semantic_threshold`, `bind_semantic_policy`). There is no authenticated principal, so a budget can only be scoped to the whole gateway process.

## Decisions

1. **Budget enforcement is a control, not a service special case.** `usage-budget` follows the existing contract: it returns spanless findings, policy maps them, audit and reporting record them with no schema change. This keeps "Every BLOCK decision explainable through structured findings" true and keeps the core free of budget logic.
2. **Limits live in policy.** `controls.usage-budget.limits` holds integers `window_seconds` (1–86400), `max_requests` (1–1,000,000), `max_estimated_tokens` (1–100,000,000) and `max_request_tokens` (1–4096, the maximum content size is 16,384 scalars = 4096 estimated tokens). Unknown or missing keys, booleans, floats, and `limits` on any other control fail startup. Enabled control requires `limits`; a disabled entry may omit them but supplied values are still validated. Limits enter the canonical digest, so changing a limit changes the digest and is visible in audit. Policy remains startup-fixed (no reload), consistent with the current system.
3. **Fixed window, in-memory counters, injectable monotonic clock.** One lock-protected window `{start, requests, tokens}`. When `now - start >= window_seconds` the window resets. A fixed window is O(1), deterministic under test and easy for an evaluator to reason about; the boundary-burst weakness (up to 2× at a window edge) is documented rather than hidden. Counters reset on restart; persistence is deferred.
4. **Charging semantics.** Every request that reaches the control is charged (attempt-based), including requests later blocked by another control, because they still consume inspection compute. Evaluation is atomic: compute `requests+1 > max_requests`, `tokens+estimate > max_estimated_tokens`, `estimate > max_request_tokens` against current counters, then charge. A request can raise several findings. Consequence: a breached window stays breached until reset, which is the expected rate-limit behaviour.
5. **Token estimate.** `estimate = ceil(len(content) / 4)` over Unicode scalars (the interaction content is already validated). It is a documented heuristic with no tokenizer dependency; the same value is used for enforcement and reporting so evaluators can predict it exactly.
6. **Shadow mode.** Mapping a budget code to `ALLOW` records the finding without blocking, letting an operator observe consumption before enforcing. Counters still advance.
7. **Evaluation order and cost.** The control is registered after the six deterministic detectors and before semantic-security (cheap before expensive). The existing "no early BLOCK shortcut" rule is retained, so a budget breach does not currently skip the semantic evaluator. Short-circuiting expensive controls after an admission failure would change the service/decision contract and is deferred to a separate change; this is stated so evaluators do not assume it.
8. **Status code.** Budget BLOCK reuses 403 with a `budget.*` finding code, preserving the response envelope and status mapping. A 429 mapping is deferred because it changes the public contract.
9. **Usage endpoint.** `GET /v1/usage` returns a closed, no-store, content-free DTO: `enabled`, `window_seconds`, `resets_in_seconds`, `requests {used, limit}`, `estimated_tokens {used, limit}`, `max_request_tokens`, and `breaches {request_limit, token_limit, request_size}` lifetime counts since startup. When disabled it returns `enabled: false` and no limits. Query parameters, other methods and failures return fixed sanitized errors consistent with reporting routes. Reading never charges the budget. The dashboard polls it with the existing visibility-aware loop and shows meters with textual values, not colour only.
10. **Evaluator harness.** `scripts/evaluate_gateway.py` uses only `httpx` (already a runtime dependency) against `--base-url` (loopback default) with target `local-echo`, so no model is needed. Cases: benign ALLOW, email REDACT, bearer/PEM/GitHub/attack BLOCK, near-miss ALLOW, bypass attempts (encoded, spaced and case-varied variants documented as unsupported must be reported as expected ALLOW-with-limitation, not hidden), oversize request BLOCK, burst exhaustion, window recovery when `--wait-reset` is given. It prints case ID, expected, observed and PASS/FAIL, never prints payloads that look like secrets beyond fixed synthetic fixtures, and exits non-zero on any mismatch. It reads `/v1/usage` to pick burst size so it adapts to the active policy.
11. **Provider independence.** No provider calls, no new dependencies. The evaluator harness and tests run with local echo.

## Assumptions needing approval

- "control usage" is interpreted as the challenge's budget and resource governance area (token/request budgets), not authentication or authorization.
- Global (process-wide) scope is acceptable because no verified principal exists.
- Input-token estimate by character count is acceptable for a first budget; output-token and monetary cost accounting are deferred.
- Default policies gain generous limits (120 requests / 60 s, 60,000 estimated tokens / 60 s, 4096 per request) so existing behaviour and tests are unaffected; the evaluation policy uses 10 requests / 60 s, 2,000 tokens / 60 s, 400 per request.
- 403 is retained for budget blocks.

## Risks and mitigations

- Shared hotspots (`policy.py`, `composition.py`, `api.py`): single owner, no parallel change; digest/compat tests updated deliberately, historical digest tests keep injecting their original registry.
- Concurrency: one lock around check-and-charge; a test sends N concurrent requests and asserts admitted ≤ limit.
- Clock: injected monotonic clock; tests never sleep.
- Misconfiguration silently disabling enforcement: strict validation, enabled-requires-limits, fail startup, no fallback.
- Privacy: usage DTO and audit contain counts only; no content, no estimates per request in audit beyond finding codes.

## Acceptance criteria

All spec scenarios pass; exact boundary (limit-th request admitted, limit+1 rejected); window reset restores admission; shadow mode never blocks but reports breaches; 16,384-scalar input estimates 4096 tokens; non-BMP characters count as one scalar; concurrent burst never over-admits; invalid limits fail startup; `scripts/evaluate_gateway.py` returns exit 0 against the evaluation policy and non-zero when a control is disabled; dashboard panel renders enabled, disabled and unavailable states; full unit/integration/browser/Ruff/OpenSpec checks and fresh independent correctness and security reviews return PASS.
