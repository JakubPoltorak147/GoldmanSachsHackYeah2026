# Tasks

## Approval and ownership

Explicit APPLY approval: user instruction on 2026-10-04, “This message is my
explicit APPLY approval”, authorizing scope reduction followed immediately by
implementation. Revised scope is recorded in proposal/design/specs. Primary agent
owns all edits; fresh agents review read-only. Preserve staged local-model work.
One integrated task group and one commit after verification and both reviews PASS.
Initially do not archive; superseded by the 2026-10-04 archive authorization below.

## 1. Demo-ready reporting foundation

- [x] 1.1 Implement closed typed projection/query DTOs and trusted target model metadata; verify invalid identifiers/types, action precedence and privacy with focused unit tests.
- [x] 1.2 Implement versioned file-backed SQLite atomic events, separate outcomes, pagination/detail/basic summaries and safe local defaults; verify restart, unknown outcomes, aggregation, read/write failure and non-leakage deterministically.
- [x] 1.3 Integrate required composed audit gate, completion recording/latency, poisoning and application lifecycle while preserving HTTP/policy contracts; verify ALLOW/REDACT/BLOCK, operational events, success/failure, pre-dispatch ordering, completion failure and core committed-then-raised regression with focused integration tests without Ollama.
- [x] 1.4 Document implemented schema, query boundary, storage setup and limitations in README/docs/reporting.md/architecture/traceability; verify examples match implementation and runtime storage is ignored.
- [x] 1.5 Run focused reporting/service/target/API tests first, then full pytest, ruff check, ruff format --check and strict OpenSpec validation; record commands/results in docs/worklog.md.
- [x] 1.6 Obtain fresh independent correctness and security/bypass PASS reviews; fix confirmed findings with regression tests first, rerun affected checks and fresh reviews. Record review evidence in docs/worklog.md and reference it here before one commit. Leave change unarchived.

## Deferred

All export/manifest/snapshot work and CLI; exhaustive filter/grouping combinations;
extensive filesystem/platform permission auditing; acknowledgement fault matrices
beyond a core regression. Dashboard, output inspection, semantic controls, budgets
and cryptographic audit integrity remain outside this change.

## Verification evidence

See `docs/worklog.md`, “2026-10-04 — Security reporting foundation implementation
verification”: initial focused 224 PASS; affected 104 PASS; schema regression
3 FAIL before fix, then reporting 74 PASS / affected integration 107 PASS; final
full 1207 PASS; Ruff lint/format PASS with the pre-existing missing archive path
excluded; strict OpenSpec and whitespace PASS. The exact broad formatter invocation
encounters that unrelated missing directory; staged archival work is preserved.

Fresh correctness review initially found incompatible version-1 schemas accepted
at startup. Regressions were added first, then versioned schema structure validation
fixed the issue. Final fresh correctness PASS (118 independent unit tests) and
security/bypass PASS (104 independent unit tests), no remaining findings. Reviewer
agents did not implement or edit. Evidence and final verdicts are in worklog.

One integrated task-group commit follows verified implementation and reviews. Do
not include pre-existing staged archival/spec/worklog edits. No push. Archive authorization follows below.


## Archive authorization and finalization

The subsequent 2026-10-04 user instruction, “Ok so now everything necessary to
archive and commit all the necessarry changes”, authorizes spec synchronization,
archive and finalization commit. Implementation commit: b801527. All required
verification and independent correctness/security reviews PASS, with no unresolved
findings. Delta requirements synchronized to main specs and strict validation PASS.
Archive-relative worklog: [finalization evidence](../../../../docs/worklog.md).
