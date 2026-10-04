# Tasks

## Approval and ownership

Planning authorization: user request to EXPLORE and create exactly one change, `add-security-reporting-foundation`, and explicitly not implement. **APPLY approval: NOT GRANTED.** Before checking implementation tasks, record the later explicit user instruction approving proposal.md, design.md, all four delta specs and this checklist. Resolve any revised material assumptions in these artifacts first.

Implementation/integration owner: primary agent, after approval. New files owned: `app/control_layer/reporting.py`, `reporting_store.py`, `reporting_cli.py`, `tests/unit/test_reporting.py`, `test_reporting_store.py`, `tests/integration/test_reporting.py`, `test_reporting_cli.py`, `docs/reporting.md`. Shared modifications: `audit.py`, `service.py`, `targets.py`, `composition.py`, `api.py`, relevant existing service/target/API tests, README, runtime ignore pattern, implemented architecture/worklog/traceability docs after verification. Do not modify detector modules, policy schema/resolution, registry finding-validation contracts, AGENTS.md or unrelated user work.

Dependencies: current trusted registrations, bound policy, retained target and audit-gated service, and implemented local-model interface. No active prerequisite change in the CLI inventory. Preserve existing staged local-model archival edits; reconcile the resulting baseline before APPLY without committing another task's work. Shared orchestration/audit/API/target integration is serialized under this owner. No second implementation agent may edit these files concurrently.

Each numbered group is a commit-sized task group. Create exactly one Conventional Commit after that group's required checks and applicable fresh independent correctness/security reviews PASS. Never commit failing/partial work, push, archive, or claim implementation complete from planning/task status alone. Record implementation verification and final fresh review evidence in docs/worklog.md and reference it here before declaring completion.

## 1. Trusted safe schema and target metadata

- [ ] 1.1 Add closed immutable reporting DTOs and projection validation against bound policy/target metadata; reconstruct producer/count/mapped action without content or spans. Verify unit tests reject unknown/foreign identifiers, bad types/counts/digest/action, metadata dictionaries and inconsistent enablement while accepting ALLOW/REDACT/BLOCK and operational events.
- [ ] 1.2 Extend optional frozen TargetDefinition model_id validation and load default Ollama settings once for shared adapter/registration identity. Verify target/registry/composition tests cover null echo, valid configured model, malformed/overlong/wrong-type IDs, retained bindings and response-metadata spoofing without network startup.
- [ ] 1.3 Document schema, provenance, privacy exclusions and configured-model versus actual runtime identity in docs/reporting.md. Verify examples contain no payload fields and match DTO tests; run `poetry run pytest tests/unit/test_reporting.py tests/unit/test_targets.py tests/unit/test_registry.py` and focused composition tests before fresh reviews/one group commit.

## 2. File-backed persistence and queries

- [ ] 2.1 Implement versioned SQLite event/control/finding/outcome tables, transactional appends, duplicate/orphan/ineligible-outcome rejection, private permissions, bounded busy timeout and write poisoning. Verify temporary-file store tests cover atomic rollback, restart, schema mismatch, unsafe/unwritable locations, concurrent writes and write/commit/lock failures without partial rows.
- [ ] 2.2 Implement safe paginated list/detail and summaries with typed filters, half-open UTC windows, parameterized values, closed grouping, deduplicated interaction joins and timing sample rules. Verify an exact-count fixture covers all actions, operational failure, target outcomes/unknown, repeated and cross-control findings, disabled-control status membership, combined producer/code matching, scoped finding sums, complete detail/export evidence, null models, boundaries, pagination, no matches, group overflow and injection attempts.
- [ ] 2.3 Add canary tests for submitted credentials/PII/attack content, returned output and exceptions; inspect rows, database/sidecar bytes where applicable, diagnostics and query serialization. Verify no raw/derived content or unvalidated IDs are persisted even under ALLOW.
- [ ] 2.4 Document persistence/versioning/private-directory setup, timing definitions and query examples in docs/reporting.md. Verify `poetry run pytest tests/unit/test_reporting.py tests/unit/test_reporting_store.py` PASS and request fresh correctness/security reviews before one group commit.

## 3. Audit gate, invocation outcomes and application lifecycle

- [ ] 3.1 Compose existing JSONL sink with required safe durable persistence and synchronized poison state; integrate startup store initialization, injection and owned-resource shutdown without changing public DTOs. Verify integration tests prove stdout flush and complete durable commit precede each invocation; startup failure and upstream short-write/flush/storage failures yield zero dispatch with existing sanitized semantics.
- [ ] 3.2 Add safe completion append after valid result/target failure and monotonic timing, without passing TargetResult/content to reporting. Verify successful and failed ALLOW/REDACT targets record distinct completion, BLOCK/evaluation errors are not_invoked, and simulated interruption leaves unknown without replay.
- [ ] 3.3 Add regression tests before resolving any discovered bypass: completion-write/commit failure preserves 200/502, invokes exactly once, exposes fixed health failure and closes later gates; concurrent calls already gated can finish without cross-request content or identity leakage. Include gate and completion commits that succeed then raise: preserve fully committed evidence, derive unknown only for absent completion, never retry/delete and close the gate regardless. Verify all failure diagnostics omit canaries and exception text.
- [ ] 3.4 Adapt relevant existing tests to inject temporary persistent stores through normal validation; retain stdout event shape/count and historical response/OpenAPI assertions. Verify unit service/routing tests and integration API/extensions/local-model/security-pack tests, without real Ollama or browser tests.
- [ ] 3.5 Document default database path/environment setting, required storage availability, split-sink non-atomicity, unknown outcomes and lifecycle/rollback in README and docs/reporting.md; add only relevant runtime storage ignore patterns. Verify all storage artifacts stay outside Git and public interaction behavior matches integration tests; obtain fresh correctness/security PASS before one group commit.

## 4. Local operator CLI and export

- [ ] 4.1 Provide local list/detail/summary CLI commands over read-only existing storage with fixed errors/nonzero failure and no reporting HTTP routes. Verify integration CLI tests exercise documented commands, absent store without creation, invalid filters without reflection, read failure distinct from empty results, and summary queries against known fixtures.
- [ ] 4.2 Implement JSONL snapshot export in bounded batches with schema/version/high-water/count manifest, private temporary/destination files, atomic publication without overwrite and cleanup on failure. Verify concurrent inserts/completions yield a consistent export, canaries never appear, existing files survive and injected write/read/rename failures leave no complete-looking partial output.
- [ ] 4.3 Document local filesystem authorization, query windows/limits, exports/backups, growth and manual stopped-service cleanup in docs/reporting.md and README. Verify command examples through `poetry run pytest tests/integration/test_reporting_cli.py tests/integration/test_reporting.py`; obtain fresh correctness/security PASS before one group commit.

## 5. Final integrated acceptance and independent review

- [ ] 5.1 Run `poetry run pytest`, `poetry run ruff check .`, `poetry run ruff format --check .` and `openspec validate add-security-reporting-foundation --strict`; verify full existing enforcement/audit/target compatibility and all acceptance criteria below. Optional real-model smoke is not required and omission is explicitly NOT RUN.
- [ ] 5.2 Update docs/architecture.md only for implemented behavior, challenge traceability only for proven coverage, and docs/worklog.md with exact commands/results and limitations. Verify none claims a dashboard, output inspection, cost/resource telemetry or cryptographic audit integrity.
- [ ] 5.3 Delegate fresh independent specification/correctness and security/bypass reviews to agents that did not implement. Require concrete findings with references/reproducers, fix confirmed findings with regressions first, rerun affected checks and request fresh reviews until both PASS. Verify final evidence is in docs/worklog.md and referenced here before one final integration commit or declaring completion. Archive only after a later explicit archive instruction and satisfied project gates.

## Acceptance criteria

All are required; these are observable gates, not an additional execution plan:

- File-backed committed evidence survives restart; concurrent events are complete and isolated.
- ALLOW/REDACT/BLOCK preserve trusted findings, central enforcement, exact approved content semantics, audit-before-invocation and existing HTTP response contracts.
- Target success/failure is independent of policy action; absent completion remains unknown; BLOCK/operational failures are not_invoked.
- Every reporting identity comes from validated startup metadata/actual-producer findings. Invalid/forged identifiers never enter storage, export or diagnostics.
- Prompts, redacted content, secrets/credentials/PII/attack values, raw model output, spans/hashes and raw exceptions never enter reporting under any action or failure path.
- Queries/aggregations return exact known totals and multiplicities, distinct interaction counts, bounded results, documented latency samples and sanitized input/read failures.
- Export is a consistent content-free JSONL snapshot with a correct manifest; output failure cannot publish a partial complete-looking artifact or overwrite existing data.
- Required pre-dispatch audit/storage failure calls no target; completion failure preserves the obtained response, closes later gates and causes no retry or false success claim.
- Default private storage setup/lifecycle works without commercial services; no dashboard, reporting HTTP, event bus, generic framework or unrelated refactor is introduced.
- Required automated verification and final fresh independent correctness/security reviews return PASS with recorded evidence. APPLY approval remains a separate prerequisite.

## Evidence

Planning validation and focused proposal review will be recorded in `evidence/planning-review.md`. These do not satisfy implementation verification or final independent code review. Implementation evidence: pending APPLY; no implementation tasks are complete.
