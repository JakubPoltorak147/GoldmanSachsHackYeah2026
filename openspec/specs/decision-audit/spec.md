# decision-audit Specification

## Purpose
Decision auditing records safe, structured evidence of control-layer evaluation before eligible requests can be dispatched to the local target.

## Requirements

### Requirement: Pre-dispatch decision event
The service SHALL produce a structured audit event for each completed evaluation and MUST emit it before any eligible target call.

#### Scenario: Allowed or redacted decision
- **WHEN** an interaction receives an `ALLOW` or `REDACT` decision
- **THEN** its decision event is emitted before the target is called and records the final action and forwarding eligibility

#### Scenario: Blocked decision
- **WHEN** an interaction receives a policy `BLOCK` decision
- **THEN** its decision event records the `BLOCK` action and the target is never called

#### Scenario: Safe event fields
- **WHEN** an interaction containing an email address is evaluated
- **THEN** its audit event contains an interaction ID, timestamp, target ID, policy identifier or digest, evaluated controls and explicit enabled/disabled control status, action, safe finding codes and counts, forwarding eligibility, and evaluation duration, while containing no content, matched values, snippets, content hashes, source spans, or raw exception text

#### Scenario: Concurrent decision records
- **WHEN** two interactions are evaluated concurrently
- **THEN** each successful decision emission produces a separate complete, parseable audit event before its corresponding target call

### Requirement: Audit-gated dispatch
The service MUST NOT dispatch an interaction to the target when emitting its decision audit event fails.

#### Scenario: Audit sink failure
- **WHEN** the audit sink fails to emit an `ALLOW` or `REDACT` decision event
- **THEN** the service returns a sanitized `503` service response and makes zero target calls

#### Scenario: Target failure after audit
- **WHEN** the target fails after a decision event has been emitted
- **THEN** the already emitted decision event remains a decision record and does not claim that target execution succeeded

### Requirement: Operational failure records
Internal evaluation failures MUST remain distinct from security findings and policy decisions; any operational record emitted for such a failure MUST contain only safe structured information.

#### Scenario: Evaluation exception
- **WHEN** evaluation fails before a policy decision can be completed
- **THEN** the service makes zero target calls and emits only safe operational information when the audit sink is available, without creating a security Finding or claiming a policy `BLOCK`
