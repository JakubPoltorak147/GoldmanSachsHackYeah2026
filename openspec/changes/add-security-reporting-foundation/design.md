# Design

## Context

See proposal.md for motivation. There are no active changes in the CLI inventory. The working tree already contains staged local-model archival/spec/worklog edits; this change must not alter or commit those edits.

Direct integration points inspected: `audit.py` (explicit safe fields and poisoned JSONL sink), `service.py` (one retained binding, required audit then one invocation), `targets.py` (immutable target metadata), `composition.py`, `api.py` lifespan, and frozen `OllamaSettings`. Relevant current specs are decision-audit, interaction-gateway, policy-decisions and local-model-target. No detector redesign is needed.

## Goals / Non-Goals

**Goals:** durable content-free evidence, separate enforcement and execution accounting, trusted identity attribution, bounded local queries and exports, deterministic verification without a model runtime.

**Non-Goals:** see proposal.md. In particular this is single-host storage, without an ingestion queue, general metadata dictionary, request-body capture toggle, token/cost estimation, reporting HTTP routes or new operator authentication scheme.

## Decisions

### 1. SQLite at the existing required audit boundary

Use standard-library SQLite in new flat `reporting_store.py`; safe reporting DTOs/projection/query validation live in `reporting.py`, local command handling in `reporting_cli.py`. The store implements narrowly defined append/query operations, not a generic event repository. No ORM or external service is required.

Default composition wraps the existing JSONL sink with a required persistent audit sink. For each audit event: validate a safe projection; emit and flush the existing sink; then commit the complete reporting event and children atomically. Return from `emit` only after both succeed. Thus a persisted decision proves successful JSONL emission, and invocation still follows successful required audit. Stdout and SQLite cannot be atomic together: a line can exist without a database row if persistence fails, but no target is called in that case. Do not retry emission or invocation.

Use one write lock per store, short transactions, foreign keys, WAL and synchronous FULL, with a bounded 1000 ms SQLite busy timeout. No transaction/lock spans target execution. A storage write/commit failure or upstream JSONL failure permanently poisons the composed dispatch gate for that process. Concurrent work that already passed its gate can finish; later gate attempts fail closed. Read errors do not disable policy or silently return empty data.

Alternative: best-effort database mirroring would create silent evidence gaps. Replacing stdout would discard current guarantees and compatibility. A remote database/event bus adds deployment complexity without a present requirement.

### 2. Append-only decision evidence and separate completion evidence

Proposed flow:

```text
validated interaction --> retained target --> controls --> central policy
                                                   |
                                 safe decision/operational projection
                                                   |
                                   existing JSONL write + flush
                                                   |
                                      SQLite transaction commit
                                                   |
                         BLOCK/error <-------------+--> ALLOW/REDACT
                         no invocation                   invoke once
                                                             |
                                                safe success/failure DTO
                                                             |
                                                SQLite completion commit
                                                             |
                                                   existing HTTP outcome
```

Operational evaluation failure keeps existing best-effort safe operational emission and no dispatch; it is not BLOCK. Public validation failures occur before service entry and remain outside reporting. Required audit failure can leave no database event; the process exposes a fixed reporting-health failure, never inventing a decision or an event it could not persist.

An eligible persisted decision starts with derived invocation status `unknown`; it establishes eligibility, not proof of execution. After the adapter returns a valid TargetResult, append `succeeded`; adapter exception/invalid result appends `failed` with `target_failed`. BLOCK and operational events derive `not_invoked`. Completion records never overwrite decisions or claim output safety. Crash between gate and invocation, during invocation, or before completion commit stays unknown, without restart replay.

Completion-write failure cannot undo a target call: preserve the original 200/502 response and original result semantics, do not retry, poison the gate and set in-memory reporting health to fixed `reporting_write_failed`. No stderr exception dump or recursive database error event. Future eligible dispatch attempts fail with existing `audit_failed`/503; evaluation failures retain `evaluation_failed`. A local health method reports healthy/unhealthy and a fixed code; after restart, unknown rows expose gaps, without claiming recovery of lost outcomes. Existing stdout AuditEvent shape and number of events remain unchanged; invocation records are database-only.

A write can commit and then raise before acknowledging success. Poison the gate on any reported write failure and never retry or delete evidence to simulate rollback. A gate commit followed by an error makes zero invocations for that request; any retained eligible decision stays unknown. For completion commit followed by an error, an existing durable outcome remains authoritative; unknown applies only when no completion is present. Atomicity guarantees complete committed records or no uncommitted record, not certainty that every exception rolled back. Failure tests must cover both pre-commit rollback and committed-then-error ambiguity.

Alternative: a mutable single request row obscures immutable decision evidence. Returning a new 503 after successful target execution invites caller retries and confuses target status. Transactional exactly-once execution across SQLite and arbitrary adapters is out of scope.

### 3. Closed reporting schema and identity provenance

No generic JSON metadata or serialization of Interaction, Finding, Decision, TargetResult, settings or exceptions. Projection accepts only these schema-version-1 fields:

| Record | Fields / constraints |
| --- | --- |
| Common audit event | server UUID interaction_id; event_type `decision`/`operational_failure`; UTC timestamp; retained registered target_id or reserved `unresolved`; policy_digest (64 lowercase hexadecimal); optional model_id; finite nonnegative evaluation_duration_ms |
| Decision | action ALLOW/REDACT/BLOCK; reason_code `no_findings`/`policy_resolved`; forwarding_eligible consistent with action; ordered evaluated_controls; explicit boolean control_status; finding counts by trusted producer and code, with centrally mapped action |
| Operational failure | fixed `evaluation_failed`; action/reason null; no finding rows; forwarding false; only controls whose outputs already validated and bound enablement |
| Invocation outcome | matching interaction_id; UTC completed_at; status `succeeded`/`failed`; error_code null/`target_failed` respectively; finite nonnegative invocation_duration_ms and total_duration_ms |

Internally use `audit_events` (one event per interaction; integer sequence for ordering), `event_controls` (status and evaluation ordinal), `event_findings` (producer, code, mapped action, positive occurrence count), and `invocation_outcomes` (at most one completion per eligible decision). Unique keys, checks and foreign keys enforce relationships. All rows for an audit event commit together. Schema version is stored explicitly; incompatible databases fail startup instead of destructive migration. Composite indexes cover timestamp/sequence, action, target, policy and finding-code joins.

The gate projection validates against the immutable startup BoundPolicy and TargetRegistry, not merely identifier regexes. Unknown producer/code, code owned by another producer, control status mismatch, invalid digest/action/count, unbound model or unknown target all fail before storage. Count projection reconstructs producer and mapped action from the bound plan's globally unique finding-code catalogue, and derives reason_code from whether validated counts are empty. It checks final-action precedence, evaluated-control membership/order and findings only from enabled evaluated producers. This reuses actual-producer validation and never stores evaluator assertions. Operational `unresolved` is allowed only without model/action/findings; caller-supplied unknown IDs are discarded by current service behavior. The store has no public ingestion API; only the bound reporting projection writes events. Service completion recording uses the same store/health gate as pre-dispatch auditing, so completion failure cannot poison an unrelated sink.

Add optional `model_id=None` to frozen TargetDefinition. Accept only a strict string matching `[a-z0-9][a-z0-9._:-]{0,127}` or None; no empty string, URLs, paths, whitespace or coercion. This is a non-sensitive, administrator-owned configured identity, not a provider assertion or evidence of actual runtime model version. Default composition loads OllamaSettings once and uses the same frozen `settings.model` for the adapter and registration. Echo/targets without explicit model metadata use null. Never inspect arbitrary adapter attributes or response metadata. The reporting sink retains the startup registry metadata; it does not resolve a target again or invoke it. Existing stdout target identity remains unchanged.

Trusted metadata is an administrative trust boundary: registration/configuration authors must use non-sensitive IDs; syntax alone is not a content sanitizer. Runtime requests, returned model names and exception strings cannot populate it. Historical events retain their recorded identities even if the next deployment changes registries; reads do not reclassify historical data using today's catalogue.

No prompts (including redacted prompts), model output, matched values, snippets, source spans, content hashes, credentials, request headers, principal assertions, URLs, arbitrary error messages or provider metadata can enter storage, export or reporting diagnostics. Numeric token/cost/resource fields are omitted because no validated source currently exists. Durations are observed using a monotonic clock; timestamps use UTC. Evaluation duration retains its current meaning, excluding persistence and inference; invocation duration includes adapter invocation and result validation; total duration runs from service entry to adapter completion, before completion persistence. These are observed timings, not timeouts or output-safety assertions.

### 4. Persistence lifecycle and access

`CONTROL_LAYER_REPORTING_DB` selects a local file, default `var/security-reporting.sqlite3`. Empty paths, in-memory/URI destinations and unsupported schema versions are rejected with a fixed startup code `invalid_reporting_configuration`; open/schema initialization failure is `reporting_unavailable`. No fallback to memory or stdout-only production. The application owns startup initialization and shutdown close; create_app gains explicit store injection through the same validated gate for tests. Sink injection continues to be the upstream audit sink, without bypassing persistence. Tests use temporary file-backed stores.

Create default parent/file with owner-only permissions on supported deployment platforms; existing storage/parent permissions must be checked and unsafe exposure rejected. Document an operator-owned private directory, filesystem permissions on DB/WAL/SHM/exports and disk backups; never show configured paths in errors. Store runtime artifacts outside Git (including WAL/SHM); reuse existing ignore patterns or add only the relevant runtime directory pattern during apply. CLI query/export opens an existing database read-only and cannot create/reset it. Local filesystem access is the authorization boundary; callers of `/v1/interactions` gain no reporting access.

No automatic deletion, retention schedule or import. Document manual operator backup/removal only while stopped. Durability follows SQLite/filesystem guarantees, not protection against malicious administrators, disk loss or disabled fsync. Backups/exports contain operational security metadata and need the same access controls.

### 5. Query, aggregation and export contract

Provide typed in-process methods and CLI equivalents:

- `list_events(filters, limit=100, after_sequence=None)` returns safe audit records with derived invocation state, sequence and schema_version, ascending sequence. Limit 1–1000; keyset cursor is an exact positive integer. Filtered detail lookup accepts a UUID interaction_id, with not-found distinct from query failure.
- `summarize(filters, group_by=None)` returns interaction_total, decision counts ALLOW/REDACT/BLOCK, operational_failure_total, invocation counts succeeded/failed/unknown/not_invoked, finding occurrence counts, affected-interaction counts, and duration sample counts/sums/min/max/means. Group-by is one of action, target_id, model_id, policy_digest, control_id, finding_code or UTC day. Null identities get an explicit null bucket. Invocation averages use completed samples only; evaluation averages use audit events. Operational rows never count as BLOCK. Per-control/finding affected counts use distinct interaction IDs, preventing multi-finding joins from multiplying decision/outcome totals; occurrence totals retain multiplicity. Grouped distinct counts across different findings need not sum to overall interaction count.
- `export_events(filters, output_path)` writes schema-versioned JSONL with the same allowlisted projection and derived invocation state. Export all matching records through bounded batches from a single consistent read transaction; append a final manifest with export UTC time, schema_version, record_count, high_water_sequence and `complete: true`. Publish an owner-only destination atomically only after success; refuse overwrite. Failure discards the temporary output, returns a fixed nonzero code and never presents a partial file as a complete export.

Filters are UTC half-open time range `[from,to)`, action, target_id, model_id, policy_digest, control_id, finding_code, invocation_status and operational error_code. Require both time bounds for summary/export, at most 31 days; list permits omitted times. Validate strict types, finite timestamps/order, identifier syntax, enumerations and reject unknown arguments. Historical well-formed IDs without matches return empty results; arbitrary SQL, provider metadata and raw request text are not filter inputs. SQL values are parameterized; grouping/sort expressions come from a closed internal enum. Page/summary group results cap at 1000; group overflow returns `reporting_limit_exceeded` rather than truncated totals. Summary returns overall totals and optionally groups; filtered sets are deduplicated before joins.

Filters combine with AND. Time selection uses audit-event timestamp, not completion time. control_id selects events containing that control's explicit plan-status row, including disabled/not-evaluated rows; finding_code selects events containing that finding. If both are supplied, they must identify the same producer/code relationship to match. Summary decision/outcome/timing totals use the distinct selected event set. Finding occurrence/affected totals include only finding rows satisfying any control/code filter; other filters select their parent events. control_id grouping attributes each event to each plan-status control, with enabled/evaluated counts and only that producer's findings; finding_code grouping uses only matching finding rows and excludes no-finding events from groups while retaining them in overall totals. Full history/detail/export preserve the complete safe evidence for each selected event rather than dropping non-matching findings. Queries with only one time bound are rejected; from must be strictly before to. No timing mean/min/max is returned for zero samples (null instead).

Each list/summary call uses its own consistent read snapshot. Export captures a high-water sequence in its single snapshot, so new events and completions cannot change that export. Long exports can retain WAL history; bound them to 31 days and document local operational cost. CLI validates without reflecting rejected values. Query failure yields `reporting_unavailable` with no fabricated zeros; query errors do not poison healthy dispatch writes unless an actual write failure occurs. Report health includes only fixed status/code; no new public endpoint.

Alternative: HTTP queries would require an operator authorization contract that the current gateway lacks. CSV creates spreadsheet formula risks and loses nested attribution; JSONL directly preserves typed safe data.

## Risks / Trade-offs

- Required local storage adds latency/availability dependency -> short commits, explicit timing, bounded lock timeout, storage failures fail closed without policy changes.
- Split stdout/database commit -> emit stdout first; no dispatch until durable commit; document stdout-only attempts and absence of cross-sink atomicity.
- Crash or completion-write failure leaves unknown outcomes -> explicit unknown accounting, no replay/retry or false success.
- Administrators can choose sensitive-looking model/registration IDs -> documented non-sensitive metadata contract, source provenance and validation; never derive identifiers from payloads.
- Database history grows -> private operator-managed storage and bounded reads/exports; no speculative retention subsystem.
- Filesystem reader can see metadata -> local operator-only API and file permissions, no unauthenticated HTTP reporting.
- Read snapshots can retain WAL -> bounded export window and documented disk monitoring; disk failure closes the dispatch gate.

## Migration Plan

After explicit APPLY approval, implement and verify through tasks.md. No historical stdout import or policy migration. Prepare private writable storage and configure its path, initialize schema v1 at startup and retain current public interaction responses and stdout fields. An unwritable path fails startup safely. Back up the store using a SQLite-consistent method before replacement. Rollback to the previous release requires stopping the service and preserving the database; the previous release will be stdout-only and provides no persistent reporting guarantee. Do not destructively downgrade schema.

## Open Questions

None requiring a product decision. Choices above are proposed scope for review/APPLY, not authorization to implement.
