# Spec Delta

## Purpose

Policy decisions combine control findings under one validated startup configuration and determine whether original, redacted, or no content may reach a target.

## ADDED Requirements

### Requirement: Strict startup policy
The service MUST load and validate policy before accepting interactions. Invalid policy MUST prevent startup rather than disabling or weakening enforcement.

#### Scenario: Valid explicit mapping
- **WHEN** policy enables the email control and explicitly maps its finding code to a supported action
- **THEN** the service starts with that mapping available for decisions

#### Scenario: Invalid policy configuration
- **WHEN** policy contains malformed syntax, duplicate keys, unknown fields or controls, an unsupported action, or a missing mapping for an enabled control's finding code
- **THEN** the service rejects startup

#### Scenario: Disabled control
- **WHEN** valid policy explicitly disables the email control
- **THEN** that control is not evaluated and its disabled state is observable in the decision audit event

### Requirement: Central action resolution
The decision engine SHALL map findings to actions using policy and SHALL apply `BLOCK` over `REDACT` over `ALLOW`. No findings SHALL produce `ALLOW`.

#### Scenario: No findings
- **WHEN** enabled controls return no findings
- **THEN** the final decision is `ALLOW`

#### Scenario: Same finding, different policies
- **WHEN** the same email finding is evaluated under policies mapping its code to `ALLOW`, `REDACT`, and `BLOCK` respectively
- **THEN** each policy produces its configured action with a structured explanation of the finding and applied rule

#### Scenario: Mixed actions
- **WHEN** one finding maps to `BLOCK` and another maps to `REDACT`
- **THEN** the final decision is `BLOCK` and zero target calls occur

#### Scenario: Unmapped runtime finding
- **WHEN** a control produces a finding code that the active policy cannot resolve
- **THEN** evaluation fails closed as an internal service failure, without turning that failure into a security Finding or calling the target

### Requirement: Central redaction
For a `REDACT` decision, the service SHALL replace spans selected by policy with `[REDACTED]` before forwarding, using offsets into the original text.

#### Scenario: Selected spans only
- **WHEN** findings mapping to both `ALLOW` and `REDACT` exist and no finding maps to `BLOCK`
- **THEN** only spans from `REDACT` findings are replaced before the target receives the text

#### Scenario: Multiple and overlapping spans
- **WHEN** selected spans are multiple or overlapping
- **THEN** every selected portion is masked exactly once without exposing text because of shifted offsets

#### Scenario: Invalid required span
- **WHEN** a `REDACT` finding has no valid source span
- **THEN** evaluation fails closed as an internal service failure and makes zero target calls
