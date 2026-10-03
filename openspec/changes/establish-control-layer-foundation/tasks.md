# Tasks

**Apply gate — approved 2026-10-03:** The user instruction “The OpenSpec change `establish-control-layer-foundation` is approved for apply” authorizes the complete proposal, four delta specs, design, and all three task groups. The same instruction approves the proposed HTTP mapping, deliberately bounded ASCII email detector (not general email or PII protection), and flushed stdout decision audit sink; durable retention and target-completion records remain out of scope. All artifacts were read before implementation. Work proceeds group by group with verification, independent correctness and security/bypass PASS, and exactly one Conventional Commit per group. Do not archive or push.

**Completion gate:** An OpenSpec `all_done` task state is insufficient. For each task group, pass its verification, obtain fresh independent correctness and security/bypass reviews with no unresolved findings, record evidence in `docs/worklog.md`, and make exactly one English Conventional Commit. Before declaring this change complete or archiving it, run final lint, format, fast and integration tests, and obtain fresh correctness and security/bypass review results of `PASS`. Record final evidence in `docs/worklog.md` and reference it here. Never archive failing or incomplete work.

## 1. Runtime and decision core

- [x] 1.1 Bootstrap Python 3.12+ and Poetry non-package mode with the approved runtime and development dependencies; verify `poetry check`, installation, and imports work without an external service.
- [x] 1.2 Implement immutable Interaction, Finding, Span, FindingResolution, Decision and Control contracts with separate operational error types; verify fast tests cover immutability, server-owned IDs, safe finding fields, and the absence of synthetic Findings on errors.
- [x] 1.3 Implement the bounded ASCII email control and its whole-candidate span behavior; verify deterministic tests cover allowed variants, punctuation, multiple addresses, Unicode preceding a match, length boundaries, malformed candidates, `xn--` labels, and every documented unsupported form.
- [x] 1.4 Implement strict startup YAML policy loading and validation, including duplicate-key detection, explicit mappings, disabled control behavior, and invalid-policy rejection; verify fast tests cover each enforcement-changing configuration and startup failure.
- [x] 1.5 Implement central action resolution and original-text span redaction; verify fast tests cover no findings, all three mappings, action precedence and selective redaction with test-only trusted codes and policy snapshots, overlap, original-content preservation for ALLOW, and fail-closed invalid findings or spans. Verify the production loader still rejects those test-only codes.
- [x] 1.6 Document the core architecture that now exists in `docs/architecture.md`; verify it matches the implemented modules and run `poetry run ruff check .`, `poetry run ruff format --check .`, `poetry run pytest tests/unit`, and `git diff --check` with passing results.
- [x] 1.7 Obtain fresh independent correctness and security/bypass reviews of group 1 with `PASS`, resolve findings, add its verified entry to `docs/worklog.md`, and create exactly one Conventional Commit for group 1; verify the worklog evidence and commit subject against Git history.

## 2. Audited execution path

- [ ] 2.1 Implement the synchronous orchestration service, TargetAdapter boundary, local echo adapter, and injectable target spy; verify service tests prove ALLOW forwards original content once, REDACT forwards only transformed content once, and BLOCK makes zero calls.
- [ ] 2.2 Implement an allowlisted AuditEvent serializer and synchronous JSON-lines sink, emitted before eligible dispatch; verify service tests inspect safe fields including explicit control enablement, event ordering, concurrent complete-line emission, sink poisoning after partial writes both with exceptions and short counts, and absence of input content, matched values, hashes, spans, snippets, and exception text.
- [ ] 2.3 Implement fail-closed operational paths for control exceptions, invalid findings or spans, inconsistent policy resolution, and audit failure, separate from policy BLOCK; verify service tests assert zero target calls, sanitized operational outcomes, and no synthetic Finding for each case.
- [ ] 2.4 Handle target failure after a successfully emitted decision event; verify service tests show the event does not claim target success and no raw exception reaches the result.
- [ ] 2.5 Update `docs/architecture.md` to the execution path now implemented; verify `poetry run ruff check .`, `poetry run ruff format --check .`, `poetry run pytest tests/unit`, and `git diff --check` pass.
- [ ] 2.6 Obtain fresh independent correctness and security/bypass reviews of group 2 with `PASS`, resolve findings, add its verified entry to `docs/worklog.md`, and create exactly one Conventional Commit for group 2; verify the worklog evidence and commit subject against Git history.

## 3. HTTP boundary and project verification

- [ ] 3.1 Implement the FastAPI application and `POST /v1/interactions` with strict request/response models, the fixed echo target, and the 16,384-character content limit; verify httpx tests cover valid input, the exact limit, over-limit content, missing/unknown fields, wrong types, empty content, malformed JSON with sensitive text, lone surrogate escapes, unsupported target, and caller-asserted identity.
- [ ] 3.2 Implement safe HTTP mapping for ALLOW, REDACT, policy BLOCK, internal evaluation/audit failure, and target failure; verify httpx tests assert the selected status codes, absence of sensitive values and exception text, zero target calls for all closed paths, and pre-dispatch audit ordering.
- [ ] 3.3 Add README installation, policy-selection, run, and test instructions; update `docs/architecture.md` to describe only the final implemented architecture. Verify documented commands and inspect the docs against the running local echo behavior.
- [ ] 3.4 Run final `poetry run ruff check .`, `poetry run ruff format --check .`, `poetry run pytest tests/unit`, `poetry run pytest tests/integration`, OpenSpec validation, and `git diff --check`; verify all pass with no external commercial service.
- [ ] 3.5 Obtain fresh independent specification/correctness and security/bypass reviews of the complete change with explicit `PASS`; fix confirmed findings, rerun affected verification, and request fresh review until both return `PASS`.
- [ ] 3.6 Add group 3 and final verification/review evidence to `docs/worklog.md`, reference that evidence here, and create exactly one Conventional Commit for group 3; verify the worklog evidence, this task record, and commit subject against Git history before declaring completion or archiving.

## Evidence

- Group 1: [worklog](../../../docs/worklog.md#2026-10-03--group-1-runtime-and-decision-core); final verification and fresh correctness/security reviews PASS. Commit subject: `feat: establish immutable policy and decision core` (resolve hash from Git history).
