# Proposal

## Why

Current safe audit records are written to stdout without persistent history, and describe eligibility rather than target completion. A small durable reporting backend is needed for security investigation, management summaries before an interactive dashboard can be built.

## What Changes

- Persist allowlisted decision and operational audit records through the existing required audit gate using local SQLite, while retaining the current JSON-lines sink and its failure/poisoning guarantees.
- Append a separate invocation outcome for eligible calls, distinguishing success, failure and unknown completion without rewriting the original decision.
- Retain trusted control/finding IDs, policy digest, registered target identity, optional startup-bound model identity, safe durations and fixed operational codes; exclude submitted content and output entirely.
- Add a typed in-process query/aggregation API for bounded queries. No reporting HTTP endpoints are introduced.
- Fail closed before dispatch when required persistence fails. A completion-write failure preserves the already obtained target response, marks storage unhealthy and prevents later dispatch; decisions lacking durable completion remain visibly unknown, and any already committed completion remains authoritative.
- Default application startup opens a configured local database and fails safely if storage cannot initialize. This adds an operational writable-storage prerequisite without changing interaction HTTP schemas or policy format.

## Capabilities

### New Capabilities

- `security-reporting`: Privacy-safe persistent interaction history, invocation outcomes, bounded reporting queries, management/security aggregations.

### Modified Capabilities

- `decision-audit`: Add required durable persistence alongside existing pre-dispatch emission and distinct post-invocation outcomes; preserve existing decision fields and stdout semantics.
- `interaction-gateway`: Extend immutable target metadata with an optional validated server-owned model identifier and wire reporting persistence at application lifespan.
- `local-model-target`: Replace the statement that reporting is future work with a reference to this reporting capability, without adding output inspection or model governance.

## Impact

Expected additions are flat reporting/store modules and focused unit/integration tests. Shared edits are limited to audit, service, target metadata, composition and application lifecycle; core controls, finding validation, central enforcement and policy configuration remain unchanged. SQLite uses the Python standard library. Documentation will describe storage setup, privacy, local access and limitations after implementation.

Goals are durable safe evidence, accurate outcome accounting and useful local queries. Non-goals are a dashboard, reporting HTTP/authentication, generic event bus, remote database, distributed ingestion, retention scheduler, historical stdout import, output inspection, resource/cost estimation, policy reload, detector changes or unrelated restructuring. Cryptographic tamper proofing remains outside scope.

The 2026-10-04 user instruction explicitly approves APPLY of the reduced scope.

## Approved scope reduction (2026-10-04)

The user's explicit APPLY approval requests a demo-ready foundation. Defer the
operator CLI and all exports (including manifests/snapshots), exhaustive filters
and groupings, platform permission auditing, and extensive acknowledgement fault
matrices. Keep basic typed listing/detail and summaries, SQLite durability,
content-free trusted attribution, distinct outcomes/timings, required persistence
before dispatch, completion poisoning, and deterministic tests. No HTTP or policy
schema changes. Implementation and two independent reviews remain required.
