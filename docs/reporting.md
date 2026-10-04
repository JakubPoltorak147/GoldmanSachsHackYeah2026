# Durable security reporting

The default HTTP application requires file-backed SQLite reporting in addition to
its existing flushed JSONL audit. Set `CONTROL_LAYER_REPORTING_DB` to a local file;
the default is `var/security-reporting.sqlite3`. There is no memory or stdout-only
fallback. New parent directories and files use 0700/0600 on POSIX. Use a trusted,
operator-owned private directory; administer permissions on existing directories,
files and backups. Symlink database destinations and SQLite URI/memory destinations
are rejected. Initialization failure raises a fixed reporting error without paths.

SQLite schema version 1 stores atomic audit events, control status, finding counts
and separate invocation outcomes. WAL, synchronous FULL and a one-second busy
timeout are enabled. Unsupported schema versions or incompatible version-1 table/constraint/trigger
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
There is no public health/reporting HTTP endpoint.

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
There is no dashboard, output inspection, semantic control, budget governance or
cryptographic audit integrity in this capability. Automated verification uses
temporary files, local detector inputs and fake targets; Ollama is not required.
