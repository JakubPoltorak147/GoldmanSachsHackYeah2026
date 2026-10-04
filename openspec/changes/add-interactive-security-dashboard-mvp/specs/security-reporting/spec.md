# Spec Delta

## MODIFIED Requirements

### Requirement: Bounded local reporting queries
The system SHALL provide a typed in-process API for ascending sequence-paginated
event listing, UUID detail lookup and summaries, plus bounded descending listing
for recent events with an exclusive before-sequence cursor. Filters SHALL support
paired UTC half-open time ranges, action, target and invocation status. Exact input
types and bounds MUST be validated and SQL values parameterized. Typed lists SHALL
cap at 1000; summaries SHALL require a range at most 31 days. A read-only HTTP
summary/list/detail boundary SHALL be provided; no operator CLI or export is required.

#### Scenario: Pagination and validation
- **WHEN** callers list filtered events and advance a sequence cursor
- **THEN** matching safe records return without duplicates; invalid types, ranges, enums, cursors or SQL-like target IDs yield fixed errors without reflection

#### Scenario: Detail and no matches
- **WHEN** a valid UUID or historical target has no matching event
- **THEN** detail returns None or listing returns empty distinctly from storage failure

#### Scenario: Recent-first bounded query
- **WHEN** callers request recent events and then an older page using the previous last sequence
- **THEN** results descend by sequence, the cursor is exclusive, newly inserted events do not duplicate older pages, and existing ascending listing remains unchanged

## ADDED Requirements

### Requirement: Minimal read-only reporting HTTP boundary
The system SHALL expose versioned GET summary, recent-events and UUID-detail routes using typed safe query results. Responses MUST use closed content-free schemas, no-store caching and existing historical attribution. Reporting reads MUST NOT invoke controls/targets, write history or weaken dispatch gates. Unknown fields and arbitrary metadata MUST NOT be serialized.

#### Scenario: Summary and detail projection
- **WHEN** HTTP clients read recorded mixed decisions, failures, findings and semantic observations
- **THEN** responses expose accurate existing counts, timings, identities, control status and invocation outcomes without input/output, scores, raw semantic responses or exception text

#### Scenario: Read-only methods
- **WHEN** a caller attempts POST, PUT, PATCH or DELETE on reporting routes
- **THEN** a fixed 405 is returned and no history or enforcement configuration changes

### Requirement: Bounded HTTP filters and sanitized errors
Summary/list SHALL accept paired UTC ranges bounded to 31 days or default last 24 hours, action, target and invocation-status filters. Lists SHALL cap at 100 with bounded positive cursors. Invalid/unknown/repeated query parameters MUST return fixed 422 invalid_reporting_query; missing detail MUST return 404 not_found; failed reads MUST return 503 reporting_unavailable without reflected input or fabricated totals.

#### Scenario: Invalid requests and no reflection
- **WHEN** requests contain a single time bound, excessive/reversed/non-UTC range, invalid enum/UUID/cursor, duplicate/unknown parameter or SQL-shaped identifier
- **THEN** they return the fixed validation envelope without submitted text, SQL execution side effects or target calls

#### Scenario: Unavailable queries versus empty history
- **WHEN** storage read fails or a successful query selects no events
- **THEN** failure is a sanitized 503 while legitimate empty results contain zero counts and null timing means/extrema

### Requirement: Reporting health and outcome meaning
The HTTP summary SHALL expose existing fixed write-gate health separately from read availability and target status. Succeeded/failed/unknown/not_invoked and semantic attempt status MUST retain their existing meanings. Missing completion MUST NOT prove invocation, and semantic failure MUST remain operational with no policy action or findings.

#### Scenario: Completion persistence and write health
- **WHEN** an eligible target outcome is obtained but completion persistence fails
- **THEN** readable summary exposes unhealthy write-gate status and existing durable evidence only, with absent completion remaining unknown and no target retry
