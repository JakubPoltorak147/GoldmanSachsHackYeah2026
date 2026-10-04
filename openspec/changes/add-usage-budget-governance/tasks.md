# Tasks

Apply approval: GRANTED on 2026-10-04 by "ZRób ten budżet jedziesz", replying to the explicit question asking for approval of this change's scope and the assumptions listed in design.md (global scope, character-based input-token estimate, generous default limits, 403 for budget blocks, in-memory counters, no short-circuit of expensive controls). Scope: groups 1–4 as written, including documentation and the evaluator harness. Excludes archive and push (separate instructions). Earlier "dorób jeszcze jeden feature..." authorized proposing only.

Ownership: one primary agent owns the entire change (touches shared hotspots `policy.py`, `composition.py`, `api.py`, `config/*.yaml`, dashboard assets, docs). No other active change may edit these concurrently. Review agents are read-only and do not implement. One Conventional Commit per completed group after required checks pass; never push or archive without separate instruction.

Status 2026-10-04 (user asked to wrap up and commit/push): groups 1–3 implemented and committed together; evaluator harness verified live (12/12). Deviations from this plan: added `config/policy-evaluation-offline.yaml` (model-free profile); evaluation limits use 20 requests instead of 10 so the harness's 10 functional cases fit; the harness has no separate unit test. NOT done: independent reviews (4.3), full docs sweep (4.1: architecture/system-summary/reporting/traceability not updated), worklog entry. The change is therefore NOT complete and NOT archivable. Verification run: 1,340 unit + 308 integration tests pass; known environment-only failures on Windows, also failing on pristine HEAD: `test_schema_mismatch_symlink_and_private_defaults` (file modes), 6 setup errors from a >32,767-character env var on emoji-parametrised tests, and 5 browser tests in `test_security_dashboard.py`/`test_demo_workbench.py`; the new `test_usage_panel.py` passes.

## 1. Policy limits and control

- [ ] 1.1 Add regression-first tests then implement `usage_control.py`: window state with lock and injected monotonic clock, token estimate, three spanless findings, atomic check-and-charge, breach counters. Verify `tests/unit/test_usage_control.py` covers allowed, exact boundary, oversize, token exhaustion, multi-breach, reset, non-BMP, concurrency (no over-admission) and shadow counters.
- [ ] 1.2 Extend `policy.py` with strict `limits` parsing, digest inclusion and snapshot validation; add bind step in `composition.py` mirroring semantic threshold binding; register `usage-budget` before `semantic-security`. Verify `tests/unit/test_policy.py`/`test_binding.py` cover valid/invalid limits, REDACT rejection, migration failure, digest change and unchanged historical digests with explicit legacy registries.
- [ ] 1.3 Update `config/policy.yaml`, `config/policy-semantic-demo.yaml` and add `config/policy-evaluation.yaml` (limits per design); fix existing fixtures deliberately. Verify the full existing unit/integration suites remain green.

## 2. Enforcement, reporting and usage endpoint

- [ ] 2.1 Integration tests then wiring: budget BLOCK via HTTP (403, zero target calls, audit/report record), shadow ALLOW, burst exhaustion, privacy canary across audit/reporting/usage/errors. Verify `tests/integration/test_usage_budget.py`.
- [ ] 2.2 Add `GET /v1/usage` closed DTO, no-store, sanitized errors, no-charge reads, disabled state. Verify snapshot, repeat-read, disabled, query/method errors in the integration suite.

## 3. Dashboard and evaluator harness

- [ ] 3.1 Add Usage and budget panel to the overview using the visibility-aware polling pattern, with enabled/disabled/stale/unavailable states. Verify one browser journey in `tests/browser/` and no regression of existing journeys.
- [ ] 3.2 Add `scripts/evaluate_gateway.py` (httpx only, local echo, PASS/FAIL table, exit status) with deterministic unit tests of its case logic using a fake transport, and an integration run against the evaluation policy. Verify zero exit with all controls on and non-zero with a control disabled.

## 4. Documentation, verification and review

- [ ] 4.1 Update README (budget section), `docs/demo.md`, `docs/architecture.md`, `docs/system-summary.md`, `docs/reporting.md` and `docs/requirements/traceability.md` (PARTIAL: request and input-token budgets only) to accepted behaviour.
- [ ] 4.2 Run `poetry run pytest tests/unit tests/integration`, `poetry run pytest tests/browser --browser chromium`, `poetry run ruff check .`, `poetry run ruff format --check .`, `openspec validate --all --strict`, `git diff --check`; record in `docs/worklog.md` and link here.
- [ ] 4.3 Delegate fresh specification/correctness and security/bypass reviews to non-implementing agents; fix confirmed findings regression-first and obtain fresh PASS from both. Record evidence and link here.
- [ ] 4.4 Declare complete only after 4.2 and 4.3 PASS. Archive requires separate user instruction.
