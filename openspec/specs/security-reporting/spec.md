# security-reporting Specification

## Purpose

Provide durable, privacy-safe security and operational evidence with accurate invocation accounting, bounded local queries for security teams and management.

## Requirements

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
Reporting SHALL store only schema-versioned allowlisted identities, timestamps, actions, fixed reason/error codes, enablement, finding counts, invocation status and finite nonnegative durations. It MUST exclude prompts, redacted content, output, matched values, spans, snippets, content hashes, credentials, URLs, raw exceptions and arbitrary metadata. There SHALL be no content-capture option in this capability.

#### Scenario: Sensitive data under every action
- **WHEN** real detectors evaluate credentials, email, SSN and attack content under ALLOW, REDACT and BLOCK mappings
- **THEN** database rows, reporting logs and queries contain only the allowlisted metadata and none of the submitted values or derived content

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
- **THEN** queries report unknown, never succeeded, failed or certainly invoked, and restart performs no replay

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
The system SHALL provide a typed in-process API for ascending sequence-paginated
event listing, UUID detail lookup and summaries. Filters SHALL support paired UTC
half-open time ranges, action, target and invocation status. Exact input types and
bounds MUST be validated and SQL values parameterized. Lists SHALL cap at 1000;
summaries SHALL require a range at most 31 days. No reporting HTTP endpoint,
operator CLI or export SHALL be introduced by this change.

#### Scenario: Pagination and validation
- **WHEN** callers list filtered events and advance a sequence cursor
- **THEN** matching safe records return without duplicates; invalid types, ranges, enums, cursors or SQL-like target IDs yield fixed errors without reflection

#### Scenario: Detail and no matches
- **WHEN** a valid UUID or historical target has no matching event
- **THEN** detail returns None or listing returns empty distinctly from storage failure

### Requirement: Accurate security and management summaries
Summaries SHALL report distinct interaction totals, per-action counts, operational
failure totals, invocation status counts, per-producer/code finding occurrence and
affected-interaction counts, and timing sample counts/sums/min/max/means. Optional
grouping SHALL support action and target_id with a 1000-group cap. Child joins MUST
NOT multiply totals; unknown/not_invoked SHALL NOT supply invocation timings.

#### Scenario: Multi-finding fixture
- **WHEN** a fixture includes all actions, repeated/multiple findings, operational failure and succeeded/failed/unknown/not_invoked outcomes
- **THEN** totals match distinct events and finding multiplicity, operational failures are not BLOCK, and invocation samples count only completed calls

#### Scenario: Empty range
- **WHEN** a valid range selects no events
- **THEN** counts are zero and timing extrema/means are null

### Requirement: Safe local storage lifecycle
Default startup SHALL require writable file-backed SQLite storage, create new
storage with private local defaults and close owned resources at shutdown.
In-memory/URI destinations, symlink database destinations and incompatible schemas
MUST be rejected. Operators SHALL administer existing directory permissions and
backups. Runtime database/sidecar files MUST be excluded from Git. No retention,
deletion, historical import or exhaustive platform hardening is required.

#### Scenario: Startup and shutdown
- **WHEN** a new store is opened and later closed and reopened
- **THEN** committed safe history survives with no replay, and unavailable storage fails startup with sanitized errors
