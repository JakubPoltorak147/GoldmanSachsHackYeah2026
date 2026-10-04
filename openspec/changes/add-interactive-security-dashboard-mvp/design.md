# Design

## Context

See proposal.md for motivation. Exploration was limited to current relevant specs, reporting/query code and tests, interaction/service/composition boundaries, local Ollama and semantic adapters, and their policies. No active change existed at exploration start.

Observed: `create_app` uses FastAPI with synchronous interaction handlers; startup retains `state.reporting` and `state.service`. `ReportingStore` already has schema-v2 safe event DTOs, summaries, UUID detail, write health and ascending sequence listing. Semantic timing/model/status already exist. SQLite is entirely behind the typed store. The declared web stack has no frontend framework or build tooling. No new payload storage, timing instrumentation or migration is necessary.

## Goals / Non-Goals

**Goals:** Make actual evidence readable immediately; preserve safe projections and enforcement; establish a stable reporting/UI surface that change 2 can consume.

**Non-Goals:** See proposal exclusions. No live model requirement, seed database, invented metrics, trace service or orchestration change. Dashboard GETs never invoke controls/targets or mutate reporting state.

## Decisions

### Same-origin application and lightweight UI

Serve `/dashboard` and local `/dashboard/assets/` from FastAPI. Use plain HTML/CSS and ES modules with a shared API client, safe event renderer and page-content/navigation slot. A separate SPA/build pipeline adds work without an existing framework to reuse. All assets are local; no CDN, fonts or chart dependency. Build a cohesive dark security-console presentation with strong typography, spacing, ALLOW/REDACT/BLOCK accents, compact bar rankings and timing cards. Icons and simple charts use CSS or inline code-owned SVG.

Use a responsive card grid above a recent-event table; selecting an event opens a keyboard-accessible detail drawer with visible focus and Escape/close support. Text labels supplement color. Start with a visible last-24-hours window and offer 1 hour / 24 hours / 7 days plus action, target and invocation-status filters. Show filter chips and clear/reset. Top-five findings use occurrence counts and separately label affected interactions. Top controls sum finding occurrences by producer; do not sum per-code affected counts into distinct control interactions.

### Three minimal reporting routes

New `reporting_api.py` owns request parsing and explicit closed response models; `api.py` only includes its router and mounts assets. Do not serialize arbitrary `__dict__`, runtime adapter metadata or generic exceptions.

| Route | Contract |
| --- | --- |
| `GET /v1/reporting/summary` | `{api_version:1, window:{from_time,to_time}, generated_at, reporting_health, overall}`; reuse `Summary` totals, actions, invocations, findings and evaluation/semantic/invocation/total statistics |
| `GET /v1/reporting/events` | `{api_version:1, window, items:[EventView], next_before_sequence}`; newest-first bounded page |
| `GET /v1/reporting/events/{interaction_id}` | Explicit safe EventView envelope or fixed 404 |

`overall` uses named action and invocation-status count maps, finding summaries with producer/code/occurrences/affected_interactions, and timing objects containing samples/sum_ms/min_ms/max_ms/mean_ms. Include all enum keys even at zero. `reporting_health` is only existing `healthy`/`reporting_write_failed`; it is write-gate health, not Ollama availability. Evaluation operational failures are a separate total; target failures are the failed invocation count and never added to BLOCK. No combined failure total that double-counts or changes existing semantics.

EventView exposes sequence, schema_version, safe event fields, invocation_status and optional completion, including its derived fixed target error code. IDs/model IDs come only from historical trusted metadata. Details show enabled/evaluated controls, producer/code/count/mapped action, reason/error, policy digest, target/evaluator identities and timings. Null semantic observations mean not recorded/not attempted, not success; null timings show em dash and zero samples are explicit. Per-control latency is unavailable and is not invented. Target identity is displayed on recent rows and details; evaluator identity remains visually distinct.

Summary and events accept optional paired `from_time`/`to_time`, action, target_id and invocation_status. Both bounds omitted selects server UTC last 24 hours; only one is invalid. Explicit bounds must be UTC, increasing and no more than 31 days. Events additionally accept limit 1–100 (default 50) and positive integer `before_sequence`; summaries do not accept grouping or pagination. Reject unknown/repeated query keys, noncanonical integers, oversized cursor (> signed 64-bit), invalid enums/UUIDs/datetimes, nonzero timezone offsets, oversized/invalid target IDs and unsupported methods with fixed errors without reflection. Unknown well-formed historical target IDs can legitimately yield empty results. Use `EventFilter` and parameterized store queries; errors use a separate closed reporting envelope `{error_code}` with 422 invalid_reporting_query, 404 not_found, 503 reporting_unavailable (unexpected read errors included) and 405 method_not_allowed. Existing interaction envelopes remain unchanged. API replies use `Cache-Control: no-store`.

### Bounded recent listing without history scans

Add `ReportingStore.list_recent_events(filters, limit=100, before_sequence=None)` using the existing safe selection/view/read transaction with `sequence < cursor ORDER BY sequence DESC LIMIT ?`. Retain `list_events` unchanged. Typed bounds remain 1–1000 with exact positive signed-64-bit cursors; the HTTP layer has the smaller 100 limit. Return next cursor as the last returned sequence only when a full page is returned; a final empty page is acceptable. This small additive method solves latest-event access; alternatives of scanning ascending pages or a frontend SQLite query violate speed or boundary requirements.

### Honest polling and late completions

Refresh summary and the first recent page every three seconds, including existing rows so `unknown` can become succeeded/failed. Poll open detail too. Re-query after filter/window changes; cancel obsolete GETs or discard by generation token, avoid overlapping cycles, pause while hidden and refresh when visible. Never merge responses from different filter generations. Preserve selected UUID and drawer across refreshes. Older pages are loaded on demand and not appended to the live first-page cache. Provide Refresh now.

On errors keep the last successful values with a conspicuous stale/unavailable label and last-updated time; do not replace them with zeros. Empty successful data gets an inviting, truthful no-events state. Summary/list/detail calls are individually consistent store reads, not one cross-route snapshot; small polling differences are expected. Refreshing completions rather than append-only polling is essential because completion does not create a new event sequence.

### Privacy and extension contract

Reporting routes contain only the existing allowlist; prohibit prompts, transformed prompts, outputs, scores, semantic raw JSON, secrets, PII, URLs, exception text and arbitrary metadata. Render scalar strings with `textContent`, never model/content-derived HTML. Browser receives JSON only and never SQLite. Deploy locally with documented loopback Uvicorn binding and same-origin assets; no authentication platform or permissive CORS is introduced.

Change 2 may add a navigation item/content panel, use the shared detail renderer and fetch events by interaction UUID. It must not change these response shapes or add content to them. Change 1 has no demo endpoint, catalog, execution button or dependency on change 2.

## Risks / Trade-offs

- [No live history yet] -> honest empty state; populate only by actual existing interaction calls, never synthetic evidence.
- [Polling latency and separate snapshots] -> three-second refresh, visible window/last-update labels, manual refresh, no real-time guarantee.
- [Unknown outcome] -> label completion evidence unavailable, never assert target was invoked or succeeded.
- [Local trusted metadata may be sensitive if misconfigured] -> retain the existing non-sensitive registration contract and avoid exposing settings/URLs.
- [Browser setup adds verification dependencies] -> add only development Playwright support for two essential journeys, no frontend runtime dependencies.

## Migration Plan

Implementation owner: primary apply agent. Own dashboard assets, reporting router/query addition and focused tests. Shared hotspot: `api.py` route/mount wiring only; `reporting_store.py` read query only. Do not edit policy/domain/service/audit or Ollama transports. Change 2 starts only after this surface is integrated. No migration or destructive data operation; rollback removes routes/assets and preserves reporting database/history and existing interactions.

## Acceptance Criteria and Focused Tests

1. Existing mixed-evidence fixture drives accurate total/action/operational/invocation counts, multiplicity rankings and timing sample counts. Failed evaluations have no action; target failures retain eligible actions; unknown/not_invoked supply no invocation sample.
2. Latest-first unit tests include more than one page, filters, monotonic sequences, insert-between-pages and later completion of an existing sequence. Existing ascending callers remain compatible; invalid cursor/limit/query values fail safely.
3. HTTP integration covers three GETs, defaults/31-day boundaries, all validation/errors, full safe response schemas, no mutation/target calls and unchanged interaction outcomes. Query failure is 503, never false empty/zero; write health is accurately exposed independently of reads.
4. Canary tests inject secrets/PII into interaction input, target output, semantic response and exceptions; no reporting response/detail/log contains any canary or excluded field. Test unknown/repeated parameters, reflection and SQL-shaped IDs.
5. Two Playwright journeys use deterministic seeded safe evidence: filtering/selecting detail; polling updates existing unknown completion and recovery from unavailable reads. Assert empty/loading/stale/error states, keyboard drawer behavior and narrow viewport usability. Browser tests verify UI only; security logic stays in lower layers.
6. Manual visual review at desktop and mobile widths verifies readable counts, rankings, identities, timings, timeline and safe detail without Ollama. Capture actual review evidence during apply.
7. Required automated checks and fresh correctness plus security/bypass implementation reviews return PASS before completion/archive; record evidence in worklog and reference it from tasks. Planning readiness is not apply authorization.
