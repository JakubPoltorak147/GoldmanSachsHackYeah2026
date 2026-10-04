# Durable security reporting

The default HTTP application requires file-backed SQLite reporting in addition to
its existing flushed JSONL audit. Set `CONTROL_LAYER_REPORTING_DB` to a local file;
the default is `var/security-reporting.sqlite3`. There is no memory or stdout-only
fallback. New parent directories and files use 0700/0600 on POSIX. Use a trusted,
operator-owned private directory; administer permissions on existing directories,
files and backups. Symlink database destinations and SQLite URI/memory destinations
are rejected. Initialization failure raises a fixed reporting error without paths.

SQLite schema version 2 stores atomic audit events, control status, finding counts
and separate invocation outcomes. WAL, synchronous FULL and a one-second busy
timeout are enabled. Unsupported schema versions or incompatible table/constraint/trigger
definitions fail startup without migration.
The application closes its owned store at shutdown. Injected `reporting_store`
instances remain owned by the caller; `audit_sink` injection is the upstream sink
and still passes through required durable persistence.

The gate validates the projection against startup-bound policy and target
registrations, flushes stdout, then commits the complete SQLite event before
returning to the service. Persistence or upstream audit failure prevents dispatch
and permanently closes this process's gate. SQLite and stdout are separate sinks:
a line can be flushed without a committed row, but that request cannot dispatch.
No transaction spans a target invocation. Central policy still owns enforcement;
HTTP request/response schemas and policy configuration are unchanged.

## Safe schema and identity

Only server UUID/time, decision or operational type, trusted target/model identity,
policy digest, action/reason or fixed operational error, forwarding eligibility,
evaluated controls/enablement, trusted finding producer/code/action/count and
measured durations are retained. Projection derives producer and mapped action
from the bound catalogue and verifies precedence. Operational evaluation events
have no action/findings and never count as BLOCK. Unknown internal targets use
`unresolved`, with no model or caller-supplied identity.

There are no payload, metadata, span, snippet or content-hash fields. Prompts,
redacted prompts, model output, credentials, PII, exception text, URLs and provider
metadata never enter reporting. Registration authors must choose non-sensitive
identifiers: administrative metadata is trusted, and identifier syntax is not a
content sanitizer. Optional model IDs are configured deployment identity, not
proof of a provider's actual model/version. Ollama registration and adapter share
one loaded immutable setting; echo has no model ID. Historical attribution remains
unchanged when later startup registrations differ.

## Outcomes and timings

An eligible decision with no durable completion is `unknown`. A separate completion
records `succeeded` only after a valid target result, or `failed` with fixed
`target_failed` after invocation exception/invalid result. BLOCK and operational
failure are `not_invoked`. A crash before invocation or completion can leave
unknown; this does not prove that a call ran. Restart never replays calls.

Completion-write failure preserves the obtained 200/502 target outcome, never
retries the target and closes later dispatch gates. `store.health` returns
`healthy` or fixed `reporting_write_failed`. A committed outcome remains
authoritative even if its acknowledgement fails; absent completion stays unknown.
The read-only HTTP reporting summary exposes fixed write-gate health; see the reporting boundary below.

Evaluation milliseconds run from service entry through decision construction,
excluding persistence and invocation. Invocation milliseconds cover adapter call
and result validation. Total milliseconds cover service entry through adapter
completion, including the audit gate and excluding completion persistence.
Timings use a monotonic clock; timestamps use UTC. No token, cost, resource or
output-safety claims are made.

## Typed dashboard boundary

Consumers use the application's `state.reporting` (`ReportingStore`), not SQLite.
Inputs and results are frozen typed DTOs in `reporting.py`. Methods:

- `list_events(EventFilter(), limit=100, after_sequence=None)` returns a tuple of
  `EventView` in ascending sequence, including full safe event and completion.
  Limit is 1–1000; cursor is an exact positive integer.
- `get_event(UUID(...))` returns an `EventView` or `None` for no match.
- `summarize(filters, group_by=None)` returns `SummaryResult` with overall totals
  and optional action/target groups. It requires paired UTC bounds at most 31 days
  apart and caps groups at 1000. Empty windows return zero counts and null timing
  means/extrema. Storage read failures raise fixed `reporting_unavailable`, without
  false empty results or poisoning otherwise healthy writes.

`EventFilter` accepts optional paired `from_time`/`to_time` (half-open `[from,to)`
on the audit timestamp), `Action`, symbolic `target_id`, and `InvocationStatus`.
Exact types/enums are required; values are parameterized in SQL. Each call uses a
consistent transaction. Totals count distinct events before aggregating findings.
Finding summaries retain occurrence multiplicity and distinct affected interactions
by producer/code. Invocation/total timing statistics include completed samples
only. Operational events form a null action group.

```python
from datetime import UTC, datetime, timedelta
from app.control_layer.domain import Action
from app.control_layer.reporting import EventFilter, GroupBy

now = datetime.now(UTC)
filters = EventFilter(now - timedelta(days=1), now, action=Action.BLOCK)
events = app.state.reporting.list_events(filters, limit=50)
summary = app.state.reporting.summarize(filters, group_by=GroupBy.TARGET)
```

## Local operation and limits

Runtime SQLite files and sidecars are ignored by Git. Filesystem access is the
local authorization boundary. Back up with SQLite's consistent backup facilities,
or stop the service and preserve the complete store. Remove history manually only
while stopped; no retention/deletion/import runs automatically. Rolling back to a
previous stdout-only release does not retain this reporting guarantee; preserve
history and never destructively downgrade its schema.

This is a single-host challenge foundation. It does not protect against malicious
administrators or disk loss. Disk exhaustion and write lock failures close the
required gate. Operators manage file growth and backups. Exports, export manifests,
operator CLI, model/policy/control/day groupings, control/code filters, exhaustive
acknowledgement fault matrices and platform permission auditing are deferred.
The read-only HTTP API is described below. Output inspection, budget governance and
cryptographic audit integrity remain outside this capability. Automated verification uses
temporary files, local detector inputs and fake targets; Ollama is not required.

## Semantic attempt evidence and schema version 2

Events expose nullable `semantic_duration_ms`, `semantic_model_id` and
`semantic_status` (succeeded/failed), all absent together when no attempt occurs.
Duration includes semantic input guards, setup, inference, reading, score parsing,
threshold conversion and actual-producer finding validation. It excludes earlier
deterministic controls, audit emission and target generation, and never exceeds
whole evaluation duration. Identity comes from startup control registration,
separate from target `model_id`; no runtime identity assertion is authoritative.

Existing typed detail/list queries expose these fields. `Summary.semantic` is a
TimingSummary counting both succeeded and failed attempts. Disabled/not-reached
and historical events have no semantic sample. Failed evaluation keeps
operational status, no action/findings, target not_invoked and no invocation
sample. Required stdout/persistence failures still prevent target dispatch;
completion accounting and poisoning are unchanged. No raw scores, input, output,
spans, hashes, rationale or exceptions are persisted.

New stores and EventView use schema version 2. Exact known v1 stores undergo one
transaction adding nullable observation columns and closed checks, validating v2
DDL and updating user_version before commit. IDs, sequences, prior fields and
outcomes are preserved. Unsupported/modified DDL fails startup; migration errors
roll back schema/version/data without deleting evidence. Back up history before
upgrading. An older binary rejects v2; use a prior backup or compatible binary
for code rollback. Explicitly disabling semantic policy retains history and
independent deterministic enforcement.

## Read-only reporting HTTP API

Routes, all using `Cache-Control: no-store`:

- `GET /v1/reporting/summary`: `{api_version:1, window, generated_at,
  reporting_health, overall}`. `overall` contains interaction_total, named actions
  and invocations count maps (all enum keys), operational_failure_total, findings
  (producer/code/occurrences/affected_interactions), and evaluation/semantic/
  invocation/total timing objects (samples/sum_ms/min_ms/max_ms/mean_ms).
- `GET /v1/reporting/events`: `{api_version:1, window, items,
  next_before_sequence}`. Each item is an explicit schema-v2 EventView projection:
  sequence, schema_version, safe event, invocation_status and optional completion
  including its fixed target error code. Newest-first, default 50, maximum 100.
- `GET /v1/reporting/events/{interaction_id}`: `{api_version:1, item}` or fixed 404.
  Requires a canonical hyphenated UUID and accepts no query parameters.

Summary/events accept paired `from_time`/`to_time` as ISO UTC timestamps with `T`,
seconds, optional 1–6 fractional digits and `Z`/`+00:00`. Range is half-open,
increasing and at most 31 days. Omit both for the server's last 24 hours.
Optional filters: action ALLOW/REDACT/BLOCK, symbolic target_id (historical valid
IDs can have no results), invocation_status succeeded/failed/unknown/not_invoked.
Events also accept canonical positive integer limit (1–100) and before_sequence
(1–9223372036854775807). The next cursor is the last sequence on a full page; a
final empty page is permitted. No grouping, export or control/code filters are
exposed. Unknown/repeated query keys, invalid bounds, enums and identifiers are
rejected without reflection.

```bash
curl -s 'http://127.0.0.1:8000/v1/reporting/summary?action=BLOCK'
curl -s 'http://127.0.0.1:8000/v1/reporting/events?limit=10&invocation_status=failed'
```

Fixed reporting errors contain only `{error_code}`: 422 invalid_reporting_query,
404 not_found, 405 method_not_allowed, 503 reporting_unavailable. These envelopes
are separate from unchanged interaction responses. Reporting health is existing
write-gate health (`healthy`/`reporting_write_failed`), independent of read
availability and target outcomes. GETs neither mutate evidence nor invoke controls
or targets. No query reaches SQLite from the browser; routes delegate to typed
store methods. The new in-process `list_recent_events(filters, limit=100,
before_sequence=None)` retains typed bounds 1–1000 and signed-64-bit exclusive
cursors. Existing ascending `list_events` is unchanged.

Trailing-slash reporting paths return fixed 404 with no-store rather than redirect;
no query text is reflected in a Location header. Interaction routing is unchanged.

The local deployment has no authentication platform or permissive CORS. Keep its
loopback binding and trusted operator context. API schemas are explicit allowlists:
no raw/transformed prompts, output, semantic responses/scores, credentials, PII,
URLs, arbitrary metadata or exception text. Strings render as text. Target model
selection is startup identity only, not a guarantee of the returned model version.
Historical details cannot reconstruct content. There is no model dependency for
viewing evidence and no fabricated seed data in the application.
