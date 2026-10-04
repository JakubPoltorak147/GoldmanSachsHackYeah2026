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

### Requirement: Registration-derived audit metadata
Decision audit metadata SHALL derive target identity from the retained target binding, evaluated control identities and enablement from the startup-bound plan, and finding codes/counts from actual-producer validated findings. Evaluator assertions, adapter result metadata, and unvalidated request strings MUST NOT establish audit identity. Existing safe field selection and audit-before-dispatch guarantees SHALL remain intact.

#### Scenario: Registered targets and controls
- **WHEN** multiple registered controls evaluate interactions for distinct internal registered targets
- **THEN** each event identifies its retained target, successfully validated evaluated controls, explicit enabled/disabled states, and validated finding counts before any eligible adapter invocation

#### Scenario: Forged evaluator metadata
- **WHEN** an evaluator asserts another producer's identity or an undeclared finding code
- **THEN** no decision event is emitted for those findings, no target is called, and any operational event excludes the forged strings and security action

#### Scenario: Adapter cannot rename audit target
- **WHEN** an adapter supplies its own identity assertion or later fails
- **THEN** the prior audit event retains the registered target identity and does not claim execution success

#### Scenario: Safe default and generic records
- **WHEN** existing email findings or valid additional test-control findings are audited
- **THEN** records retain existing field names and contain no submitted content, matched values, snippets, hashes, spans, arbitrary metadata, or raw exceptions

#### Scenario: Multiple-target audit failure
- **WHEN** decision audit emission fails for an eligible interaction bound to any registered adapter
- **THEN** no adapter is invoked, and existing sink write/flush failure and permanent-poisoning guarantees remain effective

#### Scenario: Concurrent interactions
- **WHEN** interactions for different registered target bindings execute concurrently
- **THEN** each successful emission remains a separate complete parseable record before its corresponding adapter invocation

### Requirement: Safe unresolved-target operational records
An unresolved internal target SHALL produce only sanitized operational information when the sink is available, with reserved server-owned target ID `unresolved`, no policy action, no finding counts, and no dispatch. Supplied unknown target strings MUST NOT enter audit. Public unsupported-target validation SHALL retain its existing rejection behavior without creating service audit records.

#### Scenario: Sensitive unknown internal identifier
- **WHEN** an unknown internal target ID contains submitted sensitive text or a destination URL
- **THEN** any operational event uses `unresolved`, contains no supplied identifier or exception text, and records evaluation failure without a security BLOCK or target call

#### Scenario: Unavailable operational sink
- **WHEN** internal resolution fails and operational audit emission also fails
- **THEN** the service still returns a sanitized evaluation failure and invokes no target

#### Scenario: Public unsupported identifier
- **WHEN** HTTP receives an unsupported target ID
- **THEN** it returns sanitized 422 before service evaluation and emits no service audit event

### Requirement: Deterministic pack audit privacy and dispatch
Production-pack audit SHALL retain existing safe fields and expose only trusted registration-derived identities, status and finding counts. Submitted sensitive content, secret/SSN values, attack excerpts, source spans, content hashes, catalog literals and exception text MUST NOT enter records. Eligible invocation MUST follow successful required audit; BLOCK and evaluation/audit failures MUST invoke no target.

#### Scenario: Sensitive values under all actions
- **WHEN** real production detectors find supported credentials, SSNs and emails under ALLOW, REDACT and BLOCK policies
- **THEN** audit records contain appropriate trusted codes/counts/actions but no submitted values, content or spans, including ALLOW cases that intentionally forward original content

#### Scenario: Mixed findings and audit order
- **WHEN** multiple enabled pack controls contribute findings to an eligible decision
- **THEN** one complete safe decision event is emitted before the retained target's exactly-one invocation, with explicit status for every registered control

#### Scenario: Failure paths with sensitive inputs
- **WHEN** a control raises an exception containing submitted secret text, returns forged metadata, or decision audit fails
- **THEN** records/errors remain sanitized and zero target invocations occur, preserving existing sink poisoning guarantees

#### Scenario: Concurrent pack requests
- **WHEN** concurrent interactions contain different sensitive values and attack indicators
- **THEN** findings do not cross requests and each successful audit remains a separate complete parseable record before its corresponding eligible invocation

### Requirement: Durable required audit gate
Default application auditing SHALL retain existing JSON-lines emission and require successful durable safe reporting persistence before target dispatch. Storage failure SHALL fail the gate as audit_failed, with zero target calls. Existing decision fields and upstream write/flush poisoning MUST remain unchanged. There SHALL be no silent stdout-only fallback.

#### Scenario: Dual gate ordering
- **WHEN** an eligible interaction is evaluated
- **THEN** existing JSON-lines emission succeeds and its safe reporting transaction commits before the retained target is invoked once

#### Scenario: Persistence failure after stdout
- **WHEN** stdout emission succeeds but durable commit fails
- **THEN** no target is called, the service returns audit_failed, later gates fail closed and stdout evidence is not misrepresented as durable execution evidence

### Requirement: Separate reporting completion evidence
Invocation completion SHALL append separate safe reporting evidence, never modify a decision audit record or add raw output to audit. Existing stdout decision records SHALL continue to describe eligibility only. Completion-write failure MUST preserve the obtained target outcome and prevent subsequent dispatch through the unhealthy reporting gate, without retrying invocation.

#### Scenario: Successful or failed target
- **WHEN** the adapter returns a valid result or fails after required decision auditing
- **THEN** separate durable reporting evidence records the invocation outcome, while the original stdout event remains unchanged and does not claim target success

#### Scenario: Missing completion
- **WHEN** the process crashes or completion persistence fails
- **THEN** an eligible decision without durable completion remains unknown; an already committed completion remains authoritative, without a false completion claim, evidence deletion or another target call
