# Spec Delta

## ADDED Requirements

### Requirement: Usage budget control
The system SHALL provide a registered deterministic `usage-budget` control evaluating, for every interaction it inspects, a request-count limit, an estimated-token limit over a fixed window and a per-request estimated-token limit. It SHALL return only spanless findings `budget.request_limit`, `budget.token_limit` and `budget.request_size`, which policy MAY map to ALLOW or BLOCK and MUST NOT map to REDACT. The control SHALL NOT choose actions.

#### Scenario: Within budget
- **WHEN** a request is below every configured limit
- **THEN** no budget finding is returned and the request is charged to the current window

#### Scenario: Exact boundary
- **WHEN** a window has max_requests N and N requests are evaluated, then an N+1th request occurs in the same window
- **THEN** the first N produce no request_limit finding and the N+1th produces exactly budget.request_limit

#### Scenario: Oversized single request
- **WHEN** a request's estimated tokens exceed max_request_tokens
- **THEN** budget.request_size is returned regardless of window consumption

#### Scenario: Token window exhaustion
- **WHEN** accumulated estimated tokens plus the current estimate exceed max_estimated_tokens
- **THEN** budget.token_limit is returned and the request is still charged

#### Scenario: Multiple breaches
- **WHEN** a request breaches several limits
- **THEN** one finding per breached limit is returned and central policy resolves them with BLOCK over ALLOW

### Requirement: Deterministic token estimate and charging
Estimated tokens SHALL equal ceil(Unicode scalar count / 4) of the exact original interaction content. Every evaluated interaction SHALL be charged atomically in the same operation that checks the limits, including interactions later blocked by other controls. Window state SHALL use a monotonic clock and reset when the elapsed time reaches window_seconds. Counters MAY be in memory and reset on restart.

#### Scenario: Estimate bounds
- **WHEN** content is 1, 4, 5 and 16,384 scalars, including non-BMP characters
- **THEN** estimates are 1, 1, 2 and 4096, counting each scalar once

#### Scenario: Window reset
- **WHEN** the configured window elapses on the injected clock
- **THEN** counters restart at zero before the next evaluation

#### Scenario: Concurrent burst
- **WHEN** many concurrent requests arrive with max_requests N
- **THEN** exactly N are admitted by the control and the remainder receive budget.request_limit

### Requirement: Central enforcement and observe mode
Budget findings SHALL be resolved by the existing central policy and decision engine. A BLOCK mapping SHALL produce the existing BLOCK outcome with zero target calls, 403 status and structured finding codes. An ALLOW mapping SHALL record the finding in audit and reporting without blocking while still advancing counters.

#### Scenario: Enforced budget block
- **WHEN** a budget finding is mapped to BLOCK
- **THEN** the response is 403 with the budget finding code, the target is not invoked and audit/reporting record the decision and counts without content

#### Scenario: Observe-only mapping
- **WHEN** a budget finding is mapped to ALLOW
- **THEN** the request is forwarded under existing rules and the finding is still recorded

### Requirement: Read-only usage endpoint
`GET /v1/usage` SHALL return a closed, no-store, content-free JSON object with enabled, window_seconds, resets_in_seconds, requests {used, limit}, estimated_tokens {used, limit}, max_request_tokens and lifetime breach counts per budget code since startup. A disabled control SHALL report enabled false without limits. Reading SHALL NOT charge or mutate counters. Query parameters, unsupported methods and unavailable service SHALL return fixed sanitized errors without reflecting input.

#### Scenario: Usage snapshot
- **WHEN** three requests of known size have been processed in an enabled window
- **THEN** the endpoint reports used requests 3, the exact estimated token sum, configured limits and a non-negative reset time, and a second read returns the same usage

#### Scenario: Disabled or invalid access
- **WHEN** the control is disabled, a query parameter is supplied or a non-GET method is used
- **THEN** respectively enabled false, fixed 422/invalid_request or fixed 405/method_not_allowed is returned with no-store

### Requirement: Usage dashboard panel
The dashboard overview SHALL show a Usage and budget panel derived only from the usage endpoint, presenting used, limit, remaining and reset time as text with meters, and labelled disabled, stale and unavailable states without removing existing overview evidence.

#### Scenario: Panel states
- **WHEN** the endpoint reports enabled, disabled or fails
- **THEN** the panel shows meters with numeric text, a disabled label, or the last successful values marked stale

### Requirement: Evaluator harness
The repository SHALL provide `scripts/evaluate_gateway.py` which drives a running gateway at a loopback base URL using local echo only, runs allowed, transformed, blocked, documented-limitation and budget-exhaustion cases, prints case ID/expected/observed/PASS-FAIL, exits non-zero on any mismatch, and requires no model runtime or external service.

#### Scenario: Passing evaluation
- **WHEN** the harness runs against the evaluation policy
- **THEN** every case passes and the exit status is zero

#### Scenario: Detected misconfiguration
- **WHEN** an expected control is disabled or a budget limit is absent
- **THEN** the corresponding case reports FAIL and the exit status is non-zero

### Requirement: Safe and adversarial verification
Automated tests SHALL cover allowed, clearly over-limit, exact-boundary, window-reset, non-BMP, multi-breach, concurrent, shadow-mode and invalid-configuration cases, and SHALL verify that audit, reporting, usage output and errors contain no submitted content.

#### Scenario: Privacy canary
- **WHEN** a canary string is submitted and a budget block occurs
- **THEN** the canary appears in no audit event, reporting record, usage response or error
