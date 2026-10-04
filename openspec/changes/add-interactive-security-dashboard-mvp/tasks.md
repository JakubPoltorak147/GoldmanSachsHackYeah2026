# Tasks

Approval: GRANTED on 2026-10-04 by the user instruction “Explicitly APPROVE and APPLY: `add-interactive-security-dashboard-mvp`” and “Implement the approved proposal/design/tasks as written.” Scope is this dashboard MVP only, including focused/full verification, fixes and fresh correctness/security reviews. The user explicitly excludes workbench implementation and archive. Implementation owner: primary apply agent.

Owner: primary apply agent. Dependency: existing archived reporting/semantic foundations only; independently ship before `add-demo-scenario-workbench`. Scope/ownership and acceptance criteria are in design.md. Shared `api.py` and reporting query changes are serially owned; no overlapping implementation with change 2. Each implementation group gets one Conventional Commit only after its required checks pass; never push.

## 1. Safe reporting boundary

- [x] 1.1 Add bounded typed `list_recent_events` in `reporting_store.py`, preserving ascending queries; verify newest-first/filter/cursor/multi-page/concurrent-insert and late-completion tests in `tests/unit/test_reporting.py` with `poetry run pytest tests/unit/test_reporting.py`.
- [x] 1.2 Implement `reporting_api.py` explicit DTOs, three GET routes, paired/default UTC filters, 100-row cap, signed-64-bit cursors, no-store responses and fixed errors; wire router in `api.py` and verify `tests/integration/test_dashboard_reporting.py` covers defaults/bounds/duplicate/unknown params/detail/errors/methods, zero mutation/calls and existing schema compatibility.
- [x] 1.3 Add response canary, distinct-count/sample/status, poisoned-health and failed-read tests using existing mixed evidence and fake transports; verify reporting replies contain no forbidden data and failed reads never become zero/empty with `poetry run pytest tests/unit/test_reporting.py tests/integration/test_reporting_http.py tests/integration/test_dashboard_reporting.py`.
- [x] 1.4 Update `docs/reporting.md` with implemented route/DTO/query/error/timing contracts and local-only boundary; verify examples against the integration fixture and record group verification in `docs/worklog.md`.

## 2. Polished read-only dashboard

- [x] 2.1 Add local `app/dashboard/` HTML/CSS/ES modules and FastAPI mounts with shared API client/navigation slot/detail renderer; implement cards/rankings/timeline/filter controls/null labels; verify `/dashboard` and assets serve and two-keyboard/viewport visual checks meet design acceptance.
- [x] 2.2 Implement three-second nonoverlapping polling, refresh now, filter-generation protection, completion/detail refresh and truthful empty/loading/stale/error UI; verify deterministic browser tests cover late completion, request race and unavailable-to-recovered reads without losing selected UUID.
- [x] 2.3 Add only development `playwright` and `pytest-playwright` dependencies plus Chromium setup documentation; place the two essential journeys in `tests/browser/test_security_dashboard.py`, using a temporary safe store and deterministic app server. Verify `poetry run pytest tests/browser/test_security_dashboard.py --browser chromium`, text-only rendering, keyboard close/focus and narrow viewport. No browser security-control tests or live Ollama.
- [x] 2.4 Document loopback launch, visible time windows, null/unknown semantics and implemented frontend composition in `docs/reporting.md`/`docs/architecture.md`; verify documented commands and record manual visual checks/group verification in `docs/worklog.md`.

## 3. Integrated verification and independent review

- [x] 3.1 Run `poetry run pytest tests/unit tests/integration`, the two browser journeys, `poetry run ruff check app tests`, `poetry run ruff format --check app tests` and `openspec validate add-interactive-security-dashboard-mvp --strict`; verify PASS and record actual commands/results in worklog, linked here.
- [x] 3.2 Delegate fresh implementation specification/correctness and security/bypass reviews to agents that did not implement; verify both return PASS with concrete file/scenario evidence, fix confirmed findings with regression tests first and request fresh reviews after fixes. Record worklog review links here.
- [x] 3.3 Verify all design acceptance criteria, docs and evidence links; declare complete only after required verification/reviews PASS, keep archive as a separately authorized action and preserve reporting/interaction extension contracts for change 2.

Evidence: [planning review](evidence/planning-review.md), [implementation checks](evidence/implementation-verification.json), [fresh implementation reviews and acceptance criteria](evidence/implementation-review.md), and [worklog](../../../docs/worklog.md). Final full verification: 1538 unit/integration tests and two browser journeys PASS. Fresh correctness/specification: PASS. Fresh security/bypass: PASS. All seven design acceptance criteria pass. Implementation complete; no archive, current-spec sync, workbench implementation or push.
