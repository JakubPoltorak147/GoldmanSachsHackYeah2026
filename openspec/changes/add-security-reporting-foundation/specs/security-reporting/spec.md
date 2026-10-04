# Security Reporting Delta

## Purpose

Provide durable, privacy-safe security and operational evidence with accurate invocation accounting, bounded local queries and portable audit exports for security teams and management.

## ADDED Requirements

### Requirement: Durable interaction evidence
The system SHALL persist each successfully audited decision or operational evaluation event in local durable storage. Event data and related control/finding counts MUST commit atomically. History SHALL survive application restart. Duplicate interaction events, orphan outcomes and incompatible schemas MUST be rejected without destructive recovery or memory-only fallback.

#### Scenario: All enforcement actions
- **WHEN** separate interactions receive ALLOW, REDACT and BLOCK
- **THEN** storage retains each action, safe reason, policy digest, trusted identities, findings/counts and control status; ALLOW/REDACT invoke once only after required audit succeeds, and BLOCK invokes zero times

#### Scenario: Restart and concurrency
- **WHEN** concurrent requests persist records and the application restarts using the same storage
- **THEN** each committed record remains complete, separately queryable and attributable to its own server-generated interaction ID

#### Scenario: Evaluation failure
- **WHEN** a control throws or supplies an invalid finding and operational auditing is available
- **THEN** storage records a safe operational event with no policy action or findings and no target invocation

#### Scenario: Incompatible or unavailable storage
- **WHEN** startup cannot initialize the configured store or finds an unsupported schema
- **THEN** startup fails with a fixed sanitized reporting error and preserves existing data without permissive fallback

### Requirement: Closed content-free reporting schema
Reporting SHALL store and export only schema-versioned allowlisted identities, timestamps, actions, fixed reason/error codes, enablement, finding counts, invocation status and finite nonnegative durations. It MUST exclude prompts, redacted content, output, matched values, spans, snippets, content hashes, credentials, URLs, raw exceptions and arbitrary metadata. There SHALL be no content-capture option in this capability.

#### Scenario: Sensitive data under every action
- **WHEN** real detectors evaluate credentials, email, SSN and attack content under ALLOW, REDACT and BLOCK mappings
- **THEN** database rows, reporting logs and exports contain only the allowlisted metadata and none of the submitted values or derived content

#### Scenario: Output and exception canaries
- **WHEN** target output, adapter/control exceptions or provider metadata contain sensitive canaries
- **THEN** reporting stores no canaries, raw output, exception strings or provider metadata on success or failure paths

#### Scenario: Unsafe scalar metadata
- **WHEN** a reporting record has unknown fields, numeric booleans, invalid enums, negative/nonfinite durations or malformed IDs
- **THEN** it is rejected with a fixed sanitized error before any part enters reporting state

### Requirement: Trusted reporting attribution
Reporting identities SHALL derive from retained startup registrations and validated findings. Code ownership, enablement, mapped actions, target/model binding and policy digest MUST be validated against the bound metadata before persistence. Historical records SHALL retain their original attribution after configuration changes. Unresolved targets MUST use only reserved safe metadata.

#### Scenario: Forged producer or finding code
- **WHEN** an evaluator or injected reporting event asserts an unknown producer/code or another producer's code
- **THEN** no forged identifier enters reporting state, no eligible target is invoked, and operational evidence excludes the supplied strings

#### Scenario: Well-formed but unregistered identifiers
- **WHEN** an ingestion record contains syntactically valid but unregistered control, target or model identifiers
- **THEN** it is rejected rather than accepted on syntax alone

#### Scenario: Safe unresolved target
- **WHEN** an internal unknown target contains sensitive text
- **THEN** any stored operational event uses unresolved with no model/action/findings and contains none of the supplied text

#### Scenario: Configured model and historical binding
- **WHEN** a registered model target has trusted startup model metadata and a later deployment changes its configured model
- **THEN** each event retains its own startup-bound model identity; targets without model metadata use null, and runtime response assertions cannot rename either identity

### Requirement: Distinct invocation status and latency
Reporting SHALL distinguish succeeded, failed, unknown and not_invoked independently of policy action. Only a valid completed adapter result SHALL establish succeeded; invocation exception/invalid result SHALL establish failed with target_failed. Eligible decisions without completion evidence SHALL remain unknown. Evaluation, invocation and total durations SHALL have distinct documented measurement boundaries.

#### Scenario: Target success and failure
- **WHEN** audited ALLOW/REDACT invocations respectively return a valid result or fail
- **THEN** separate completion evidence records succeeded or failed with invocation/total durations, leaving the original action and decision event unchanged

#### Scenario: No invocation
- **WHEN** an interaction is BLOCKed or fails evaluation
- **THEN** its invocation status is not_invoked and no inference duration is fabricated

#### Scenario: Interrupted execution
- **WHEN** execution stops after a durable eligible decision but before a durable completion
- **THEN** queries/export report unknown, never succeeded, failed or certainly invoked, and restart performs no replay

### Requirement: Reporting failures preserve enforcement
Required reporting failure before dispatch MUST return sanitized audit failure and make zero target calls. Completion persistence failure MUST preserve the original target outcome without retry, mark reporting unhealthy and close later dispatch gates in that process. Failed queries MUST return sanitized errors instead of fabricated empty data or totals. No reporting failure SHALL become a security finding or policy BLOCK.

#### Scenario: Write or commit failure before invocation
- **WHEN** required storage fails while committing an eligible decision
- **THEN** the service returns existing audit_failed/503, invokes zero times, leaves no partial event and refuses later dispatch through the poisoned gate; a fully committed event whose acknowledgment failed remains evidence of eligibility only

#### Scenario: Completion write failure
- **WHEN** persistence fails after successful or failed invocation
- **THEN** the original 200/502 outcome is preserved, the adapter is never retried, health exposes only a fixed failure code and subsequent gate attempts fail closed; absent durable completion is unknown, while an already committed completion remains authoritative

#### Scenario: Committed completion followed by error
- **WHEN** completion persistence commits and then raises before acknowledging success
- **THEN** the committed succeeded/failed outcome remains queryable, the gate is poisoned, the target response is preserved and no evidence is deleted or invocation retried

#### Scenario: Read failure
- **WHEN** a query encounters storage failure
- **THEN** it returns reporting_unavailable without exception details or false zeros, and a read-only failure alone does not disable healthy writes

#### Scenario: Existing audit failure
- **WHEN** upstream audit emission short-writes, throws or fails to flush
- **THEN** no target is invoked, existing permanent sink poisoning remains effective and no reporting row claims successful required auditing

### Requirement: Bounded local reporting queries
The system SHALL provide an operator-local typed API for paginated event history, interaction lookup and summaries filtered by time, action, target/model, policy, control/finding, invocation status and operational error. Inputs MUST be strictly validated and SQL values parameterized. No reporting HTTP endpoint SHALL be exposed. Lists SHALL cap at 1000 records; summaries SHALL require a half-open UTC range of at most 31 days and cap grouped results at 1000.

#### Scenario: Filtered pagination and detail
- **WHEN** an operator filters by BLOCK, target and finding code, then advances the sequence cursor
- **THEN** only matching records are returned in ascending sequence without duplicate records; detail lookup returns the same safe evidence

#### Scenario: Query validation and injection
- **WHEN** callers submit malformed ranges/cursors, unsupported grouping, over-limit pages, unknown options or SQL-like identifier strings
- **THEN** queries return fixed validation errors without reflecting the input or executing caller-selected SQL

#### Scenario: Historical identifier without matches
- **WHEN** a syntactically valid historical identifier has no rows in the selected range
- **THEN** a successful query returns an empty result distinctly from reporting_unavailable

### Requirement: Accurate security and management summaries
Summaries SHALL report interaction totals, per-action decision counts, operational failures, invocation status counts, finding occurrences/distinct affected interactions and duration sample statistics. Supported grouping SHALL be action, target/model, policy, control, finding code or UTC day. Joins MUST NOT multiply interaction totals. Operational failures MUST NOT count as BLOCK; unknown completion MUST NOT count as success/failure.

#### Scenario: Known multi-finding fixture
- **WHEN** a fixture contains ALLOW/REDACT/BLOCK, repeated findings, multiple producers, disabled controls, operational failure, successful/failed invocation and unknown completion
- **THEN** filtered and grouped counts exactly match the known distinct interactions and finding multiplicities; completed-only invocation timing samples exclude unknown and not_invoked

#### Scenario: Control and finding filter semantics
- **WHEN** control/finding filters and grouping are applied
- **THEN** control selection uses explicit plan-status membership including disabled controls, finding selection requires a matching occurrence, combined control/code filters require the same producer, and occurrence totals include only matching findings; decision/outcome totals use distinct selected interactions and detail/export retains complete safe evidence

#### Scenario: Null model and empty range
- **WHEN** a summary includes echo events without model IDs or a valid range with no events
- **THEN** missing identity uses a null bucket, empty counts are zero, and absent timing samples have null means/min/max rather than fabricated durations

#### Scenario: Group limit
- **WHEN** a query would exceed 1000 groups
- **THEN** it returns reporting_limit_exceeded rather than incomplete totals

### Requirement: Safe consistent audit export
The system SHALL export selected safe records as schema-versioned JSONL from one consistent snapshot, with a completion manifest and record count. Export MUST require a UTC range of at most 31 days, use bounded batches and owner-only local files, refuse overwrite, and publish only complete output. Storage/export diagnostics MUST exclude rejected values and exception details.

#### Scenario: Export during concurrent activity
- **WHEN** new events or completions arrive during export
- **THEN** the published export contains a consistent snapshot, a high-water sequence and complete manifest whose count matches exported records

#### Scenario: Failed or existing destination
- **WHEN** output writing fails or the destination already exists
- **THEN** export returns a fixed nonzero error, leaves the existing destination intact and publishes no apparently complete partial export

### Requirement: Private storage lifecycle
Default startup SHALL require private writable file-backed storage. Unsafe storage permissions MUST be rejected on supported platforms. Query/export CLI SHALL open existing storage read-only without creating it. Database, sidecars and exports MUST be excluded from Git and documented as operator-controlled security metadata. No automatic retention/deletion or historical import SHALL occur.

#### Scenario: Private files and shutdown
- **WHEN** the application initializes a new store and later shuts down
- **THEN** the database and sidecars are privately accessible and owned resources close without logging content or paths

#### Scenario: Read-only CLI and missing database
- **WHEN** an operator runs queries against an absent database
- **THEN** the CLI fails safely without creating a database or modifying runtime state
