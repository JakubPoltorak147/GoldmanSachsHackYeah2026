# Proposal

## Why

The reporting dashboard explains historical decisions but cannot run predefined cases or accept the spontaneous prompts expected by the challenge. An interaction workspace with a restrained operator interface will let judges exercise real enforcement and inspect its evidence.

## What Changes

- Redesign the shared dashboard shell and overview as a light operator console with compact navigation, readable tables and restrained status colors; add an Interactions view with an immutable server-owned synthetic scenario catalog.
- Add a single-interaction composer with a multiline input, Unicode character count and explicit Local echo / Local model selection, using the existing ordinary `target_id` / `content` request and the application's bound policy.
- Expose safe startup workspace metadata so the composer displays actual enabled controls, policy identity and registered public target/model identities without claiming runtime availability.
- Add a demo-only `scenario_id` request variant to the existing `/v1/interactions` boundary, resolving content, target and startup-bound profile on the server before the existing service pipeline.
- Exercise benign generation, PII redaction, supported credential/private-key/signature blocks, three semantic attack categories, hybrid controls and two labelled unavailable-transport demonstrations.
- Use real `local-ollama` generation and real local semantic evaluation for normal live runs; use deterministic doubles only in tests and explicit transport faults only in outage scenarios.
- Render observed pipeline stages from the interaction outcome and existing safe event detail; distinguish expectations from actual model findings.
- Deliver allowed generated text only through the existing interaction result into a transient Demo response panel, never reporting/catalog/detail APIs or durable history.
- Protect browser-origin execution with exact same-origin validation while preserving ordinary non-browser clients without Origin; preserve truthful errors, one active run and no automatic POST retries.

Out of scope: new providers/abstractions, multi-turn chat/history, frontend Ollama access, RAG, memory, tools, output inspection, budgets, policy reload/editor, per-request policy selection, generic tracing and job infrastructure.

## Capabilities

### New Capabilities

- `demo-scenario-workbench`: Server-owned scenarios, custom interaction input, truthful startup controls, shared console presentation and evidence-based pipeline results.

### Modified Capabilities

- `interaction-gateway`: Opt-in scenario request variant and safe workspace metadata, using existing response/error envelopes; browser-origin execution requires same origin and ordinary clients without Origin remain compatible.

## Impact

Depends on the implemented, verified and independently reviewed dashboard MVP being integrated first; its acceptance evidence is in worklog. Own `app/dashboard/` presentation changes, new `app/control_layer/demo.py` and workbench tests, with narrowly scoped changes to `api.py` and `composition.py`. Preserve reporting routes/DTOs and safe detail rendering behavior while restyling overview and navigation. Reuse existing registries, policy files, `InteractionService`, `PersistentAuditSink`, Ollama adapters and schema-v2 reporting. No reporting schema or security-core redesign.

Challenge grounding: `docs/requirements/challenge-requirements.md` and `docs/reference/ai-control-layer.pdf`, pages 3–4, require an interactive dashboard and permit spontaneous ad-hoc prompts. This change improves that demonstration; it does not claim to implement missing budget, authorization, output-DLP or policy-reload capabilities. Update coverage documentation only after implementation acceptance.

Demo composition is explicitly enabled for trusted local challenge use and disabled by default. All profile changes are fixed at startup; browser requests cannot set policy, model, endpoint or fault behavior. A second approval is required before implementing this dependent change.
