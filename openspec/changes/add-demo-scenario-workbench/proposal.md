# Proposal

## Why

The implemented interaction workspace can run prepared and custom requests, but its technical labels make outcomes difficult to understand, several existing controls have no prepared example, and required live semantic rehearsal remains failing. This revision makes the demonstration understandable and completes scenario coverage of existing controls while requiring real evaluator verification before acceptance.

## What Changes

- Redesign the shared dashboard shell and overview as a light operator console with compact navigation, readable tables and restrained status colors; add an Interactions view with an immutable server-owned synthetic scenario catalog.
- Add a single-interaction composer with a multiline input, Unicode character count and explicit Local echo / Local model selection, using the existing ordinary `target_id` / `content` request and the application's bound policy.
- Expose safe startup workspace metadata so the composer displays actual enabled controls, policy identity and registered public target/model identities without claiming runtime availability.
- Add a demo-only `scenario_id` request variant to the existing `/v1/interactions` boundary, resolving content, target and startup-bound profile on the server before the existing service pipeline.
- Retain the eleven existing scenarios and add eight examples: GitHub personal/OAuth tokens, labelled SSN, pickle OS/POSIX indicators, base64 execution indicator, email plus SSN redaction, and email plus credential BLOCK precedence. All nineteen use existing controls and fixed server profiles.
- Explain each scenario's test, expected outcome and prerequisites before execution; after execution show the observed decision, readable finding reasons, forwarding consequence and an appropriate next step. Keep technical codes available as supporting detail and make disabled scenarios inspectable without allowing execution.
- Explain custom input's application policy, Local echo versus Local model, and semantic enablement independently of scenario profiles and the selected target.
- Use real `local-ollama` generation and real local semantic evaluation for normal live runs; use deterministic doubles only in tests and explicit transport faults only in outage scenarios.
- Render observed pipeline stages from the interaction outcome and existing safe event detail; distinguish expectations from actual model findings.
- Diagnose live semantic prerequisites and rehearse the configured preprovisioned evaluator without weakening strict classifier validation, thresholds or fail-closed behavior. A model/configuration fix must pass actual benign, attack and hybrid runs; a confirmed adapter/core defect requires a separate reviewed scope amendment before fixing it.
- Deliver allowed generated text only through the existing interaction result into a transient Demo response panel, never reporting/catalog/detail APIs or durable history.
- Protect browser-origin execution with exact same-origin validation while preserving ordinary non-browser clients without Origin; preserve truthful errors, one active run and no automatic POST retries.

Out of scope: new controls, new providers/abstractions, evaluator/target transport or classifier-contract changes, multi-turn chat/history, frontend Ollama access, RAG, memory, tools, output inspection, budgets, authorization, policy reload/editor, per-request policy selection, generic tracing and job infrastructure. Model provisioning is an administrator prerequisite; no automatic download or lifecycle management is added.

## Capabilities

### New Capabilities

- `demo-scenario-workbench`: Nineteen server-owned scenarios, readable test/outcome explanations, custom-policy guidance, truthful startup controls, shared console presentation and evidence-based pipeline results with required live acceptance.

### Modified Capabilities

- `interaction-gateway`: Opt-in scenario request variant, safe workspace metadata and additive code-owned catalog explanations/runtime requirements, using existing interaction response/error envelopes; browser-origin execution requires same origin and ordinary clients without Origin remain compatible.

## Impact

Depends on the implemented, verified and independently reviewed dashboard MVP being integrated first; its acceptance evidence is in worklog. The existing workbench groups 1–3 are implemented; this revision owns additions in `app/control_layer/demo.py`, presentation in `app/dashboard/`, workbench fixtures/tests and operator documentation. The version-1 Demo catalog gains only safe explanatory fields; workspace/reporting and interaction outcome DTOs stay unchanged. Reuse existing registries, policies, service, audit gate, Ollama adapters and schema-v2 reporting. No security-core, transport, sample-policy or database changes are planned.

Challenge grounding: `docs/requirements/challenge-requirements.md` and `docs/reference/ai-control-layer.pdf`, pages 3–4, require an interactive dashboard and permit spontaneous ad-hoc prompts. This change improves that demonstration; it does not claim to implement missing budget, authorization, output-DLP or policy-reload capabilities. Update coverage documentation only after implementation acceptance.

Demo composition remains explicitly enabled for trusted local challenge use and disabled by default. All profile changes are fixed at startup; browser requests cannot set policy, model, endpoint or fault behavior. The user instruction “Update it. Lets go” authorizes this planning revision following the proposed artifact update. Earlier apply approval covers the prior scope only; explicit approval of these revised artifacts is required before implementing the additions.
