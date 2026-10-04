# Worklog

### 2026-10-03 — Extension-point task 1.1 baseline verified

**Scope:** The user instructed “To domknijmy krok 1.1”. Completed only the
pre-change baseline for `generalize-control-layer-extension-points`. Task 1.2
and runtime implementation have not started. The blocked entry below remains
historical; this entry supersedes its current baseline status.

**Revision/isolation:** HEAD `97d2c1504b4426450fde5b58e61d4e5a100bbc18`
(`chore: archive control layer foundation baseline`), branch `main`, unchanged
through capture. Before and after capture, Git showed no tracked or untracked
product changes in `app/`, `tests/`, `config/`, `pyproject.toml`, `poetry.lock`,
`README.md`, `docs/architecture.md`, or `openspec/specs/`. No overlapping product
changes required isolation. Preserved existing modified `AGENTS.md`,
`docs/project-context.md`, `docs/worklog.md`, and untracked `docs/collaboration.md`,
`docs/reference/`, `docs/requirements/`, the summary and approved change directory.
This step changes only baseline evidence, this worklog, the summary and task 1.1
tracking. Establish the planned implementation branch/worktree before runtime
edits; the unchanged product baseline was captured on `main`.

**Environment:** Python 3.12.15, Poetry 2.5.1. Installation from the existing
lockfile succeeded outside the sandbox with
`POETRY_CACHE_DIR=/tmp/control-layer-poetry-cache poetry install`. Sandbox
DNS/network restrictions and an unwritable default cache blocked earlier attempts.
Outside the sandbox, verbose Poetry logs showed PyPI HTTP 200 followed by
`PermissionError(13, 'Permission denied')`; `/home/node/.cache` belonged to
`nobody:nogroup`. Writable cache resolved installation. No dependency updates
or repository environment configuration changes. HTTP tests/capture also ran
outside the sandbox; the restricted integration run hung and was interrupted,
not counted as PASS.

**Required verification:** All eight commands were rerun during capture and
exited 0. Exact arguments, stdout/stderr, versions, UTC capture time and initial
Git status are retained in
[baseline-verification.json](../openspec/changes/archive/2026-10-03-generalize-control-layer-extension-points/evidence/baseline-verification.json).

- PASS: `poetry check`.
- PASS: `poetry run ruff check .`.
- PASS: `poetry run ruff format --check .` (14 files).
- PASS: `poetry run pytest tests/unit` (133 passed).
- PASS: `poetry run pytest tests/integration` (40 passed).
- PASS: `openspec validate --all --strict` (5 items).
- PASS: `openspec validate --archived --strict` (1 archive).
- PASS: `git diff --check` with command-local `-c safe.directory` for the
  workspace ownership mismatch; no persistent Git configuration changes.

**Compatibility:** Default policy ID `foundation-default`; canonical digest
`5416596669594e811989eb6cfba7311737e80922f2fb4c2171837038aa427ec4`.
The verification artifact also includes the SHA-256 of the unchanged policy file.
[baseline-openapi.json](../openspec/changes/archive/2026-10-03-generalize-control-layer-extension-points/evidence/baseline-openapi.json)
is the full unmodified `create_app().openapi()` document with request/response
schemas. Finding-code items are currently constrained to `pii.email`; compare
against this document rather than assume a particular enum representation.
[baseline-http.json](../openspec/changes/archive/2026-10-03-generalize-control-layer-extension-points/evidence/baseline-http.json)
contains 13 synthetic local cases: no-findings ALLOW, default REDACT, email
ALLOW/BLOCK using temporary policy copies, invalid/unsupported/malformed input,
evaluation/audit/target/unexpected failures, 404 and 405. Recorded statuses,
bodies and target-call counts were asserted. The spy delegates successful calls
to the real local echo and verifies audit-before-dispatch. Default policy was
never edited. Only response UUID values are normalized after UUID validation;
exact forwarded text and null omission are preserved. Failure cases use explicit
local injection. No external target or commercial service is involved.

**Tracking:** Task 1.1 checked; tasks 1.2–1.16 remain unchecked. Baseline-evidence
review returned PASS; full refactor correctness/security reviews remain pending
at task 1.15. No commit: the single task-group commit is
required only at task 1.16 after the whole group passes. No archive or push.

**Independent baseline review:** Fresh read-only reviewer `baseline_review`
returned **PASS**, with no findings. Confirmed completeness of all eight command
records and 13 HTTP examples, exact equality of the complete OpenAPI snapshot,
canonical policy digest and policy-file hash with the current product, unchanged
product paths at the recorded HEAD, and coherent 1/16 tracking/preserved edits.
This reviews task 1.1 evidence only; it does not satisfy the future task 1.15
implementation correctness/security review gate.

### 2026-10-03 — Extension-point apply baseline blocked

**OpenSpec change:** `generalize-control-layer-extension-points`.

Recorded explicit user approval for the complete scoped apply in `tasks.md`.
Attempted task 1.1 before any runtime edits; stopped at the user's required
baseline gate. This entry records the attempt, not task-group completion.

**Baseline:** HEAD `97d2c1504b4426450fde5b58e61d4e5a100bbc18`
(`chore: archive control layer foundation baseline`), branch `main`.
Existing modified `AGENTS.md` and `docs/project-context.md`, and untracked
`docs/collaboration.md`, `docs/reference/`, `docs/requirements/`, and the approved
change directory were preserved. No overlapping runtime/test edits were present.

**Verification:** `poetry check`, `poetry run ruff check .`,
`poetry run ruff format --check .`, `poetry run pytest tests/unit`, and
`poetry run pytest tests/integration` each exited 127: `poetry: command not found`.
PASS: `openspec validate --all --strict` (5 items),
`openspec validate --archived --strict` (1 archive), and `git diff --check`.
Baseline digest/HTTP/OpenAPI capture remains pending; the baseline is not verified.

**Implementation/review/commit:** Not reached. No runtime, test, default-policy,
current-spec or dependency changes. All 16 tasks remain unchecked. No archive,
push or new change. Resume requires restoring Poetry/project environment and
rerunning task 1.1. Summary: `docs/generalize-control-layer-extension-points-summary.md`.

The sandbox launcher failed with disabled unprivileged namespaces; shell reads
and verification attempts used approved escalation. Evidence-only edits followed.

Chronological record of completed project work.

This is not a backlog and not a planning document.
Planned work belongs in OpenSpec.

Add one entry per completed task group.

---

## Entry template

### YYYY-MM-DD — <short goal>

**OpenSpec change:** `<change-name>` or `none`

**Goal**

What this task group was intended to achieve.

**Built**

- What changed.
- Important implementation details only where useful.

**Deviations**

- Differences from the approved design or task.
- `None` when there were no deviations.

**Verification**

List only commands and checks actually performed, with their results.
For Python changes, Ruff and relevant test commands may be appropriate once
those tools and tests exist. For documentation work, record document inspection,
whitespace checks, and relevant workflow checks.

Record PASS, FAIL or skipped with the reason.

**Independent review**

Reviewer result: `PASS` / `FAIL` / `not required`

Product implementation always requires a fresh independent review result of `PASS`
before completion or archive. `not required` may be used only for a documentation
or administrative task outside product implementation when no review is required
by the task; record the reason. It cannot waive a product review requirement.

Summarize confirmed findings and their resolution.

**Manual check**

What was actually run or inspected.

**Commit**

`<commit hash> <commit subject>`

For the commit containing this entry, record its exact subject and resolve the hash
from Git history after committing; do not embed a self-referential commit hash.

---

## Completed work

### 2026-10-03 — Bootstrap project documentation and OpenSpec workflow

**OpenSpec change:** `none` (repository bootstrap only; no product change created)

**Goal**

Prepare a truthful documentation and workflow baseline without selecting or
implementing product architecture.

**Built**

- Replaced the copied starter README with product status, document links, workflow,
  and OpenSpec setup instructions.
- Clarified approval before apply and verification plus independent review `PASS`
  before completion or archive; generated OpenSpec skills remain unchanged.
- Marked project-context architecture as conceptual and reduced architecture
  documentation to the current unimplemented state.
- Clarified worklog verification and review requirements.
- Added Python ignore rules and four-space Python indentation.
- Removed the copied Node manifests, Docker ignore file, and isolation script.
- Retained OpenSpec configuration, placeholders, skills, ownership marker, and
  the project security-reviewer instructions.

**Deviations**

None. No application code, runtime configuration, product specs, or infrastructure
was introduced. The requested audit export `bootstrap-audit.txt` is retained locally
and excluded from this commit.

**Verification**

- PASS: inspected working-tree and staged diffs; `git diff --check` and
  `git diff --cached --check` passed.
- PASS: `openspec --version` reported `1.14.0`; `openspec context --json`
  recognized this repository's OpenSpec root.
- PASS: `openspec list --json` and `openspec list --specs --json` reported no
  changes or capability specs; `openspec schemas --json` resolved `spec-driven`.
- PASS: the installed OpenSpec `readProjectConfig` parser read `schema: spec-driven`;
  `openspec doctor --json` reported a healthy root with no status issues.
- PASS: compared SHA-256 hashes of all six generated skills with the pre-edit
  baseline; contents are unchanged.
- PASS: checked that all four named starter files are absent.
- PASS: inspected `git status --short --untracked-files=all`.
- PASS: checked the staged path set against the explicit 18-file allowlist and
  inspected staged content; no local dev-container or secret files are staged.
- Product tests were not run: no application or product test suite exists.

**Independent review**

PASS: fresh independent correctness review (`bootstrap_review`) and staging /
workflow safety review (`bootstrap_safety_review`) found no concrete findings.
Both confirmed the approved scope, unchanged generated skills, workflow gates,
and staged whitespace checks.

**Manual check**

Inspected repository documentation, configuration, skills, and Git status.
Inspected the staged file list and content; only the authorized bootstrap files
are included. The audit export remains unstaged.

**Commit**

`chore: bootstrap project documentation and OpenSpec workflow`

Resolve the hash of the commit containing this entry from Git history.

### 2026-10-03 — Extension-point apply baseline blocked

**OpenSpec change:** `generalize-control-layer-extension-points`.

The current user instruction explicitly approves the complete change scope and
requires stopping on an unclean baseline. Approval is recorded in the change's
`tasks.md`. Read AGENTS.md, project context, collaboration, implemented architecture,
all current specs and the complete approved change before attempting task 1.1.

**Baseline verification**

- HEAD: `97d2c1504b4426450fde5b58e61d4e5a100bbc18`, branch `main`.
- BLOCKED (exit 127, `poetry: command not found`): `poetry check`,
  `poetry run ruff check .`, `poetry run ruff format --check .`,
  `poetry run pytest tests/unit`, `poetry run pytest tests/integration`.
- PASS: `openspec validate --all --strict` (5 items),
  `openspec validate --archived --strict` (1 archive), `git diff --check`.
- Digest, representative HTTP outcomes and OpenAPI baseline capture remain
  pending; task 1.1 is incomplete. This is an environment blocker, not a refactor
  failure. No runtime edits, environment repair or dependency installation occurred.

**Preserved existing changes**

Modified `AGENTS.md`, `docs/project-context.md`, `docs/worklog.md`; untracked
`docs/collaboration.md`, `docs/reference/`, `docs/requirements/`, the approved
change directory and `docs/generalize-control-layer-extension-points-summary.md`.
Only task evidence, this appended worklog entry and the existing summary were
updated by this session. Runtime, tests, default policy and current specs remain
untouched. No branch/worktree transition was needed before stopping.

**Independent reviews / commit**

Not reached: implementation did not start, all 16 tasks remain unchecked, and the
passing task-group commit gate was not reached. No commit, archive or push.
The requested Markdown report is in
`docs/generalize-control-layer-extension-points-summary.md`.


### 2026-10-03 — Group 1: runtime and decision core

**OpenSpec change:** `establish-control-layer-foundation`, tasks 1.1–1.7.

**Goal / Built**

Established Python 3.12+, Poetry non-package mode and a locked environment with
only the approved application/test dependencies. Added frozen core contracts,
separate operational errors, bounded ASCII email-address detection, strict
startup YAML loading with duplicate detection and immutable policy snapshots,
central action resolution, and original-offset selective redaction. Architecture
now describes the implemented core. User apply approval and resolved assumptions
are recorded in the change's tasks.md.

**Deviations**

None. The environment initially had Python 3.11 and no Poetry; Python 3.12.15
and Poetry were bootstrapped using temporary tooling under /tmp. Sandbox command
launch failed because user namespaces are unavailable; authorized escalated
commands were used. No bootstrap tool or local environment configuration is staged.

**Verification**

- PASS: `poetry check`, `poetry install`, and imports of all approved dependencies
  under Python 3.12.15. The checked-in lockfile installs without further changes.
- PASS: `poetry run ruff check .`, `poetry run ruff format --check .`,
  `poetry run pytest tests/unit` (103 passed), and `git diff --check`.
- Initial formatting/lint failures were corrected before final passing checks.
  Staging exposed an existing trailing blank line in a supplied delta spec that
  unstaged diff checks could not see; removed it without changing requirements,
  passed the staged whitespace check and amended the single group commit.
- Regression-first evidence: six quoted-local substring tests and two HTML-entity
  suffix tests failed before their fixes, then passed in the complete unit suite.
- Manual detector probes confirmed ordinary detection, rejection of malformed
  local parts and HTML-entity suffixes, and detection of a separate valid address
  after an unsupported quoted local.

**Independent review**

Initial `group1_correctness` and `group1_security`: FAIL for the same confirmed
quoted-local substring defect. Added failing regressions before suppression of
quoted-local regions. A related self-probe found an HTML-entity suffix defect;
added failing regressions and retained semicolons inside whole candidates.
Fresh `group1_correctness_final`: PASS; independently verified 103 tests, lint,
format, Poetry check and whitespace. Fresh `group1_security_final`: PASS;
independently verified 103 tests and 210 candidate probes. No unresolved findings.

**Commit**

`feat: establish immutable policy and decision core`

Resolve the hash of the commit containing this entry from Git history.


### 2026-10-03 — Group 2: audited execution path

**OpenSpec change:** `establish-control-layer-foundation`, tasks 2.1–2.6.

**Built**

Added synchronous service orchestration, injectable TargetAdapter and local echo,
allowlisted decision/operational events, and a locked JSON-lines sink with exact
write-count and flush acceptance. Evaluation/audit failures stop dispatch with
sanitized operational outcomes; target failure preserves its prior decision event.
Updated architecture to the execution path now implemented.

**Deviations:** None.

**Verification**

PASS: `poetry run ruff check .`, `poetry run ruff format --check .`,
`poetry run pytest tests/unit` (133 passed, including 30 service tests), and
`git diff --check`. Manual local echo demonstrated transformed content and safe
pre-dispatch audit. Tests include 40 concurrent records, throwing partial writes,
short write counts, flush failure and permanent poisoning, disabled control status,
invalid findings/spans/mappings, audit failure and target failure.

**Independent review**

Fresh `group2_correctness`: PASS; independently reran 30 service tests.
Fresh `group2_security`: PASS; inspected approved artifacts, code and test coverage
without rerunning tests. Neither reviewer implemented the group; no findings.
The delegated test author `group2_tests` was not a reviewer.

**Commit**

`feat: add audit-gated local interaction execution`

Resolve the hash of this entry's commit from Git history. Group 1 commit verified:
`5a6ed3a2100275e1d6728791f5ff773d99d8d8c3`.


### 2026-10-03 — Group 3: HTTP boundary and final verification

**OpenSpec change:** `establish-control-layer-foundation`, tasks 3.1–3.6.

**Built**

Added the strict FastAPI factory and POST `/v1/interactions`, server-owned IDs,
fixed local echo target, 1–16,384-character scalar text validation, safe response
DTOs and the approved 200/403/422/503/502 mapping. Startup loads the administrator's
policy selection before accepting requests. Validation, malformed JSON/UTF-8,
operational errors and target failures produce sanitized HTTP outcomes. Added
httpx integration tests and README install, policy-selection, run and test commands.
Updated architecture to describe only the final implemented runtime and boundaries.

**Deviations:** None. No additional application dependencies or infrastructure.
The API and integration test authors worked in separate files and did not review
or commit their implementation. The user requested additional agents and later
restored normal pace; all verification and review gates were preserved.

**Verification**

- PASS: `poetry env use python3.12`, `poetry install`, and `poetry check` using
  the bootstrapped Python 3.12.15 on PATH; no dependency updates were required.
- PASS: `poetry run ruff check .` and `poetry run ruff format --check .`
  (14 Python files).
- PASS: `poetry run pytest tests/unit` (133 passed).
- PASS: `poetry run pytest tests/integration` (40 passed). Includes exact scalar
  preservation, Unicode character limits, invalid shapes/types/extras/identity,
  malformed JSON with sensitive text, invalid UTF-8, lone surrogates, valid surrogate
  pairs, all policy/operational/target status mappings, zero calls on closed paths,
  audit ordering, disabled control, environment policy selection and startup failure.
- PASS: `openspec validate establish-control-layer-foundation --strict`.
- PASS: `git diff --check`; staged whitespace was checked before committing.
- PASS: actual local Uvicorn factory startup with `--no-access-log`, HTTP request
  and shutdown. Echo returned `Contact <[REDACTED]>`; stdout contained one parseable
  flushed decision line and no submitted address. README commands were inspected
  against this behavior. No external commercial service was used.

**Independent review — group 3 and complete change**

Fresh `final_correctness`: PASS. Independently ran all 173 tests, Ruff lint/format
and whitespace checks; inspected all artifacts, modules, configuration and docs.
Fresh `final_security`: PASS. Independently ran all 173 tests and adversarial HTTP
probes for policy-override instructions, malformed/deeply nested JSON, surrogates,
request-selected policy fields and audit content exclusion. No concrete findings.
Both reviewers were independent of implementation; no unresolved findings remain.

**Final state**

All approved task groups are implemented and verified. Architecture describes the
implemented application only. The detector remains deliberately bounded ASCII
email-address detection, not general email or PII protection. Audit is flushed
stdout decision recording; durable retention and target-completion records remain
out of scope. Ready to archive after final Git/task-record confirmation. Neither
archive nor push is authorized or performed.

**Commit**

`feat: expose validated policy-governed interaction API`

Resolve this entry's commit hash from Git history. Earlier task-group commits
verified against Git history:

- Group 1: `5a6ed3a2100275e1d6728791f5ff773d99d8d8c3`,
  `feat: establish immutable policy and decision core`.
- Group 2: `6d732f565a2057d5460f8263b02f83d18eebc021`,
  `feat: add audit-gated local interaction execution`.

### 2026-10-03 — Document the implemented system and approved assumptions

**OpenSpec change:** `none` (documentation follow-up to the completed foundation).

**Built**

Added `docs/system-summary.md` explaining the implemented request flow, startup
policy, the three approved assumptions, detector/audit boundaries, and the
relationship between this foundation and broader product goals. Links point to
existing implementation and approval records; no requirements or runtime changed.

**Verification**

PASS: inspected the summary against architecture, API, default policy, approved
change artifacts and recorded worklog evidence. Checked all five HTTP statuses,
explicit bounded-detector and audit limitations, referenced path existence,
final newline and absence of trailing whitespace. Staged whitespace checked before
commit. Product tests were not rerun for this documentation-only task; the summary
explicitly attributes the 173-test result to prior recorded verification.

**Independent review**

Not required: this is a documentation-only summary outside product implementation,
with no new behavior, requirements, policy, or enforcement changes.

**Deviations:** None.

**Commit**

`docs: summarize control layer and approved assumptions`

Resolve the hash of the commit containing this entry from Git history.

### 2026-10-03 — Archive the foundation as the current baseline

**OpenSpec change:** `establish-control-layer-foundation`, archived as
`2026-10-03-establish-control-layer-foundation`.

**Built**

- Inspected all change artifacts, implementation boundaries, repository status,
  task evidence and implementation commits. The current user instruction
  authorizes archive, superseding the earlier apply-session archive restriction.
- Ran `openspec archive establish-control-layer-foundation --yes` with spec sync
  and validation enabled. Promoted four capabilities with 11 added requirements
  and preserved the complete change, including `.openspec.yaml`, in the archive.
- Updated README validation commands, the system-summary archive link, and archived
  task evidence links/authorization. No application, test, dependency or runtime
  configuration changed. Pre-existing documentation edits were left untouched.

**Verification**

- PASS: 19/19 tasks, all artifacts complete, matching implementation commits, and
  recorded final independent correctness/security reviews PASS with no unresolved
  findings (see the group 3 entry above). No current-spec conflict or destination
  collision; all deltas contain only ADDED requirements and authored Purpose.
- PASS: reran Poetry check, Ruff lint/format, and all 173 unit/integration tests.
- PASS: `openspec validate establish-control-layer-foundation --strict` before
  archive; `openspec validate --all --strict` (4 specs) and
  `openspec validate --archived --strict` (1 archive) after archive.
- PASS: exact comparison of all four Purpose sections and complete requirement/
  scenario bodies against archived deltas; new main-spec headings are canonical.
- PASS: OpenSpec lists four current specs and zero active changes; whitespace
  and staged scope checks passed before commit.
- Archive emitted only the non-blocking advisory to consider splitting changes
  with more than 10 deltas. No missing prerequisites or blocking conflicts.

**Independent review**

Product implementation retains the recorded fresh `final_correctness` and
`final_security` PASS results. This task changes only planning/documentation
state. Fresh independent `archive_review`: PASS; confirmed exact spec preservation,
unchanged archived artifacts, corrected links, completion gates, strict validation,
zero active changes, and staged scope/whitespace with no runtime or user edits.

**Deviations:** None. No redesign, runtime change or push.

**Commit**

`chore: archive control layer foundation baseline`

Resolve the hash of the commit containing this entry from Git history.

### 2026-10-03 — Generalize control-layer extension points

**OpenSpec change:** `generalize-control-layer-extension-points`, tasks 1.2–1.16.
The user authorized resume and instructed “1.1 is done. Start from 1.2. I guarantee
you it is all ok.” Used the recorded successful baseline; earlier exit-127 results
remain historical environment failures, not product failures. Implementation branch:
`change/generalize-control-layer-extension-points`.

**Built**

- Immutable copied control/finding registrations with strict bounded metadata,
  globally unique codes and stable order; exact immutable target bindings with
  reserved safe `unresolved` operational identity.
- Registry-bound startup policy retaining exact evaluator registrations and explicit
  enablement/mappings. Actual-producer validation and central span redaction preserve
  foundation semantics. Service retains one target binding through audit/dispatch.
- Explicit production composition and uniform test registry injection. Production
  still contains only email and local echo. HTTP finding codes accept validated
  strings while public requests continue admitting only local echo.
- README and implemented architecture document contracts, policy rollout obligations,
  client schema compatibility and future ownership boundaries. Flat modules retained.

**Verification and compatibility**

Baseline at `97d2c1504b4426450fde5b58e61d4e5a100bbc18`: all eight baseline
commands passed, with 133 unit and 40 integration tests; see the baseline entry
and committed change evidence. Default policy digest remains
`5416596669594e811989eb6cfba7311737e80922f2fb4c2171837038aa427ec4`, and policy
file SHA-256 remains
`9dd0abf869bb4bb7733c63406344807c8f22ab7d20a87bf368ebae5dae0e2995`.

Final PASS: `poetry check`, `poetry run ruff check .`,
`poetry run ruff format --check .`, `poetry run pytest tests/unit` (237 tests),
`poetry run pytest tests/integration` (63 tests),
`openspec validate generalize-control-layer-extension-points --strict`,
`openspec validate --all --strict`, and `git diff --check`.
Exact commands/results are in
[final verification](../openspec/changes/archive/2026-10-03-generalize-control-layer-extension-points/evidence/final-verification.json).

All 13 recorded baseline HTTP cases match exactly after UUID normalization,
including result omission, status/error envelopes, forwarding content and call/audit
counts. Complete OpenAPI comparison changes only finding-code item removal of
`const: pii.email`. Email detector implementation/expectations, default policy,
dependencies and current specs are unchanged. Restricted HTTP tests hung as recorded
in the baseline; the run was interrupted and rerun successfully outside the sandbox.
The TestClient deprecation warning did not affect results; dependencies stayed fixed.

**Independent review**

Fresh read-only `extension_correctness_review`: **PASS**, no findings. Independently
reran 237 unit tests and two schema/strict-response tests; reviewed complete evidence.
Fresh read-only `extension_security_review`: **PASS**, no findings. Independently
reran 237 unit and 63 integration tests, eight prompt/policy override/repeated-request
probes and 1,000 randomized redaction overlap/adjacency probes. Neither reviewer
implemented or modified files. See
[review evidence](../openspec/changes/archive/2026-10-03-generalize-control-layer-extension-points/evidence/independent-reviews.md).

**Scope and commit**

Preserved unrelated modified AGENTS.md/project-context/worklog content and untracked
collaboration, summary, reference and requirements documents. The commit includes
only owned implementation/tests, README/architecture, this change and its evidence,
and baseline/final worklog evidence. No local environment files, archive, push,
new change or deferred capability.

`refactor: generalize control layer extension points`

Resolve the hash of the single task-group commit containing this entry from Git
history. All tasks and required final reviews passed before that commit.


### 2026-10-03 — Post-archive baseline repair

**Scope:** The user requested only restoration and fresh verification of the
post-archive repository baseline. No new OpenSpec change, feature, core refactor,
dependency update, archive command or push was performed. Implementation commit
`6f167a3` remains the completed extension-point change.

**Root cause and repair:** Integration collection failed with FileNotFoundError
because `test_extensions.py` loaded baseline HTTP evidence from the former active
change directory; its OpenAPI test used the same obsolete path. There was no
existing canonical test-fixture directory. Introduced documented long-lived
`tests/fixtures/foundation/` snapshots, copied byte for byte from archived evidence,
and resolved both paths relative to the test module. All assertions, 13 recorded
HTTP cases, and the exact schema comparison remain intact. Archived evidence is
preserved as the historical source rather than a runtime test dependency.

**Documentation and archive state:** Updated the stale task-1.1-only summary to
16/16 completed tasks, implementation commit, recorded review/verification PASS
and the observed archive state. Corrected worklog evidence links and its malformed
heading; preserved earlier blocked attempts and apply restrictions as historical
records. Updated system-summary target/producer identity and startup-binding
descriptions, retaining historical foundation verification. Corrected the challenge
source path to the actual `docs/reference/ai-control-layer.pdf`.

The complete extension-point archive (including `.openspec.yaml`) matches every
file from its former active path at HEAD byte for byte. No active copy remains.
Every archived delta requirement and scenario is present in the three synchronized
current capabilities; email specs are unchanged. Four current specs and two archives
validate. Archive completion is recorded here from observed repository state;
no archive operation needs repeating and no historical archived artifact was edited.

**Fresh verification on the repaired checkout:**

- PASS: `poetry check` — All set.
- PASS: `poetry run ruff check .` — All checks passed.
- PASS: `poetry run ruff format --check .` — 22 files already formatted.
- PASS: `poetry run pytest tests/unit -q` — 237 passed.
- PASS: `poetry run pytest tests/integration --collect-only -qq` — 40 API and
  23 extension tests collected, exit 0; the previous collection failure is resolved.
- PASS: `poetry run pytest tests/integration -q` — 63 passed.
- PASS: `poetry run pytest -q` — 300 passed.
- PASS: `openspec validate --all --strict` — four current specs, zero failures.
- PASS: `openspec validate --archived --strict` — two archives, zero failures.
- PASS: `git diff --check` and `git diff --cached --check`.
- PASS: direct byte comparisons of every archived file against HEAD's former
  active path and both fixtures against their archived originals; exact containment
  checks of every delta requirement/scenario in current specs; no active copy.

Restricted HTTP test runs hung and were interrupted (exit 130); they are not counted
as PASS. The successful integration and complete runs used approved execution
outside the sandbox, consistent with prior repository evidence. Both report the
existing Starlette TestClient/httpx deprecation warning; no dependency change is
needed for this repair. Unit tests and collection succeed inside the sandbox.

**Independent review:** Fresh read-only `baseline_correctness_review`: PASS, no
findings; independently verified all archive files, exact current-spec delta
containment, fixture bytes, unchanged email specification and integration collection.
Fresh read-only `baseline_security_review`: PASS, no findings; independently reran
237 unit tests and 63-test integration collection and checked central policy,
actual-producer validation, retained target identity, audit-before-dispatch, audit
privacy and unchanged runtime/configuration/dependencies. Neither reviewer
implemented or modified files.

**Git scope:** One restoration commit covers the existing archive move and current
spec synchronization, test fixtures/path repair, system/completion summaries and
owned worklog repair/evidence. Pre-existing governance/context/collaboration,
reference, requirements and historical worklog edits remain outside that commit.
The challenge-document filename correction remains ready to commit with its
pre-existing untracked requirements/reference group. This is a verified development
checkout with preserved user edits, not a claim that all Git paths are clean.
No new change or deferred feature was started. Commit subject:
`fix: restore post-archive development baseline`; resolve hash from Git history.


**Baseline commit scope follow-up:** The user's subsequent instructions “Ok add
those untracked files to the commits” and “and not staged” authorize including
the remaining reference/requirements/collaboration files and tracked governance,
context and historical worklog edits in the same baseline commit. These
supersede the earlier exclusion above. No runtime changes or push are included.

### 2026-10-03 — Deterministic security pack implementation verification

**Change:** `add-deterministic-security-controls`; explicit APPLY APPROVAL states
“This message is explicit APPLY APPROVAL for the approved proposal, design,
delta specs and tasks.” Baseline gate verified before behavioral edits: `4b45120`
is the amended replacement snapshot of `4584f2c`, both parented by `6f167a3`.
All runtime/config/test/spec repair work is identical; the replacement adds the
subsequently authorized governance/reference/requirements/collaboration and
historical worklog files. Evidence: change `evidence/baseline-relationship.md`.

Implemented five independent new controls: bounded whole-line bearer,
complete supported PEM envelopes, classic ghp_/gho_ shapes, labelled US SSN,
and five trusted local attack literals/four codes. Explicit default composition
and policy enable all six controls/ten codes. Central enforcement, original spans,
non-redactable attack metadata, startup completeness and audited dispatch consume
existing contracts; domain/registry/policy/service/API/audit/targets/email code
and dependencies are unchanged. Old email-only default policies fail startup;
historical fixtures use explicit email-only registrations without weakened assertions.

**Verification (all final results exit 0):**

- `poetry check` — All set.
- `poetry run ruff check .` — All checks passed.
- `poetry run ruff format --check .` — 34 files already formatted.
- `poetry run pytest tests/unit -q` — 856 passed.
- `poetry run pytest tests/integration -q` — 79 passed, one existing
  Starlette TestClient/httpx deprecation warning.
- `poetry run pytest -q` — 935 passed, same existing warning.
- `openspec validate add-deterministic-security-controls --strict` — valid.
- `openspec validate --all --strict` — 5 items passed, 0 failed.
- `openspec validate --archived --strict` — 2 archives passed, 0 failed.
- `git diff --check` — PASS.

The first complete normal-suite attempt failed collection because both new unit
and integration modules shared a basename. Design/task file references were
corrected before renaming the integration file to `test_security_pack_http.py`;
normal-suite collection and all 935 tests then passed. This reproducer and final
outputs are in change `evidence/implementation-verification.json`. Earlier
restricted HTTP execution hung and was interrupted, matching the known baseline
environment limitation; successful HTTP/normal runs used approved execution outside
the sandbox. No dependencies or security assertions were weakened.

Added deterministic adversarial grammar/candidate/canonical-base64 tests, strict
catalog validation and immutable-snapshot tests, real multi-control composition/
precedence/ordering/redaction, producer/code/span forgery, exception privacy,
write/short-write/flush poisoning, HTTP failures and concurrent isolation. Tests
include unchanged full OpenAPI/baseline wire fixtures and actual default local echo.
Normal suite runs without network, LLM, credentials or paid service; synthetic
payloads are never executed/deserialized. Independent implementation reviews are
pending; accepted challenge traceability and task-group completion are not yet claimed.

**Independent-review regression and final verification:** Initial fresh correctness
and security reviewers both returned FAIL for the same supported-SSN omission:
`XUS SSN: 123-45-6789` rejected the invalid long label after consuming the valid
inner `SSN:` candidate. Five prefix regression cases failed before the fix; an
HTTP regression now verifies default redaction. The Unicode left boundary is
part of the label regex, preserving ASCII-only keyword folding and approved
matching semantics. No shared core contract changed.

After repair, every required command was rerun: `poetry check` (All set),
`poetry run ruff check .` (PASS), `poetry run ruff format --check .`
(34 formatted), `poetry run pytest tests/unit -q` (861 passed),
`poetry run pytest tests/integration -q` (80 passed), `poetry run pytest -q`
(941 passed), `openspec validate add-deterministic-security-controls --strict`
(valid), `openspec validate --all --strict` (5 passed, 0 failed),
`openspec validate --archived --strict` (2 passed, 0 failed), and
`git diff --check` (PASS). All exit 0. The integration/normal suites retain only
the existing TestClient/httpx warning. Exact outputs:
`evidence/final-implementation-verification.json` in the change. Two new fresh
read-only final reviewers are checking the repaired implementation; completion
and accepted traceability remain gated on both PASS results.

**Final independent acceptance and task-group completion:** Fresh read-only
`/root/final_correctness_review` returned PASS, no unresolved findings; independently
ran 861 unit tests and checked approved artifacts, exact grammars, migration,
composition, historical compatibility and the SSN repair. Fresh read-only
`/root/final_security_review` returned PASS, no concrete security/bypass findings;
checked 20,000 SSN boundary cases, ran 624 focused tests and 17 security-pack HTTP
tests, and reviewed catalog trust/bounds/snapshot, validation, privacy, fail-closed
dispatch and concurrency. Neither implemented or edited files. Full review evidence:
change `evidence/implementation-reviews.md`. Both reviewed the repaired implementation
after the complete final verification above.

Accepted challenge traceability now records bounded deterministic controls,
PII/credential handling, centralized configurable enforcement, historical literal
mitigation and positive/negative self-testing. Broad challenge categories remain
partial/deferred; semantic controls, budgets, reporting and dashboard are not claimed.
All 19 tasks constitute one approved task group. The single authorized commit
subject is `feat: add deterministic security controls`; resolve its hash from the
commit containing this entry. Owned staged scope and whitespace are checked before
commit; no unrelated work, dependencies or core contracts are included. No archive,
push or new feature is authorized or performed.

### 2026-10-03 — Deterministic security controls finalization and archive

**Authorization and scope:** The user explicitly requested finalization only of
`add-deterministic-security-controls`, final verification, completion evidence,
archive, current/archived validation and a repository-authorized commit; no runtime
changes, new feature or push. Implementation commit `d11ffc3` has all 19 tasks
complete and recorded fresh final correctness/security PASS reviews. Current
runtime/configuration/tests match that reviewed commit exactly.

**Fresh final verification (all successful commands exit 0):**

- `poetry check` — All set.
- `poetry run ruff check .` — All checks passed.
- `poetry run ruff format --check .` — 34 files already formatted.
- `poetry run pytest tests/unit -q` — 861 passed.
- `poetry run pytest tests/integration -q` — 80 passed.
- `poetry run pytest -q` — 941 passed before archive and 941 passed after archive.
- `openspec validate add-deterministic-security-controls --strict` — valid before
  sync and after synchronization while still active.
- Before archive: `openspec validate --all --strict` — 5 passed;
  `openspec validate --specs --strict` — 4 passed;
  `openspec validate --archived --strict` — 2 passed.
- After archive: `openspec validate --all --strict` and
  `openspec validate --specs --strict` — 7 passed, 0 failed each;
  `openspec validate --archived --strict` — 3 passed, 0 failed.
- `openspec list --json` — no active changes.
- `git diff --check` — PASS; staged whitespace checked before commit.

HTTP/complete runs used approved execution outside the sandbox. The initial
restricted integration attempt produced no results and was interrupted (exit 130)
after the documented TestClient hang; it is not counted as PASS. Passing HTTP and
complete runs retain the existing TestClient/httpx deprecation warning. OpenSpec
emits an informational long-description hint for the approved whole gateway
requirement; its description and scenarios remain intact and strict validation passes.

**Conformity and independent finalization review:** Fresh read-only reviewer
`/root/finalization_conformity` returned PASS for approved scope, current reviewed
runtime and absence of active-change path dependencies in tests/app/config. Its
second read-only review returned PASS for all synchronized delta requirements and
scenarios, preservation of untouched blocks/titles/Purpose/email, archive integrity
and unchanged runtime/config/tests. No files were edited by the reviewer. The
previous final independent implementation correctness/security reviews remain PASS;
see [archived implementation reviews](../openspec/changes/archive/2026-10-03-add-deterministic-security-controls/evidence/implementation-reviews.md).

**Synchronization and archive:** Created current credential-exposure-detection,
labelled-ssn-detection and known-attack-signatures capabilities; added policy and
audit requirements; merged the two approved gateway updates. All six deltas match
current requirement/scenario blocks exactly. Existing titles/Purpose, unmentioned
requirements and the complete email specification remain unchanged.
Archived at `openspec/changes/archive/2026-10-03-add-deterministic-security-controls/`.
All 15 original artifacts, including `.openspec.yaml` and evidence, are preserved
byte for byte from `d11ffc3`, except the authorized finalization append to tasks.
The active copy is absent. Direct Git comparisons confirm no app/config/tests or
dependency changes.

**Git:** Started clean. One finalization task-group commit includes only the archive
move, synchronized current specs and completion/worklog evidence. Subject:
`chore: archive deterministic security controls`; resolve its hash from the commit
containing this entry. No push or other feature is included.

### 2026-10-03 — Local model target group 1: bounded adapter

User explicitly approved exact `add-local-model-target` artifacts for apply, with
no installation/download, architecture redesign, archive or push. Approval scope
is recorded in tasks.md. Added frozen settings, local-only bounded HTTPX adapter,
strict response validation and sanitized failures, plus configuration documentation.

Verification: `poetry run pytest tests/unit/test_ollama_target.py -q` — 126 PASS;
`poetry check` — PASS; adapter import without SDK/server — PASS;
`poetry run ruff check .` — PASS; `poetry run ruff format --check .` — 36 files PASS;
`git diff --check` — PASS. No runtime required. PyPI was unreachable both restricted
and after approved escalation, so existing locked versions/hashes were retained;
HTTPX, httpcore, certifi and their existing transitive dependencies now belong to
main, with Poetry's computed content hash and successful consistency check.
One task-group commit: `feat: add bounded local Ollama adapter`.

### 2026-10-03 — Local model target group 2: governed gateway

Registered local-ollama beside unchanged local-echo and widened only the explicit
API selector. Added threaded loopback fake-runtime transport/gateway tests, including
exact original/centrally redacted submission, BLOCK and failed gates with zero
requests, audit-before-request, retained binding, privacy and synchronized concurrency.
Full historical fixture comparisons normalize only approved OpenAPI differences.
Updated implemented-state docs and bounded challenge coverage; final acceptance
still requires fresh independent review.

Verification: `poetry run pytest tests/unit -q` — 989 PASS;
`poetry run pytest tests/integration -q` — 122 PASS (approved outside sandbox for
HTTP boundary/loopback). Ruff check/format and whitespace — PASS (37 formatted files).
No Ollama/model needed. Existing Starlette TestClient/httpx deprecation warning
remains. Initial targeted run had one fixture expecting an unsupported `os.system(`
literal to block (64 PASS, 1 FAIL); corrected it to the approved catalog literal,
without changing detection. Full suites then passed.
One group commit: `feat: integrate governed local model target`.

### 2026-10-03 — Local model target group 3: optional smoke

Added `scripts/smoke_local_model.py` outside pytest discovery. Explicit execution
uses TestClient/in-memory audit and observed retained adapters to check model scalar
text success, pre-dispatch evidence, echo and BLOCK zero-call dispatch. Only fixed
outcomes/length/elapsed time are printed. Missing prerequisites return sanitized
nonzero failure, never setup/download/fallback. README documents preparation/command.

Verification: `poetry run pytest tests/unit/test_smoke_local_model.py -q` — 12 PASS
using deterministic targets, no Ollama. Ruff check/format — PASS (39 files);
`git diff --check` — PASS. Initial malformed-surrogate fixture failed while HTTPX
constructed JSON, before the script check (11 PASS, 1 FAIL); encoding a literal
JSON escape corrected the fixture and all checks passed.
Optional real Ollama smoke: **NOT RUN**. `command -v ollama` found no executable;
connection to default loopback port 11434 was refused. No runtime/model installation
or download. Runtime version/model/hardware/inference latency: unavailable/not measured.
One group commit: `test: add optional local model smoke`.

### 2026-10-03 — Local model target final verification and independent review

Final implementation state submitted to fresh reviewers: `a327fc0`, following
adapter group `d1d1fc8` and integration group `cc3c977`. Required verification after
all three groups (commands exit 0, no real Ollama/model):

- `poetry check` — All set.
- `poetry run ruff check .` — All checks passed.
- `poetry run ruff format --check .` — 39 files already formatted.
- `poetry run pytest tests/unit` — 1001 passed, 1 existing TestClient deprecation warning.
- `poetry run pytest tests/integration` — 122 passed, 1 existing TestClient warning.
- `openspec validate add-local-model-target --strict` — valid.
- `openspec validate --all --strict` — 8 passed, 0 failed (existing long gateway
  requirement informational hint only).
- `openspec validate --archived --strict` — 3 passed, 0 failed.
- `git diff --check` — PASS.

HTTP/loopback TestClient checks used approved execution outside the sandbox. All
normal tests are deterministic with client doubles/fake runtime or injected targets.
Optional real smoke remains NOT RUN as recorded in group 3. No core policy/service/
audit/registry/domain/control, policy config/catalog or historical fixture JSON edits.
Fresh correctness and security review outcomes will be recorded below before
completion; artifact/task readiness alone is not acceptance.

**Fresh specification/correctness review — PASS:** `/root/correctness_review` did
not implement this change and reviewed final code `a327fc0`, all approved artifacts,
current specs and subsequent evidence/doc wording changes. No blocking findings or
scope deviations. Confirmed settings, bounded one-call transport and parsing,
central policy/audit/retained binding/zero-call gates, unchanged echo/protected
files, public compatibility and optional smoke/privacy/limitations.
Independent focused adapter/smoke/target/fake-runtime/compatibility run:
`poetry run pytest tests/unit/test_ollama_target.py tests/unit/test_smoke_local_model.py tests/unit/test_targets.py tests/integration/test_local_model_target.py tests/integration/test_extensions.py -q`
— 217 PASS, 1 existing warning (7.18s), outside sandbox; initial restricted
TestClient attempt hung and was interrupted without a verification outcome.
No required corrective regression was identified.

**Fresh security/bypass review — PASS:** `/root/security_review`, a fresh reviewer
that did not implement, reviewed final implementation
`a327fc09fb3cd6a340eae012da11deeaaeed631c` and documentation-only updates against
approved scope/current specs. No concrete bypass or mandatory fix. Independently
ran 180 adapter/smoke/fake-runtime checks plus 47 existing routing/service regressions,
all PASS, with no file edits. Verified fixed loopback destination/model, disabled
proxies/redirects/retries, pre-parse bounds/strict scalar completion, central redaction,
retained binding/audit gating, repeated poisoned-sink zero dispatch, identity and
error/log privacy, concurrency isolation and smoke privacy. References included
ollama_target.py settings/transport/parser and unchanged service.py retained dispatch.

**Final disposition:** Both independent implementation reviews PASS. No confirmed
findings, so no corrective code changes/regressions were needed under task 4.3.
Final code/tests remain byte-identical to reviewed `a327fc0`; final group contains
only documentation/evidence/task completion. Required checks above cover final code;
strict validation/lint/format/whitespace were rechecked after evidence completion.
All 23 tasks are complete; verification and review gates are satisfied. Real smoke
NOT RUN is optional and does not weaken deterministic verification. Remaining limits:
uninspected output, trusted cloud-disabled daemon without attestation, per-operation
inactivity bounds rather than total deadline/cancellation, synchronous thread/queue
latency and no semantic controls, full model authorization, budgets or reporting.
One completed integration/evidence commit: `chore: record local model verification`;
resolve its hash from the commit containing this entry. No archive, spec synchronization,
installation/model download, push or new change. Implementation PASS, ready for later
user-authorized archive.


### 2026-10-03 — Local model target finalization and archive

**Authorization:** User requested finalization and archive of `add-local-model-target`
only, required final verification and no new scope/refactors/cleanup. Started clean
at `8b54bce`. Implementation/tests/scripts/config/dependencies match independently
reviewed `a327fc0` exactly. All 23 tasks are complete; the recorded fresh correctness
and security/bypass reviews are PASS with no unresolved findings.

**Fresh final verification:** `poetry check` PASS; `poetry run ruff check .` PASS;
`poetry run ruff format --check .` PASS (39 files); `poetry run pytest tests/unit -q`
1001 PASS; `poetry run pytest tests/integration -q` 122 PASS; active-change strict
validation PASS; before sync all strict validation 8 PASS and archived strict
validation 3 PASS; after sync current-spec strict validation 8 PASS, all strict
validation 9 PASS and active-change strict validation PASS; `git diff --check` PASS.
All successful commands exit 0. Restricted unit run stalled at the documented
TestClient boundary and was interrupted (130), not counted as PASS. Approved
outside-sandbox unit/integration runs passed with only the existing TestClient/httpx
deprecation warning. OpenSpec long-description hints are informational; approved
whole requirements were retained. Real-runtime smoke remains optional NOT RUN,
runtime absent/default port refused as recorded previously; no installation/download.

**Independent conformity:** Fresh read-only `/root/finalization_review` returned
PASS for unchanged reviewed implementation, completion/review evidence and no
unresolved correctness/security findings; subsequent sync preservation review PASS.
Four gateway requirements synchronized, keeping original title/Purpose and all
unmentioned requirement blocks; new local-model-target spec carries every approved
requirement/scenario and verbatim delta Purpose. No application changes.

**Archive execution and blocker:** Normal CLI archive reported success at `openspec/changes/archive/2026-10-03-add-local-model-target/`. Post-archive full suite passed 1123 tests (one existing warning); all/current strict validation passed 8 items each; archived strict validation passed 4; active list is empty. However direct filesystem reads, including approved outside-sandbox attempts by primary and independent reviewer, cannot access the listed archive directory (ENOENT). Archive artifact integrity and evidence-link repair could not be verified/completed. Finalization remains blocked on archive filesystem visibility; no finalization commit was created. The CLI result alone is not claimed as fully verified archival completion.

## 2026-10-04 — Security reporting foundation implementation verification

Change: `add-security-reporting-foundation`. The user's 2026-10-04 instruction
explicitly approved APPLY after a focused scope reduction. Proposal/design/delta
specs/tasks were revised before implementation and strict validation passed.
Exports/manifest/snapshot work, operator CLI, exhaustive filters/groupings,
platform permission auditing and extensive acknowledgement fault matrices were
deferred. The typed reporting boundary and core security guarantees remain.

Implemented closed content-free reporting DTOs and startup-bound projection;
trusted optional configured model metadata; file-backed schema-v1 SQLite event,
control/finding and separate outcome records; typed list/detail/basic summaries;
required JSONL-flush then durable-commit gate; monotonic evaluation/invocation/total
timings; completion-write poisoning with preserved original target outcome; default
startup/storage shutdown and caller-owned injection. HTTP DTOs and policy config
are unchanged. README, reporting documentation, architecture and system summary
record implemented behavior and limits. Current specs remain unsynchronized and
the change is unarchived.

Verification:

- `poetry run pytest tests/unit/test_reporting.py tests/integration/test_reporting_http.py tests/unit/test_service.py tests/unit/test_targets.py tests/unit/test_routing.py tests/integration/test_api.py tests/integration/test_local_model_target.py -q -o faulthandler_timeout=30`: **224 PASS** (outside sandbox).
- Initial full run: 1203 PASS, one compatibility regression for invalid injected
  target-registry startup error type. Existing ValueError behavior restored.
- `poetry run pytest tests/integration/test_extensions.py tests/unit/test_reporting.py tests/integration/test_reporting_http.py -q`: **104 PASS** after fix (outside sandbox).
- Final `poetry run pytest -q`: **1204 PASS**, one pre-existing Starlette/httpx
  deprecation warning, 27.52 seconds (outside sandbox).
- `poetry run ruff check .`: checks PASS, with a traversal warning for the
  pre-existing missing `openspec/changes/archive/2026-10-03-add-local-model-target`
  directory. `poetry run ruff format --check .`: 44 files formatted but traversal
  exits nonzero for that same missing directory. Existing staged archival work
  was preserved, not repaired or included in this change.
- `poetry run ruff check . --extend-exclude openspec/changes/archive/2026-10-03-add-local-model-target`: **PASS**.
- `poetry run ruff format --check . --extend-exclude openspec/changes/archive/2026-10-03-add-local-model-target`: **PASS**, 44 files already formatted.
- `openspec validate add-security-reporting-foundation --strict`: **PASS**.
- `git diff --check`: **PASS**.
- Real Ollama smoke: **NOT RUN**; deterministic verification requires no Ollama.

Sandboxed HTTP tests stalled with asyncio selector/worker waits; reruns outside
the sandbox passed. The new tests cover all actions, safe operational failures,
target success/exception/invalid result, pre-dispatch committed evidence, latency,
unknown completion, restart, distinct aggregate totals/finding multiplicities,
pagination/time bounds, invalid identities/query inputs, sensitive input/output
non-leakage, concurrency, duplicate/orphan/ineligible outcomes, rollback, required
write-lock failure, completion failure, and committed-then-raised acknowledgement.

Independent review is a separate required gate. Fresh correctness reviewer
`/root/reporting_correctness_review` failed to start because the agent service
reported a usage limit; no review verdict was produced. Security reviewer
`/root/reporting_security_review` was requested separately. Review verdicts and
remaining gate status are recorded below when available. This verification entry
does not declare the change complete and does not authorize archival.

Fresh independent security review `/root/reporting_security_review`: **PASS**, no
concrete findings. Independently ran reporting 71 PASS and reporting/service
101 PASS; checked trusted projection, dual gate, completion poisoning, privacy,
parameterized queries and restart semantics. No files modified by reviewer.

Fresh independent correctness review `/root/reporting_correctness_review` resumed
after the initial service limit and returned **FAIL** with one confirmed medium
finding: schema version 1 plus expected table names with wrong columns was accepted
at startup. Reviewer reproduced it and independently ran reporting/service/targets
115 PASS. Before fixing, added three regression variants (wrong columns, omitted
count constraint, missing eligible-outcome trigger): **3 FAIL** as expected. Fixed
startup to compare the actual schema objects against versioned DDL, including
columns, keys/checks/FKs/index and eligibility trigger, before enabling WAL. Invalid
stores are rejected with fixed invalid_reporting_configuration without destructive
recovery. Unit reporting after fix: **74 PASS**. Affected integration and fresh
reviews were requested; final results follow.

Final review/verification after schema fix:

- `poetry run pytest tests/unit/test_reporting.py tests/integration/test_reporting_http.py tests/integration/test_extensions.py -q`: **107 PASS** (outside sandbox).
- Fresh correctness rereview `/root/reporting_correctness_review`: **PASS**, no
  remaining findings. Independently ran reporting/service/targets **118 PASS**.
- Fresh security rereview `/root/reporting_security_review`: **PASS**, no remaining
  bypass or privacy findings. Independently ran reporting/service **104 PASS**,
  including schema regressions; confirmed existing incompatible data is preserved.
- Full pytest, final lint/format, strict validation and whitespace results are
  recorded below. Challenge traceability was updated only after both fresh review
  gates passed. No output, budget, dashboard or cryptographic integrity claims.

- Final `poetry run pytest -q` after confirmed review fix: **1207 PASS**, one
  pre-existing Starlette/httpx deprecation warning, 25.05 seconds.
- Final Ruff lint/format with the pre-existing missing archive path excluded:
  **PASS**, 44 files formatted. Strict change validation and whitespace: **PASS**.
- Required correctness and security review gates: **PASS**. No remaining product
  blocker. The broad unexcluded formatter still encounters the unrelated missing
  archive path; its files/staged state remain preserved. One reporting task-group
  commit is required; no push, spec synchronization or archival is performed.

## 2026-10-04 — Reporting and pending archive finalization

**Authorization:** The user requested “Ok so now everything necessary to archive
and commit all the necessarry changes”, superseding the earlier instruction to
leave reporting unarchived. This authorizes current-spec synchronization, reporting
archive and a finalization commit including the previously staged local-model
closure. No push is authorized or performed.

**Gates:** Reporting implementation is committed at `b801527`. All six tasks are
complete; final full suite 1207 PASS and fresh correctness/security reviews PASS
with no remaining findings are recorded above. Application, tests, configuration,
scripts and dependencies remain byte-identical to `b801527` during finalization
(`git diff HEAD --exit-code -- app tests config scripts pyproject.toml poetry.lock`
PASS). The deterministic suite was not redundantly rerun for documentation-only
archive/spec changes; real Ollama remains optional NOT RUN.

**Spec synchronization:** Added two durable-audit requirements, two target/model
and storage-lifecycle gateway requirements, and the eight-requirement
security-reporting capability; modified only the named local-model output/governance
requirement. Existing main-spec titles/Purpose and unmentioned requirements/scenarios
were preserved. New security-reporting main spec has canonical Requirements format
and verbatim delta Purpose. Every reporting delta block was checked present after
sync, with no delta headers remaining in main specs.

**Archive integrity and recovery:** Reporting artifacts were copied into
`openspec/changes/archive/2026-10-04-add-security-reporting-foundation/`, every one
of nine files verified by SHA-256 before removing the active directory. The tasks
file records the new archive authorization and archive-relative worklog link.

The earlier `2026-10-03-add-local-model-target` directory is listed but remains
unreadable (ENOENT), and recreation fails EEXIST, both inside and outside sandbox.
That filesystem entry was preserved. To safely commit the pending local-model
finalization without losing planning/evidence, all eight original tracked files
were recovered from Git HEAD into the readable
`openspec/changes/archive/2026-10-04-add-local-model-target/` directory. Recovered
bytes were checked against Git, including .openspec.yaml; only tasks worklog link
depth and a recovery/finalization note were then changed. Original reviewed code
and completed test/review evidence are unchanged. No unavailable archive contents
were invented. The old 2026-10-03 worklog blocker is historical; the readable
recovery completes preservation for this commit. The unreadable old entry is still
an environment limitation, not a claimed repaired directory.

**Finalization checks:** `poetry check` PASS; `openspec validate --specs --strict`
9 PASS; reporting active validation PASS before moving; post-archive
`openspec validate --all --strict` 9 PASS and
`openspec validate --archived --strict` 6 PASS (CLI includes the unreadable older
entry); `openspec list --json` returns no active changes. Ruff lint/format PASS,
44 formatted files, excluding only the unchanged unreadable old archive path.
`git diff --check` PASS. No code changes or new scope.

Fresh independent archive/spec-conformity review and commit result are recorded
below once complete.

**Fresh independent finalization review:** `/root/archive_finalization_review`
returned **PASS**, no findings. Independently verified all nine reporting artifacts
and all eight local-model recovered artifacts against Git, delta/main equality,
untouched requirement/Purpose preservation, unchanged implementation, current/all
9 PASS, archived 6 PASS, no active changes and whitespace PASS. The older unreadable
entry is explicitly documented; readable recovery preserves tracked evidence and
does not block this finalization commit.

**Finalization commit:** `chore(openspec): finalize reporting and local model archives`
(resolve its hash from the commit containing this entry). Includes synced current
specs, verified readable archives, prior staged local-model finalization and this
evidence. No implementation changes, push or new OpenSpec change.

## 2026-10-04 — add-semantic-security-control apply verification

Explicit apply approval: user instructed “Explicitly APPROVE and APPLY
`add-semantic-security-control`” with strict approved-artifact scope and no archive.
Primary agent owns implementation and serialized integration. Dedicated local
classifier/control, frozen startup threshold/model binding, disabled baseline and
complete demo policy, semantic attempt timing and exact transactional reporting
v1→v2 migration are implemented. Central policy remains the enforcement authority;
deterministic controls and target generation behavior are unchanged.

Verification evidence:

- Focused evaluator/parser/target/policy/binding/registry suite: **430 PASS**.
- Focused service/reporting/semantic/extension/API suite: **223 PASS**.
- `poetry run pytest tests/unit tests/integration -q`: **1473 PASS**, one existing
  Starlette TestClient deprecation warning, 32.03 seconds. Fake clients and a local
  fake HTTP runtime suffice; no real Ollama/commercial dependency.
- `poetry run ruff check .`: **PASS**, with pre-existing archive traversal warning.
- `poetry run ruff format --check .`: **ENVIRONMENT BLOCKER**, exit 2. The existing
  archive directory entry `openspec/changes/archive/2026-10-03-add-local-model-target`
  appears in scandir but stat returns ENOENT. The error remains outside the sandbox.
  No formatting violations: `poetry run ruff format --check . --exclude
  openspec/changes/archive`: **PASS**, all 50 Python files already formatted.
  The inaccessible archive and local environment configuration were not modified.
- `openspec validate add-semantic-security-control --strict`: **PASS**.
- `git diff --check`: **PASS**.
- Optional real semantic Ollama smoke: **NOT RUN**; no install/download requested.

Initial sandbox HTTP runs hung inside TestClient/AnyIO thread wakeup and were
interrupted. Focused/full HTTP and fake loopback verification was rerun outside the
sandbox with approved execution. The first full run found one legacy fixture
expecting only six disabled-control statuses; corrected to include the explicit
semantic entry, then reran the full suite above.

Independent reviews: pending fresh correctness/specification and security/bypass
review. Completion gate remains open while required exact formatting command is
blocked; no archive requested or performed.

Fresh independent review evidence:

- `/root/correctness_review`: **PASS**, no blocking correctness/specification
  findings. Reviewed final startup binding, central decisions, failed-attempt
  timing/projection and transactional history migration. Independently ran
  **292 focused unit tests PASS** and `git diff --check` PASS. Nonblocking README
  migration-count wording was corrected from five to six additional controls.
- `/root/security_review`: **PASS**, no concrete security/bypass findings.
  Reviewed closed scores and injected runtimes, fail-closed mixed-control paths,
  loopback/no-retry transport, immutable metadata, privacy, required audit gates,
  concurrency and the additive migration. Independently ran **242 semantic tests
  PASS** (16 HTTP selections deselected) and **82 reporting tests PASS**.
- Final affected verification after extending historical preservation fixtures to
  include ALLOW/REDACT/BLOCK, operational events and succeeded/failed/unknown/
  not_invoked history: **130 reporting + semantic tests PASS**, 8.65 seconds.

No confirmed review findings required a code fix or regression cycle. Both final
review responsibilities PASS. OpenSpec tracks **14/15 tasks complete**; task 4.1
remains unchecked because its exact format command fails on the pre-existing
inaccessible archive entry. The full required verification gate therefore remains
open: this change is implemented and reviewed but is not declared complete, not
archived, and task-group commits are deferred until all required checks pass.

## 2026-10-04 — semantic completion blocker resolved

The user authorized investigation and minimal repository-local filesystem repair
of `openspec/changes/archive/2026-10-03-add-local-model-target`, preserving archived
content/history and leaving the passing semantic implementation unchanged.

Root cause: inconsistent case-dependent pathname lookup on the case-insensitive
9p/DrvFS workspace mount (`cache=5`). Directory enumeration reported the lowercase
name and inode 6473924464762285, but lstat/stat/open/listdir for that exact spelling
returned ENOENT. A differently cased spelling resolved the same directory and
revealed its contents. This was a stale lookup/directory-entry state, rather than
permissions or a dangling symlink: the real directory was mode 0755, uid/gid
1000/1000 (`node:node`), with accessible 0755 parent directories and no symlink.

Minimal fix: rename the existing directory through its accessible case alias to a
unique temporary sibling, then rename it back to the original lowercase basename.
No exclusion, ignore rule, chmod/chown, deletion or archived-content rewrite was
used. Before/after manifests verified identical contents, modes, ownership and
symlink state for all 12 entries within that directory. SHA-256 checks also verified
all 53 tracked archived files remained unchanged. The original directory's
pre-existing untracked contents are now visible to Git and remain untracked; they
are not part of the semantic change or its commits.

Final exact verification, after the repair:

- `poetry run ruff format --check .`: **PASS**, exit 0; 50 files already formatted,
  with no exclusion or traversal error.
- `poetry run ruff check .`: **PASS**, exit 0; no traversal warning.
- `poetry run pytest tests/unit tests/integration`: **1473 PASS**, 28.90 seconds;
  one existing Starlette TestClient deprecation warning.
- `openspec validate add-semantic-security-control --strict`: **PASS**.
- `git diff --check`: **PASS**.

The preceding fresh correctness/specification and security/bypass reviews remain
**PASS**: this repair changed no semantic implementation, tests or enforcement
configuration. All completion gates now PASS, task 4.1 is complete and OpenSpec
tracks 15/15 tasks complete. No blocker remains. No archive or push is authorized
or performed. The previously deferred task-group commits may now be created under
the existing AGENTS.md/task instructions.

## 2026-10-04 — semantic change archived

User instruction “Ok so now archive it and do a commit” authorizes finalization
of `add-semantic-security-control`. All 15 tasks, exact verification checks and
fresh independent correctness/specification and security/bypass reviews had PASS
before this archive operation.

Synced the six approved delta capabilities into current specs: decision-audit,
interaction-gateway, local-model-target, policy-decisions, security-reporting and
new semantic-security-detection. Preserved established titles/purposes, untouched
requirements and scenarios; verified every delta statement/scenario after merging.
`openspec validate --specs --strict`: 10 PASS, 0 FAIL. The active change also
passed strict validation immediately before its move.

Archived the complete change, including its metadata and planning evidence, to
`openspec/changes/archive/2026-10-04-add-semantic-security-control/`. Verified moved
file hashes; then corrected worklog links for the additional archive directory
level and recorded the user's archive authorization. No implementation behavior
changed. Prior pre-existing untracked local-model archive remains preserved and
outside this commit. No push was requested.

Post-archive checks: `openspec validate --all --strict` **10 PASS**;
`openspec validate --archived --strict` **7 PASS**; `openspec list --json` reports
no active changes; `poetry run ruff check .`, exact
`poetry run ruff format --check .` (50 files) and `git diff --check` all **PASS**.
No test rerun was needed for this spec/documentation-only finalization; the final
1473-test PASS and both fresh review PASS results remain the implementation evidence.

## 2026-10-04 — interactive dashboard and workbench proposals

The user authorized EXPLORE and exactly two narrowly separated OpenSpec changes,
explicitly prohibiting implementation. Created proposal, focused design, two
capability delta files and unchecked implementation tasks with acceptance criteria
and focused tests for each:

- [add-interactive-security-dashboard-mvp](../openspec/changes/add-interactive-security-dashboard-mvp/proposal.md): independently shippable FastAPI-served read-only dashboard, three typed reporting GET routes, bounded newest-first query and polling. No target invocation or enforcement changes.
- [add-demo-scenario-workbench](../openspec/changes/add-demo-scenario-workbench/proposal.md): dependent UI/catalog extension, exclusive server-owned scenario request variant on the existing interaction API, eleven scenarios, existing real local generation/evaluation adapters and labelled isolated transport faults. Existing reporting contracts remain content-free and unchanged.

Focused exploration used relevant current specs, reporting/query/test boundaries,
interaction API/service/composition, local Ollama/semantic adapters and sample
policies. No application code, runtime configuration or current specs changed.

Both individual `openspec validate <change> --strict` checks: **PASS**.
Both `openspec status --change <change>` checks: **4/4 planning artifacts complete**;
implementation remains unapproved and unchecked. Fresh independent read-only
planning correctness and security/bypass reviews: **PASS** for both changes.
Correctness review identified and verified correction of OpenAPI compatibility
language to permit the documented demo scenario request alternative.
Detailed evidence: [dashboard planning review](../openspec/changes/add-interactive-security-dashboard-mvp/evidence/planning-review.md)
and [workbench planning review](../openspec/changes/add-demo-scenario-workbench/evidence/planning-review.md).

Dashboard MVP is **READY FOR APPLY APPROVAL**, with no planning blockers.
Workbench implementation depends on passing integrated MVP; its live acceptance
requires preprovisioned local models and successful actual-runtime rehearsal.
No implementation tests or live-model checks were run for these planning artifacts;
planning PASS does not satisfy implementation completion/review gates. No apply,
archive or push is authorized or performed.

## 2026-10-04 — dashboard MVP reporting boundary

The user explicitly approved and requested APPLY of
`add-interactive-security-dashboard-mvp` as proposed, excluding workbench and
archive. Approval is recorded in the change tasks. Implemented the bounded typed
newest-first query and three read-only reporting HTTP endpoints with explicit safe
DTOs, strict filter validation, fixed nonreflective errors and no-store responses.
Interaction/core contracts, policy, audit and transports remain unchanged.

Focused verification: `poetry run pytest tests/unit/test_reporting.py
 tests/integration/test_reporting_http.py
 tests/integration/test_dashboard_reporting.py -q`: **150 PASS**, 12.74 seconds;
existing Starlette TestClient deprecation warning. Tests cover mixed counts/timing,
semantic/target identity, unknown/late completion, pagination, UTC/bounds, malicious
or duplicate keys, methods, failed reads, shared poisoned write health and canaries
excluded from reporting/logs. Async HTTP tests require execution outside this
session's restrictive sandbox; sandboxed runs were interrupted after confirmed
runtime hangs. No assertions were weakened. Exact routes/DTOs documented in
`docs/reporting.md`. Task-group commit is deferred until final fresh reviews, so
confirmed findings can be fixed without committing partial/failing work.

## 2026-10-04 — dashboard MVP UI and integrated verification

Implemented local `/dashboard` HTML/CSS/ES modules: metric/status cards,
deterministic/semantic finding totals and rankings, control occurrence rankings,
latency/sample cards, time/action/target/invocation filters, newest-first timeline
and a keyboard-accessible safe detail dialog. Three-second polling refreshes
existing outcomes/detail, pauses while hidden, rejects obsolete filter generations
and preserves visibly stale evidence on read errors. Older pagination is separate
from the live cache. No content, model response or scenario execution surface exists.

Development-only Playwright dependencies are locked. Downloads used writable
`/tmp` cache/browser directories; the container's restricted default cache caused
permission failures, without any dependency substitution. Isolated Chromium tests
use a small process footprint and a persistent test context to fit the shared
512-process ceiling and close the browser reliably. No existing unrelated
processes were modified. The mobile journey first demonstrated overflow from an
absolutely positioned accessible table label; the scrolling container now owns its
positioning. The regression asserts no document overflow at 390px. Mobile View
buttons remain visible beside the horizontally scrolling table.

Integrated verification:

- `poetry run pytest tests/unit tests/integration -q`: **1532 PASS**, 38.73 seconds.
- `PLAYWRIGHT_BROWSERS_PATH=/tmp/dashboard-playwright poetry run pytest tests/browser/test_security_dashboard.py --browser chromium -x -vv -o faulthandler_timeout=30`: **2 PASS**, 19.27 seconds.
- `poetry run ruff check app tests`: **PASS**.
- `poetry run ruff format --check app tests`: **PASS**, 53 files formatted.
- `node --check` for dashboard.js/detail.js/api.js: **PASS**.
- `openspec validate add-interactive-security-dashboard-mvp --strict`: **PASS**.
- `git diff --check`: **PASS**.

The full suite initially identified the historical OpenAPI equality assertion;
it now permits exactly the approved reporting routes/DTOs while continuing the
unchanged interaction contract comparison. Affected extension/reporting checks:
**72 PASS**. No wire compatibility assertion was removed.

Manually inspected actual Playwright desktop (1280px) and mobile (390px) rendered
screenshots, including safe detail. Cards, rankings, timing samples, table and
drawer are legible and usable; browser journey also verifies focus restoration,
empty states, stale/recovery, late completion without new sequence, filter race
and no injected output execution. Temporary screenshots:
`/tmp/security-dashboard-desktop.png`, `/tmp/security-dashboard-mobile.png`,
`/tmp/security-dashboard-mobile-detail.png`. Documented loopback Uvicorn factory
launch and curl summary example were exercised against an isolated `/tmp` store;
startup, read-only empty history and shutdown all succeeded without Ollama.

Implementation verification is passing; fresh independent implementation reviews
are pending. Task-group commits remain deferred until reviews pass. No workbench,
archive, current-spec sync or push has occurred.

## 2026-10-04 — dashboard MVP final reviews and acceptance

Initial independent reviews returned FAIL with two confirmed findings. The first
was omission of historical targets discovered on older pages from the target
filter. The existing first browser journey reproduced the missing option before
`targets(page)` was added after generation validation. It now verifies historical
discovery after 50 newer rows and successful filtering.

The second was FastAPI's automatic reporting trailing-slash redirect reflecting
secret query text in Location without no-store. A regression first reproduced
307. A reporting-only pre-routing guard now returns fixed 404/not_found/no-store.
Six GET/POST cases verify no Location/reflection/calls/mutations; existing
interaction redirects remain compatible. No security core or scope was changed.

Final verification after fixes:

- Affected extension/reporting integration checks: **78 PASS**, 10.57 seconds.
- `poetry run pytest tests/unit tests/integration -q`: **1538 PASS**, 36.55 seconds.
- `PLAYWRIGHT_BROWSERS_PATH=/tmp/dashboard-playwright poetry run pytest tests/browser/test_security_dashboard.py --browser chromium -x -q`: **2 PASS**, 19.67 seconds.
- Ruff check/format (53 files), all three JavaScript syntax checks, strict OpenSpec,
  `poetry check --lock` and `git diff --check`: **PASS**.

Fresh independent corrected-implementation reviews: correctness/specification
(`/root/dashboard_correctness_review`) **PASS**; security/bypass
(`/root/dashboard_security_review`) **PASS**. Security reviewer independently
verified all **55 reporting integration tests**. A temporary account usage-limit
interruption was resolved by retrying the required review; no approval was inferred.
All seven design acceptance criteria pass. Evidence:
[implementation checks](../openspec/changes/add-interactive-security-dashboard-mvp/evidence/implementation-verification.json)
and [review/acceptance record](../openspec/changes/add-interactive-security-dashboard-mvp/evidence/implementation-review.md).

Dashboard MVP implementation is complete with no remaining blockers. Exactly one
Conventional Commit is made per approved task group after passing verification
and reviews. Workbench remains planned only; no archive, current-spec sync or push.
