# Tasks

## Approval and execution boundary

The user requested exploration and creation of `add-deterministic-security-controls`
and explicitly instructed “Do not implement yet” and “Then stop.” This authorizes
planning only. **Apply approval: GRANTED on 2026-10-03.** The user states: “This message is explicit APPLY APPROVAL for the approved proposal, design, delta specs and tasks.” Scope is exactly this change: bearer, PEM, classic GitHub PAT/OAuth, labelled SSN, bounded local literal signatures, production registration/default policy, migration, adversarial/policy/audit/concurrency/HTTP tests and implementation documentation/accepted traceability. No broader feature or core-contract redesign is authorized. Baseline condition resolved before behavioral edits: see `evidence/baseline-relationship.md`. `continue` during artifact creation
continues planning; it does not override the implementation prohibition.

Baseline: verified post-archive `4b45120`; prerequisite
`generalize-control-layer-extension-points` is archived and consumed as-is. No new
architecture-generalization task or second change is authorized.

Implementation owner: primary agent. Allowed implementation files and shared
hotspots are enumerated in design decision 6. Core domain/registry/policy/service/
API/audit/targets, email evaluator, dependencies, AGENTS, environment configuration,
baseline evidence and other changes are outside planned behavioral edits. Stop
and revise approved artifacts if a concrete necessity changes those boundaries.

One coherent task group follows. Its exactly-one Conventional Commit occurs only
after all implementation, verification and required fresh independent PASS reviews.
No proposal-stage commit, archive or push is part of this request.

## 1. Deterministic security capability pack

- [x] 1.1 Record explicit apply approval and verify owned paths are clean on the dedicated branch based on `4b45120` or its verified integration successor; inspect prerequisite contracts without redesign. Verify approval cites the granting user instruction, `git status` preserves unrelated changes, and all selected scope matches the six deltas.
- [x] 1.2 Add `bearer_control.py` with `bearer-credential`/`secret.bearer`, exact whole-line grammar and token-only original spans; add `test_bearer.py` for positive/near-miss/malformed, 1/4096/4097 lengths, keyword case, SP/TAB, LF/CRLF/bare CR, multiline recovery, Unicode offsets, embedded/repeated values and unsupported forms. Document these boundaries in its module. Verify targeted pytest and Ruff pass. Trace: credential delta, whole-line bearer grammar/adversarial verification.
- [x] 1.3 Add `pem_control.py` with `pem-private-key`/`secret.pem_private_key`, five matching envelope labels, canonical base64 and full original block spans; add `test_pem.py` for every label, exact marker dash/case/label grammar, unsupported-END recovery, 31/32-byte threshold, wrapping/padding, max content, nested/mismatched/truncated candidates, multiline/mixed endings/bare CR, multiple blocks, Unicode offsets, malformed-neighbor recovery and excluded certificates/metadata/binary forms. Document shape-only scope in its module. Verify targeted pytest and Ruff pass. Trace: credential delta, complete bounded PEM envelopes/adversarial verification.
- [x] 1.4 Add `github_control.py` with `github-token` and separate PAT/OAuth codes, maximal-run whole-candidate matching; add `test_github.py` for both prefixes, 35/36/37 lengths, punctuation, case, Unicode/alphanumeric/underscore/hyphen boundaries, embedded/repeated tokens and unsupported prefixes/obfuscations. Document legacy-shape/checksum limitations in its module. Verify targeted pytest and Ruff pass. Trace: credential delta, bounded GitHub token shapes/adversarial verification.
- [x] 1.5 Add `ssn_control.py` with `us-ssn`/`pii.us_ssn`, exact label/numeric validation and number-only spans; add `test_ssn.py` for both labels/case, numeric boundaries, malformed/overlong groups, missing/embedded context, Unicode digits/offsets, repetitions, punctuation, newline rejection and unsupported forms. Document non-issuance/context limits in its module. Verify targeted pytest, existing email suite and Ruff pass. Trace: all labelled-SSN requirements.
- [x] 1.6 Add the bounded strict local JSON catalog loader and frozen representation in `attack_signatures.py`; add loader tests in `test_attack_signatures.py` covering every required field/type/version, duplicate keys/IDs/literals, intentional shared code, metadata bounds, invalid UTF-8/scalars, NaN/Infinity, 64-KiB/32-entry/8–256-character boundaries, unreadable data and sanitized errors. Verify targeted pytest and Ruff pass and no raw catalog is present in diagnostics. Trace: known-attack delta, trusted bounded startup catalog.
- [x] 1.7 Add the literal evaluator in `attack_signatures.py` and repository-owned five-entry `config/attack-signatures.json` matching design decision 4; register four deduplicated codes with required spans/non-redactable metadata. Add tests for each literal, case/spacing/CRLF/backslash-n near misses, quotations, multiple/embedded/overlapping occurrences, deterministic ordering, Unicode offsets, frozen snapshot after source edits and trusted new-code fixtures. Document exact coverage/provenance in module and README. Verify targeted pytest/Ruff, fixed-path loading independent of cwd and no execution/deserialization/network behavior. Trace: initial signature coverage, literal findings, local historical verification.
- [x] 1.8 Extend explicit production registrations in `composition.py` in approved order and upgrade `config/policy.yaml` with all six enabled controls/ten code mappings; add `test_security_pack.py` for exact ownership/capabilities, full startup mappings, catalog code collisions and incomplete-policy rejection. Verify startup uses frozen definitions before the existing binder, default controls contain only the approved pack and default targets remain local echo. Run targeted pytest/Ruff. Trace: gateway explicit composition and default pack policy.
- [x] 1.9 Migrate composition-sensitive historical fixtures in `test_registry.py`, `test_binding.py`, `test_extensions.py`, `test_api.py` and any directly affected existing test fixtures to explicit email-only injection where historical assertions require it. Add explicit old-policy/default-registry rejection and valid disabled-entry migration tests; update README sample policy and restart/rollback guidance. Verify the original email suite, exact historical digest/wire fixtures and full OpenAPI comparison pass without weakening original assertions. Trace: gateway preserved public behavior/migration and design migration plan.
- [x] 1.10 Add actual-control policy tests to `test_security_pack.py`: each sensitive-data code under ALLOW/REDACT/BLOCK; each attack code under ALLOW/BLOCK; invalid attack REDACT even disabled; explicit enablement/disablement and required mapping behavior. Verify default and alternative policies pass/fail as specified using deterministic inputs. Trace: default deterministic pack policy and non-redactable signature capability.
- [x] 1.11 Add cross-control tests for email+secret, labelled SSN+secret, attack+other finding, simultaneous findings from all six controls, no findings, findings-to-ALLOW, selective REDACT and BLOCK-over-REDACT. Permute valid registration/finding order under equivalent policies and assert unchanged strongest action. Verify trusted structured resolutions and zero dispatch for BLOCK. Trace: policy cross-control enforcement.
- [x] 1.12 Add exact original-offset redaction tests using real Unicode-prefixed email/SSN/credential matches and overlapping bearer/GitHub spans; preserve labels/separators and selected ALLOW values. Test generic adjacent/overlapping spans via existing trusted fixtures where actual grammars cannot produce adjacency. Verify byte-for-byte expected forwarded text, identity/target preservation and each selected value masked once. Trace: central original-offset composition.
- [x] 1.13 Add expanded-registry adversarial-output tests for unknown codes, cross-control ownership forgery, wrong producer, malformed findings/containers and missing/invalid spans under all applicable actions. Add regression tests before any discovered bypass fix. Verify fixed evaluation failure, no synthetic findings/BLOCK and zero target calls; run affected existing validation suites. Trace: production pack fail-closed verification.
- [x] 1.14 Add real-secret audit/error privacy and dispatch tests for ALLOW/REDACT/BLOCK, mixed controls, exceptions containing sensitive values, pre-dispatch event order, audit write/short-write/flush failures and poisoned-sink reuse. Verify allowlisted records exclude content, values, snippets, hashes, spans, catalog literals and raw exceptions; BLOCK/evaluation/audit failure cause zero invocations. Trace: deterministic pack audit privacy and dispatch.
- [x] 1.15 Add `tests/integration/test_security_pack_http.py` exercising full default registration/catalog/policy through HTTP to local echo/retained spy, including a multi-control end-to-end composition case, 200 ALLOW/REDACT, 403 BLOCK, 503 evaluation/audit failure, code ordering/multiplicity and explicit disabled status. Test concurrent inputs for no findings leakage and complete audit-before-corresponding-dispatch events. Verify existing input limits/scalar validation/public target restriction and all existing integration suites remain compatible. Trace: gateway, audit, policy production-pack scenarios.
- [x] 1.16 Update README and implemented architecture/system summary to tested bounded behavior, exact supported/unsupported categories, FP/FN risks, local-catalog trust/update procedure, policy-digest scope and migration. Prepare the coverage mapping for review in this change; leave the current traceability ledger unchanged until task 1.19 follows independent acceptance. Verify documented examples/policies with local tests and check no proposed behavior or final verification is claimed before evidence exists. Trace: proposal challenge mapping and design decisions 3–7.
- [x] 1.17 Run complete verification commands from design: Poetry check, Ruff lint/format, all unit/integration suites, strict change/all/current/archived OpenSpec checks and `git diff --check`. Verify all exit successfully, normal suite needs no network/LLM/paid service, full OpenAPI is unchanged, and record exact commands/counts/results in `docs/worklog.md` with a reference here. No redundant baseline-generalization exercise is required.
- [x] 1.18 Delegate fresh independent specification/correctness and security/bypass reviews to reviewers who did not implement. Require concrete references and reproducer/scenario for FAIL. Fix confirmed findings with regression-first tests, rerun affected/full required checks as appropriate, and request fresh reviews until both return PASS. Record reviewer identity/scope/results and references in worklog and here; task completion alone does not establish completion.
- [x] 1.19 Once verification and both independent reviews PASS, update `docs/requirements/traceability.md` to accepted bounded coverage while keeping broader challenge areas partial/deferred, finalize actual coverage documentation/worklog references, inspect staged owned scope and whitespace, and create exactly one English Conventional Commit for this task group. Verify coverage claims against passing evidence, commit subject/hash and clean owned paths while preserving unrelated files. Do not archive or push; require later user authorization.

## Evidence

Apply approval and implementation verification are recorded above and below.
Independent reviews initially found the SSN label omission. Regression-first
repair, full verification and both fresh final reviews now PASS; see
`evidence/implementation-reviews.md` and the worklog completion entry.

Planning strict validation and fresh read-only proposal PASS are recorded in
[planning verification](evidence/planning-verification.md). These do not complete
any implementation task or grant apply approval.

**Verification repair:** Combined pytest collection exposed duplicate test module basenames. Before the file rename, design/task references were corrected to `tests/integration/test_security_pack_http.py`. This file-only discovery repair preserves all approved test behaviors/assertions and changes no runtime or pytest configuration. The failing normal-suite collection is the regression reproducer.

**Initial task 1.17 PASS (before review repair):** 856 unit, 79 integration, 935 normal tests; all required checks PASS. Exact outputs in `evidence/implementation-verification.json`; worklog entry “Deterministic security pack implementation verification”. Superseded by the post-review verification below.

**Post-review task 1.17 PASS:** Regression-first SSN label-boundary repair; all
required commands rerun successfully, with 861 unit, 80 integration and 941 normal
tests. Exact outputs in `evidence/final-implementation-verification.json`; worklog
follow-up records the initial reviewer FAIL and repair. Both fresh final reviews PASS.

**Task 1.18 PASS:** `/root/final_correctness_review` and
`/root/final_security_review` independently return PASS without editing files.
Reviewer scopes, checks and initial finding/repair are recorded in
`evidence/implementation-reviews.md` and the worklog completion entry.

**Task 1.19 acceptance:** Both reviews and final verification PASS. Accepted
traceability/system documentation updated; all 41 owned paths inspected and staged
whitespace PASS. Single authorized commit: `feat: add deterministic security controls`
(resolve hash from the commit containing this evidence). No archive or push.

## Finalization authorization and evidence

The user instruction on 2026-10-03 explicitly requests “Finalize this change only”,
“archive `add-deterministic-security-controls`” and “commit the archive/spec
synchronization if repository rules authorize it.” This authorizes synchronization,
archive and one finalization commit after the repository gates pass; no runtime
changes, new feature or push. Implementation commit: `d11ffc3`. All 19 tasks and
recorded final independent correctness/security PASS reviews remain complete.

Fresh final verification and read-only conformity PASS, synchronized six deltas,
archive integrity and current/archived validation are recorded in
`docs/worklog.md`, entry “Deterministic security controls finalization and archive”.
This completion entry supplements the historical implementation evidence above.
