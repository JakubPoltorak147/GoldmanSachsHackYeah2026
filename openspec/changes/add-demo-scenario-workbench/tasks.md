# Tasks

Approval: NOT GRANTED. The user instruction dated 2026-10-04 authorizes proposal artifacts and explicitly forbids implementation. Record a new explicit approval of this change's scope here before implementation; approval of dashboard MVP alone does not cover this workbench.

Owner: primary apply agent. Hard dependency: `add-interactive-security-dashboard-mvp` implemented, verified, freshly independently reviewed PASS and integrated. Consume its API/DTO/assets unchanged. Serialize `api.py`/`composition.py` edits after prerequisite integration. Own `demo.py`, Demo assets and tests; do not edit security core, detectors, transports, reporting schema or sample policy behavior. Each implementation group gets exactly one Conventional Commit after checks pass; never push.

## 1. Server-owned catalog and startup profiles

- [ ] 1.1 Implement eleven immutable synthetic scenario definitions in `demo.py` with server-only payloads, safe public metadata and expectation/prerequisite/simulation labels; verify `tests/unit/test_demo_catalog.py` checks all IDs, bounds, supported bearer/PEM/signature/email shapes, synthetic-key construction and absence of raw payloads from public catalog.
- [ ] 1.2 Add strict default-off Demo and semantic-Demo flags and fixed startup profile assembly using existing policy files, registries, adapters/client-factory seams and profile-specific persistent audit projection with shared store/sink; verify `tests/unit/test_demo_composition.py` checks frozen settings/identities, no startup runtime calls, invalid profile fail-closed and isolated labelled fault injection.
- [ ] 1.3 Document flags, profiles, fixed-model binding, simulated outages and genuine unavailable-runtime rehearsal in `docs/demo.md`; verify examples against catalog/composition tests and record group checks in worklog. No model installation/download during tests.

## 2. Governed scenario interaction boundary

- [ ] 2.1 Add safe GET catalog and the exclusive scenario_id request variant to `/v1/interactions`; resolve server-owned UUID/content/local-ollama/profile then reuse existing service and response serializer. Verify `tests/integration/test_demo_api.py` covers disabled/unknown/mixed/extra/wrong-type input, strict same-origin checks and unchanged ordinary interaction envelopes in both modes.
- [ ] 2.2 Add deterministic integration fixtures with real detectors, fake local generation transport and fake semantic scores; verify all eleven outcomes, exact redacted-only forwarding, audit-before-once invocation, deterministic/semantic BLOCK zero-generation, hybrid precedence and sanitized outage status with `poetry run pytest tests/unit/test_demo_catalog.py tests/unit/test_demo_composition.py tests/integration/test_demo_api.py`.
- [ ] 2.3 Add canary/forged-override, concurrent-profile identity, shared poisoned gate, completion-write/read failure and missing-record regressions; verify catalog/reporting/log/history exclude input/transformed content/output/semantic responses/scores/exceptions while only existing successful interaction result contains generated text.
- [ ] 2.4 Update `docs/demo.md` with executable route/validation/privacy/failure contracts and safe evidence semantics; verify with HTTP fixture commands and record group verification in worklog.

## 3. Clickable Demo and observed pipeline

- [ ] 3.1 Extend dashboard navigation/styles with grouped scenario cards, expectation chips, disabled prerequisites and one-run controls; consume existing catalog/interaction/reporting clients without changing reporting DTOs. Verify deterministic browser journey shows benign actual text, REDACT and BLOCK with matching new timeline events.
- [ ] 3.2 Render post-response stages from outcome plus UUID detail, separate evaluator/target identities/status and measured timing, not-reached/disabled/unknown/unavailable states and expected/observed mismatch; verify second browser journey covers semantic failure without fabricated BLOCK, target failure with retained eligible decision, unavailable reporting and no automatic POST retries.
- [ ] 3.3 Keep allowed output exclusively in a transient text-only uninspected result panel, clear on new run/navigation, avoid browser storage and fake progress; verify HTML-like canary remains inert, storage/history excludes it and concurrent UI responses cannot cross runs using `poetry run pytest tests/browser/test_demo_workbench.py --browser chromium`.
- [ ] 3.4 Document the implemented view, evidence correlation and operator click path in `docs/demo.md`/`docs/architecture.md`; verify desktop/narrow viewport/keyboard visual walkthrough and record group verification in worklog.

## 4. Integrated verification and live rehearsal

- [ ] 4.1 Run `poetry run pytest tests/unit tests/integration`, `poetry run pytest tests/browser --browser chromium`, `poetry run ruff check app tests`, `poetry run ruff format --check app tests` and `openspec validate add-demo-scenario-workbench --strict`; verify deterministic PASS without real Ollama and link results from worklog here.
- [ ] 4.2 Rehearse eleven clicks with preprovisioned real generation/evaluator models: observe benign response, real REDACT dispatch, deterministic blocks, three semantic findings/central BLOCK and hybrid findings; exercise labelled transport faults and genuine stopped-runtime failure. Verify safe timings/identities/evidence without output logs; record PASS/FAIL/NOT RUN and runtime prerequisites separately. A failed/not-run required live demonstration leaves demo acceptance incomplete even if automated tests PASS.
- [ ] 4.3 Delegate fresh specification/correctness and security/bypass implementation reviews to nonimplementing agents; verify final PASS for both, fix confirmed findings with regression tests first and obtain fresh review after fixes. Record worklog evidence and references here.
- [ ] 4.4 Verify all design acceptance criteria including required live-demo evidence and prerequisite integration; declare complete only when required verification/review/demo acceptance PASS, leave archive separately authorized and preserve existing reporting security guarantees.

Evidence: implementation pending. [Planning validation/review](evidence/planning-review.md) is PASS, recorded in [worklog](../../../docs/worklog.md); it does not satisfy implementation/live verification or authorize apply. Dependency must be integrated first.
