git# Worklog

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
