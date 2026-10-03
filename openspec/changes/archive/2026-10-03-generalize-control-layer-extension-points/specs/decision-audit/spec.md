# Spec Delta

## ADDED Requirements

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
