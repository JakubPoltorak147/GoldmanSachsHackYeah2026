# Planning validation and independent review

Date: 2026-10-04. Scope: proposal/design/delta specs/tasks only. No apply, implementation, real-runtime check or archive.

## Original scenario-only scope

- `openspec validate add-demo-scenario-workbench --strict`: PASS.
- `openspec status --change add-demo-scenario-workbench`: 4/4 planning artifacts complete; implementation tasks remain unchecked.
- Fresh read-only specification/correctness reviewer `/root/planning_correctness`: PASS after correcting retained OpenAPI compatibility language in the interaction-gateway delta to permit the explicit scenario request alternative. No remaining blocker; extension consumes unchanged dashboard/reporting contracts and matches actual service semantics.
- Fresh read-only security/bypass reviewer `/root/planning_security`: PASS; no genuine planning blocker. Server-owned scenario/profile selection, existing service gates, profile-specific trusted projections and shared store health are consistent with available seams. Raw output is isolated to the existing immediate interaction result, not reporting/catalog/history; simulated faults are explicitly labelled and do not mint decisions.

Dependency: implement, verify, independently review and integrate dashboard MVP first. Live/manual demo acceptance later requires preprovisioned real local generation/evaluator models and successful rehearsal; this was not claimed or tested during planning. Separate explicit apply approval is required. See [worklog](../../../../docs/worklog.md) entry “interactive dashboard and workbench proposals”.

## Revised scope: custom interactions and operator console

Authorization: the user replied “Do it” after the primary proposed revising the existing workbench's proposal, design, delta specs and tasks to add custom input and the visual redesign before apply. This authorizes the planning revision only; implementation approval remains NOT GRANTED in tasks.md.

Revised five planning files include the single-interaction composer, ordinary application-policy binding, immutable scenarios, safe startup workspace metadata, labelled transient echo/model results, a shared light console, Unicode scalar validation, one run lock across navigation and the explicit ordinary browser-origin boundary tightening. Reporting APIs/DTOs and security-core behavior remain unchanged. No new capability file or second execution plan was created.

Grounding: primary read `docs/requirements/challenge-requirements.md`, coverage ledger and the original four-page `docs/reference/ai-control-layer.pdf` during exploration. Because pdftotext was absent, the primary extracted text from the PDF's compressed content streams/font mappings with a read-only Python command. Pages 3–4 establish the interactive dashboard/ad-hoc evaluation motivation; no budget, authorization, output-DLP or policy-reload coverage is claimed. Reviewers used the challenge summary; neither reviewer claimed direct PDF extraction.

Verification:

- `openspec validate add-demo-scenario-workbench --strict`: PASS.
- `openspec validate --all --strict`: 12 PASS, 0 FAIL. Informational long-requirement notices concern preserved existing requirement blocks and do not invalidate the changes.
- `git diff --check`: PASS.
- Application tests and real-runtime rehearsal: NOT RUN; no implementation changed.

Fresh read-only planning reviews:

- `/root/revised_plan_correctness`: PASS. Checked artifacts against existing API/composition/policy/audit boundaries, complete modified gateway scenarios, custom-policy/profile isolation, scalar/privacy/race verification and explicit implementation gates. A compatibility wording clarification was applied to design's scenario boundary and acceptance criterion 4; reviewer verified the latest text. No blocking findings remain.
- `/root/revised_plan_security`: PASS. Checked exact origin validation and originless compatibility, startup metadata privacy/readiness, transient scalar-safe custom input and labelled echo/model output, navigation lock, profile isolation/shared poison health and required adversarial/live/independent verification. No blocking security or bypass findings.

Outcome: revised planning is ready for explicit scope approval. All implementation tasks remain unchecked; no apply, current-spec synchronization, archive or push. Dashboard MVP implementation acceptance exists already; verify its integrated baseline before applying this dependent change. Required real-model rehearsal and fresh implementation reviews are future acceptance gates, not satisfied by this planning PASS.
