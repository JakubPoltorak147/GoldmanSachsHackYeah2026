# Tasks

**Planning authorization:** The 2026-10-03 user instruction “Now create the OpenSpec change: generalize-control-layer-extension-points” authorizes proposal, design, delta specs, and tasks only. The six refinements in that instruction are incorporated. Exploration acceptance is not apply approval. No runtime implementation is authorized.

**Apply gate:** Before task 1.1, review all artifacts and obtain explicit approval for their complete implementation scope. Record the exact user instruction, date, and scope here. If an approved design proves wrong, stop the affected work and resolve the artifact change before continuing. Do not silently extend scope.

**Explicit apply approval (2026-10-03):** The user instructed: “I approve the complete implementation scope of the OpenSpec change `generalize-control-layer-extension-points`.” They further instructed: “Proceed with apply according to AGENTS.md, docs/collaboration.md, the approved proposal, design, delta specs, and tasks” and “Record this instruction as the explicit apply approval required by the task gate.” Approval covers only this change, with all stated deferred capabilities excluded. No archive, push, or new change is authorized. The user requires stopping if task 1.1 baseline is not clean.

**Ownership and dependencies:** One implementation owner—the primary agent/developer assigned to apply—owns the complete task group, shared-core integration, verification, and commit. Use `change/generalize-control-layer-extension-points`, preferably in a separate worktree. The archived foundation/current specs are the prerequisite; no other active change is required. Owned implementation scope and forbidden areas are defined in design decision 7. Reviewers are read-only and do not overlap implementation ownership. Dependent controls/target work begins only from the merged prerequisite, with concrete separate files/worktrees and one owner for shared composition/configuration/spec changes.

**Completion gate:** All tasks, verification, and fresh independent specification/correctness and security/bypass reviews must PASS before completion. Add evidence to `docs/worklog.md` and reference it here. Exactly one English Conventional Commit covers this single coherent task group after it passes; no partial/failing commits. Do not archive or push without separate authorization. The planning artifacts' `done` status is not implementation completion.

## 1. Architectural extension refactor (one task group)

- [x] 1.1 Establish clean pre-change baseline verification before any runtime edits: inspect Git status/HEAD and isolate overlapping product changes without modifying unrelated user files; run `poetry check`, `poetry run ruff check .`, `poetry run ruff format --check .`, `poetry run pytest tests/unit`, `poetry run pytest tests/integration`, `openspec validate --all --strict`, `openspec validate --archived --strict`, and `git diff --check`. Capture the existing default policy digest, representative HTTP response/error shapes, and OpenAPI request/response schemas. Record the revision, commands/results, and preserved unrelated changes in worklog/task evidence; stop on baseline failures rather than counting them as refactor results.
- [x] 1.2 Add immutable finding/control definitions, registrations, and ordered control registry; register only existing email in production. Verify unit tests reject duplicate IDs/codes, unsafe/overlong identifiers, bad types, empty code catalogues, inconsistent evaluator assertions, and REDACT-capable definitions without required spans; input-collection/evaluator-ID mutation cannot alter registered bindings. Prefer flat modules; package migration is optional.
- [x] 1.3 Add immutable target definitions/registrations and exact registry/resolver with reserved `unresolved` ID. Verify unit tests cover two local test targets, duplicates/unsafe IDs, reserved-ID rejection, immutable input copying, exact lookup, no fallback/URL interpretation, and no invocation/network activity during resolution. Production still registers only local echo.
- [x] 1.4 Replace email-only policy loading with registry validation producing an immutable bound policy/execution plan that retains exact registrations. Verify unit tests cover explicit enablement for every registered control, full enabled mappings, allowed disabled subsets/omissions, invalid syntax/keys/types/actions/codes, unsupported REDACT even when disabled, and startup failure when a new registration lacks a policy entry.
- [x] 1.5 Preserve policy canonicalization and stable execution order. Verify baseline foundation digest is unchanged; equivalent policy key orders yield equal digests and the same registered execution order; repeated evaluation retains exact startup registration identities; disabled entries remain observable without evaluation.
- [x] 1.6 Validate findings using the invoked registration and derive trusted downstream identity from it. Verify adversarial unit tests reject forged producer IDs/cross-control codes, malformed containers/types, invalid spans including booleans, and missing spans under ALLOW/REDACT/BLOCK for REDACT-capable definitions. Verify valid spanless non-redactable ALLOW/BLOCK findings and required-span enforcement independent of email constants.
- [x] 1.7 Adapt central resolution to bound mappings and validated findings while preserving precedence and original-span redaction. Verify multi-control tests cover no findings, ALLOW/REDACT/BLOCK precedence, selective cross-control overlap/adjacency, fixed `[REDACTED]` masking, unchanged original ALLOW interaction, preserved identity/target, and sanitized fail-closed inconsistent resolution. Run the existing email suite without changing detector expectations.
- [x] 1.8 Switch service orchestration to the retained plan and a target binding resolved once before evaluation. Verify service tests prove correct routing for two targets, zero controls/calls on unknown targets, exact-once eligible invocation after audit, no re-resolution after audit, and zero adapter calls for BLOCK/evaluation/audit failures.
- [x] 1.9 Derive audit metadata from retained target registration, plan entries, and actual-producer validated findings. Verify default field/value compatibility, forged-output exclusion, safe `unresolved` operational records containing no supplied secret/URL, no synthetic BLOCK, no target-success claims, concurrent complete records, short-write/flush failure, permanent sink poisoning, and sanitized target-result/failure handling.
- [x] 1.10 Wire explicit default composition and registry/sink injection through the same startup loader/binder. Verify API startup tests use multiple registered test controls with complete policy, reject invalid injected registries/incomplete policy without fallback, preserve administrator policy selection, and confirm core service/policy contain no concrete email construction/catalogue or local-echo dispatch/audit selection.
- [x] 1.11 Generalize response finding codes to strict validated strings while keeping the public local-echo request restriction. Verify integration tests cover non-email test codes, list ordering/multiplicity, existing result/null/error envelopes and all status mappings, rejection of internally registered non-public targets with 422/no audit/no calls, and an OpenAPI comparison showing only the justified finding-code item enum broadening.
- [x] 1.12 Verify all existing foundation regressions: email grammar/whole-candidate matching, exact content/scalar handling and 16,384-character boundaries, server-owned IDs, strict shape/identity rejection, sanitized errors, audit privacy/order, disabled controls, target failures, and original/redacted echo. Preserve default `config/policy.yaml`; add regression-first tests for any discovered bypass before fixing it.
- [x] 1.13 Update README compatibility/injection guidance and `docs/architecture.md` to the now-implemented contracts, including mandatory policy updates for future production registrations, OpenAPI broadening, span-only redaction, and optional package layout. Verify documentation matches tested behavior and concrete future ownership boundaries; leave current specs, collaboration/context/requirements files, dependencies, and unrelated user edits untouched.
- [x] 1.14 Run complete final verification: `poetry check`, `poetry run ruff check .`, `poetry run ruff format --check .`, `poetry run pytest tests/unit`, `poetry run pytest tests/integration`, `openspec validate generalize-control-layer-extension-points --strict`, `openspec validate --all --strict`, and `git diff --check`. Record passing results and compare compatibility evidence to task 1.1; no external commercial service is required.
- [x] 1.15 Delegate fresh independent specification/correctness and security/bypass reviews to reviewers who did not implement the change. Require concrete file references/reproducers for FAIL findings; fix confirmed findings with regression-first tests, rerun affected verification, and request fresh reviews until both return PASS with no unresolved findings.
- [x] 1.16 Record baseline, implementation verification, compatibility evidence, and final independent PASS results in `docs/worklog.md`; reference the entry here. Review staged scope/whitespace and create exactly one Conventional Commit for this task group. Verify its subject/hash and clean owned paths, preserving unrelated user changes; do not archive or push.

## Evidence

Apply approval is recorded above. Earlier attempts stopped because Poetry was
unavailable; their historical record remains in `docs/worklog.md`, entry
“Extension-point apply baseline blocked”. Those failures are not refactor results.

**Task 1.1 PASS (2026-10-03):** The user instructed “To domknijmy krok 1.1”,
limiting this session to baseline completion. All eight required commands exited
0 at HEAD `97d2c1504b4426450fde5b58e61d4e5a100bbc18`, branch `main`. Product
paths were clean before and after capture; existing documentation/planning changes
were preserved. Environment repair installed the existing lockfile without
changing dependencies. See `docs/worklog.md`, entry “Extension-point task 1.1
baseline verified”, [verification](evidence/baseline-verification.json),
[HTTP examples](evidence/baseline-http.json), and
[full OpenAPI](evidence/baseline-openapi.json).

Default canonical policy digest:
`5416596669594e811989eb6cfba7311737e80922f2fb4c2171837038aa427ec4`.
Only response UUID values in the 13 synthetic HTTP examples are normalized;
response fields and null omission are preserved. OpenAPI is captured unmodified.
Progress is 1/16. Task 1.2 and runtime implementation have not started. Establish
the planned implementation branch/worktree before runtime edits. Full-change
independent implementation reviews and the single task-group commit remain pending.

Fresh read-only baseline reviewer `baseline_review`: **PASS**, no findings;
independently confirmed digest/file hash, full OpenAPI equality, HTTP evidence
and unchanged product paths. Review evidence is in the worklog entry above;
task 1.15 implementation reviews remain pending.

**Resume authorization (2026-10-03):** The user instructed “1.1 is done. Start from 1.2. I guarantee you it is all ok.” Continued on `change/generalize-control-layer-extension-points`, preserving the recorded successful baseline and unrelated changes.

**Task 1.2 verification:** `poetry run pytest tests/unit/test_registry.py`: 25 PASS. Targeted Ruff lint and format checks PASS. Immutable copied definitions/registrations, exact ordered lookup, globally unique codes, bounded strict metadata and evaluator assertions covered. Production composition registers only existing email.

**Task 1.3 verification:** 12 target tests PASS; targeted Ruff lint/format PASS. Two copied immutable target bindings, exact resolution without adapter calls, reserved/unsafe IDs and invalid bindings covered; default registers only local echo.

**Task 1.4 verification:** Registry-bound startup loader retains exact registrations; 18 binding tests PASS including explicit entries, complete enabled mappings, disabled subsets, unsupported REDACT and strict types. Existing malformed YAML cases will run with migrated fixtures during foundation verification.

**Task 1.5 verification:** 19 binding tests PASS; exact baseline digest retained, equivalent YAML orders produce equal digests and registry order, repeated plan invocation retains identities and skips disabled entries. Service-level repetition is covered when orchestration switches in 1.8.

**Task 1.6 verification:** 25 adversarial finding-validation tests PASS: actual producer mismatch, foreign codes, malformed containers/types, exact spans including boolean rejection, required spans and canonical registration identity. Policy-action combinations are additionally exercised in 1.7/1.8.

**Task 1.7 verification:** 121 policy/binding/email tests PASS; cross-control precedence, selective overlapping/adjacent original spans, spanless ALLOW/BLOCK, required spans under every action, inconsistent resolution and unchanged email expectations. Targeted lint PASS.

**Task 1.8 verification:** 44 service/routing tests PASS. Two targets route after audit using a binding resolved once; changing registry during emission cannot redirect dispatch. Unknown targets perform zero evaluations/calls; BLOCK and evaluation/audit failures remain closed.

**Task 1.9 verification:** 47 service/audit/routing tests PASS, preserving safe default fields, excluding forged outputs, unresolved supplied secrets/URLs, concurrent complete records, write/flush poisoning across targets and sanitized result failures without completion claims. Existing audit serializer/sink unchanged.

**Task 1.10 verification:** 40 existing HTTP tests and 4 registry startup tests PASS outside sandbox. Two controls use exact startup bindings, incomplete policy/invalid injected registries fail without fallback; administrator selection preserved. Core policy/service select no concrete email/echo implementation. Restricted HTTP run hung as in baseline and was interrupted; no product failure.

**Task 1.11 verification:** 50 HTTP tests PASS; non-email codes retain order/multiplicity, forged outputs yield sanitized 503, internal targets stay 422/no audit/calls, codes reject coercion. Full OpenAPI comparison differs only by removal of the finding-code item `const: pii.email`; all other schemas/routes are exactly equal.

**Task 1.12 verification:** 237 unit tests and 50 integration tests PASS; original foundation assertions preserved with migrated internal injection fixtures. Added exact comparisons for all 13 recorded baseline HTTP cases: 23 extension integration tests PASS. Policy/config/dependencies/current specs unchanged. No discovered detector bypass or detector expectation changes.

**Task 1.13 verification:** README and implemented architecture document tested registration/binding/injection contracts, mandatory future policy entries, strict span redaction, sole OpenAPI item broadening, flat layout and serialized future integration ownership. Forbidden/current-spec/dependency/user documentation paths preserved.

**Task 1.14 verification:** All eight final commands PASS; 237 unit and 63 integration tests. Full stdout/stderr recorded in [final verification](evidence/final-verification.json). Baseline policy digest/file hash retained, exact 13 HTTP cases and complete OpenAPI comparison PASS. Independent implementation reviews remain pending.

**Task 1.15 verification:** Fresh `extension_correctness_review` and `extension_security_review` both PASS, no findings. See [independent review evidence](evidence/independent-reviews.md). Reviewers made no changes; security independently reran all 300 tests and additional bypass/redaction probes.

**Task 1.16 completion evidence:** Baseline/final verification and both independent PASS results recorded in `docs/worklog.md`, entry “Generalize control-layer extension points”. The single task-group commit is `refactor: generalize control layer extension points`; resolve its hash from the commit containing this evidence. Stage only owned paths and baseline/final worklog entries; preserve unrelated worklog edits and all other user files. No archive or push.
