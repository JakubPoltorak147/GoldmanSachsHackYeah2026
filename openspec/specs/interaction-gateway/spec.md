# interaction-gateway Specification

## Purpose
The interaction gateway accepts bounded text requests and exposes policy decisions while forwarding only content that the control layer has approved for the selected local target.

## Requirements

### Requirement: Validated text interaction
The gateway SHALL accept a text interaction for the fixed local echo target, assign its identifier on the server, and reject invalid requests without forwarding them.

#### Scenario: Valid request
- **WHEN** a caller submits a valid nonempty text string of at most 16,384 characters for the local echo target
- **THEN** the gateway assigns an interaction ID and evaluates that exact text without trimming or normalization

#### Scenario: Maximum content length
- **WHEN** a caller submits content of exactly 16,384 characters
- **THEN** the gateway accepts it for evaluation

#### Scenario: Over-limit content
- **WHEN** a caller submits content of 16,385 characters
- **THEN** the gateway returns a sanitized validation response and makes zero target calls

#### Scenario: Invalid request shape
- **WHEN** a caller submits missing fields, unknown fields, a wrong type, or empty content
- **THEN** the gateway returns a sanitized validation response without reflecting submitted content and makes zero target calls

#### Scenario: Malformed JSON
- **WHEN** a caller submits malformed JSON containing sensitive text
- **THEN** the gateway returns a sanitized validation response without reflecting the body and makes zero target calls

#### Scenario: Invalid Unicode scalar
- **WHEN** a caller submits content containing a lone surrogate through a JSON escape
- **THEN** the gateway returns a sanitized validation response and makes zero target calls

#### Scenario: Untrusted destination or identity
- **WHEN** a caller supplies an unsupported target or a caller-asserted identity field
- **THEN** the gateway rejects the request and makes zero target calls

### Requirement: Decision-governed forwarding
The gateway SHALL forward only interactions with an `ALLOW` or `REDACT` decision and SHALL make no target call for a `BLOCK` decision.

#### Scenario: Allowed interaction
- **WHEN** policy decides `ALLOW` for a valid interaction
- **THEN** the local echo target receives the original text unchanged exactly once and the caller receives its echo result with the `ALLOW` decision

#### Scenario: Redacted interaction
- **WHEN** policy decides `REDACT` for a valid interaction
- **THEN** the local echo target receives only the centrally transformed text exactly once and the caller receives its echo result with the `REDACT` decision

#### Scenario: Blocked interaction
- **WHEN** policy decides `BLOCK` for a valid interaction
- **THEN** the gateway returns an explainable `BLOCK` response and makes zero target calls

### Requirement: Sanitized HTTP outcomes
The gateway MUST distinguish policy decisions from internal and target failures in its HTTP responses and MUST NOT expose submitted content or internal exception text in error responses.

#### Scenario: Internal evaluation failure
- **WHEN** evaluation fails because a control raises an exception, a finding span is invalid, or policy resolution is inconsistent
- **THEN** the gateway returns a sanitized `503` service response without a security Finding or policy `BLOCK` decision and makes zero target calls

#### Scenario: Target failure after eligible decision
- **WHEN** the local target fails after an `ALLOW` or `REDACT` decision has been audited
- **THEN** the gateway returns a sanitized target-failure response without exposing exception text
