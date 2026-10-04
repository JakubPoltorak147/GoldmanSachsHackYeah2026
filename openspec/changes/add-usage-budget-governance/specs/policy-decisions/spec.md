# Spec Delta

## ADDED Requirements

### Requirement: Strict usage budget limits policy
Policy SHALL accept an optional `limits` mapping only on the `usage-budget` control. It SHALL contain exactly integer keys window_seconds (1–86400), max_requests (1–1,000,000), max_estimated_tokens (1–100,000,000) and max_request_tokens (1–4096). Booleans, floats, strings, unknown or missing keys, and `limits` on any other control SHALL fail startup with sanitized PolicyError. An enabled `usage-budget` entry SHALL require limits and mappings for every budget code; a disabled entry MAY omit them but supplied values SHALL still be validated. Normalised limits SHALL be included in the policy digest. Policy SHALL reject REDACT for budget codes even when disabled. Every selected policy SHALL contain an explicit `usage-budget` entry; no implicit default is added.

#### Scenario: Valid limits
- **WHEN** an enabled usage-budget entry has all four integer limits and three mappings
- **THEN** startup succeeds, the control is bound with those limits and the digest differs from the same policy with another limit

#### Scenario: Invalid limits fail closed
- **WHEN** limits are missing for an enabled entry, contain an unknown key, a boolean, a float, a zero or an out-of-range value, or appear on another control
- **THEN** startup fails with sanitized PolicyError and no fallback policy is used

#### Scenario: Budget REDACT rejected
- **WHEN** a budget finding code is mapped to REDACT
- **THEN** startup fails even when the control is disabled

#### Scenario: Old policy migration
- **WHEN** a policy without a usage-budget entry is loaded against the expanded default registry
- **THEN** startup fails until an explicit entry (possibly disabled) is added
