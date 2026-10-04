# Tasks

Apply approved on 2026-10-03 by the user instruction: “I explicitly approve this OpenSpec for implementation. Implement exactly the approved proposal/design/specs/tasks.” Scope is these artifacts only, preserving all named enforcement, audit, privacy and echo guarantees. All design non-goals remain excluded; no Ollama installation/model download, archive, push or new change is authorized. Required deterministic verification and fresh correctness/security PASS reviews remain completion gates.

Owner: primary applying agent/developer, responsible for implementation, integration, verification and commits. Dependencies: archived extension surface and deterministic pack at `136f483`; consume without redesign. New adapter/tests/smoke ownership and shared composition/API/dependency/docs hotspots are listed in design.md; serialize shared edits. Do not modify security core, controls, policy/catalog, AGENTS.md or historical fixture JSON. If approved assumptions prove wrong, stop affected work and update artifacts before resuming.

## 1. Bounded adapter and transport

- [x] 1.1 Obtain and record explicit apply scope approval before code changes; verify its reference here covers these artifacts and excludes all listed non-goals.
- [x] 1.2 Promote existing HTTPX 0.28 dependency from dev-only to runtime and update poetry.lock; verify Poetry dependency consistency and adapter import without an Ollama SDK/server.
- [x] 1.3 Add frozen settings/loader in app/control_layer/ollama_target.py with exact design defaults, grammar/ranges and fixed invalid_target_configuration startup errors; add tests/unit/test_ollama_target.py covering accepted overrides, empty/invalid/nonfinite/bool bounds, loopback restrictions and no value/cause leakage; verify targeted unit tests.
- [x] 1.4 Implement existing TargetAdapter contract with one non-streaming fixed-model generate POST, invocation-local client/parser buffers, disabled proxies/redirects/retries and explicit connect/read/write/pool timeouts; verify unit tests assert exact approved prompt JSON, fixed model, one call and closed resources on success/failure.
- [x] 1.5 Enforce raw response byte cap before JSON parsing, identity encoding, strict completed text/scalar validation and character cap; verify unit tests for exact/over limits, missing/chunked/incorrect length, compressed body rejection, malformed UTF-8/JSON, duplicate keys/constants, invalid shapes/completion, empty text and ignored metadata.
- [x] 1.6 Sanitize all client/response errors with existing TargetError and suppressed chaining without content logs; verify prompt/output-bearing exceptions and 3xx/400/404/429/500 responses yield fixed failures with no retry/fallback or captured log leakage.
- [x] 1.7 Document adapter configuration, I/O inactivity versus wall-clock timeout, no guaranteed cancellation, loopback/cloud-disabled runtime preparation and uninspected output in README; verify defaults/ranges align with settings tests and no lifecycle/download automation is added.
- [x] 1.8 Verify this group's targeted tests and repository lint/format, record passing task-group evidence in docs/worklog.md and commit exactly once with an English Conventional Commit; do not commit partial/failing work.

## 2. Public registration and governed local interaction

- [x] 2.1 Register local-ollama alongside local-echo in composition and widen only the explicit public target selector in API; verify updated tests/unit/test_targets.py and test_security_pack.py assert both registrations with unchanged six controls, no network at assembly/startup, unchanged echo and no settings load for explicit registry injection.
- [x] 2.2 Add tests/integration/test_local_model_target.py with a deterministic threaded loopback fake runtime and real client; verify success, refused/reset connection, absent runtime, missing model, delayed headers/body timeout, malformed responses, unexpected statuses and oversized body/output, with resource cleanup and no real runtime dependency.
- [x] 2.3 Verify full gateway/security-pack ALLOW original, REDACT centrally transformed, BLOCK and evaluation/audit failure zero runtime calls, per-request audit-before-dispatch, retained binding identity and exactly one successful HTTP request; add regressions first for any discovered bypass.
- [x] 2.4 Verify unknown public IDs remain sanitized 422/no audit, unknown internal IDs and allowed public ID missing from injected registry use unresolved safe 503/zero calls, arbitrary injected destinations remain private, and prompt/model/URL strings cannot establish trusted audit identity.
- [x] 2.5 Add prompt/output-bearing error/audit/log privacy and concurrent distinct-prompt tests using event/barrier synchronization; verify response association, no shared request/parser state, per-request audit ordering and unchanged poisoned-sink behavior.
- [x] 2.6 Update full OpenAPI comparison in tests/integration/test_extensions.py to permit only the additional target enum difference; preserve EchoResult/schema fields/statuses and historical fixture JSON, document the difference in tests/fixtures/README.md; verify recorded echo HTTP fixtures and existing deterministic-control tests remain passing.
- [x] 2.7 Update README request examples and implemented architecture/system-summary/challenge traceability to reflect actual integrated behavior and honest remaining gaps; verify documentation states no output inspection, no full model authorization/budgets/reporting, unchanged policy digest and sync thread safety/latency limitations.
- [x] 2.8 Run both complete unit and integration suites plus lint/format; record task-group evidence in docs/worklog.md and commit exactly once after passing required verification, with no push.

## 3. Optional real-runtime demonstration

- [x] 3.1 Add scripts/smoke_local_model.py outside normal discovery, using existing HTTP test-client boundary and in-memory audit against a separately provisioned real runtime; verify it tests model text success, echo, blocked dispatch and pre-dispatch evidence without exact wording, raw content output, downloads or setup automation.
- [x] 3.2 Document explicit smoke command, Ollama local-only startup and preprovisioned qwen2.5:0.5b prerequisite in README; verify smoke is excluded from normal pytest and missing prerequisites yield fixed nonzero failure. Run when available and record runtime/model/hardware/latency, otherwise record NOT RUN and reason; optional execution is not a required normal-suite gate.
- [x] 3.3 Verify script lint/format and deterministic tests of its failure/privacy/result-check behavior without a real server; record task-group evidence and commit exactly once after passing checks.

## 4. Integration verification and independent review

- [x] 4.1 Run poetry run ruff check ., poetry run ruff format --check ., poetry run pytest tests/unit, poetry run pytest tests/integration, openspec validate add-local-model-target --strict, openspec validate --all --strict, openspec validate --archived --strict and git diff --check; record exact outcomes in docs/worklog.md and link the entry here. All required checks must PASS without Ollama.
- [x] 4.2 Delegate fresh specification/correctness review and fresh security/bypass review to agents that did not implement; require concrete file-referenced findings/reproducers and PASS/FAIL, record evidence in docs/worklog.md and reference it here. Proposal review does not satisfy this implementation gate.
- [x] 4.3 Fix confirmed findings only within approved scope, first add reproducing regressions, rerun affected required checks and request fresh independent reviews until both PASS; verify final review evidence references the final code state.
- [x] 4.4 Record final verification/review references here and completed evidence in docs/worklog.md; commit this completed integration group exactly once after required PASS. Do not declare complete or archive before these gates. Archiving requires a later user request; never push without explicit instruction.

Group 1 evidence: [worklog](../../../../docs/worklog.md#2026-10-03--local-model-target-group-1-bounded-adapter).

Group 2 evidence: [worklog](../../../../docs/worklog.md#2026-10-03--local-model-target-group-2-governed-gateway).

Group 3 and optional NOT RUN evidence: [worklog](../../../../docs/worklog.md#2026-10-03--local-model-target-group-3-optional-smoke).

Final verification/review evidence: [worklog](../../../../docs/worklog.md#2026-10-03--local-model-target-final-verification-and-independent-review).

Final acceptance: required checks PASS (1001 unit + 122 integration, Ruff,
Poetry consistency, active/all/archived strict validation and whitespace).
Fresh independent `/root/correctness_review` PASS and `/root/security_review` PASS
on final implementation `a327fc0`; no confirmed findings or corrective code changes.
Final task group changes only docs/evidence, preserving reviewed implementation.
See final worklog link above for review verification and optional smoke **NOT RUN**
(runtime executable absent and default port refused). Implementation is ready for
archive, but this change remains active; no archive or push is authorized.


Archive finalization authorized by the 2026-10-04 user instruction to archive and
commit all necessary changes. The previously attempted 2026-10-03 destination is
unreadable (ENOENT even outside sandbox; recreation gives EEXIST). This readable
archive restores all eight tracked planning/evidence files from reviewed Git HEAD,
with only archive-relative worklog links and this finalization note updated.
Implementation/tests remain unchanged; final reporting suite 1207 PASS also covers
local-model integration. See worklog finalization evidence for the recovery.
