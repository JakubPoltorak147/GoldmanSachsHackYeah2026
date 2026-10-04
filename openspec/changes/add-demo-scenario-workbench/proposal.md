# Proposal

## Why

The reporting dashboard explains historical decisions; judges also need a compelling way to trigger real security evaluation and local generation. A curated Attack Lab can demonstrate enforcement and its evidence without building another LLM application.

## What Changes

- Extend the first change's UI shell with a Demo view and immutable server-owned synthetic scenario catalog.
- Add a demo-only `scenario_id` request variant to the existing `/v1/interactions` boundary, resolving content, target and startup-bound profile on the server before the existing service pipeline.
- Exercise benign generation, PII redaction, supported credential/private-key/signature blocks, three semantic attack categories, hybrid controls and two labelled unavailable-transport demonstrations.
- Use real `local-ollama` generation and real local semantic evaluation for normal live runs; use deterministic doubles only in tests and explicit transport faults only in outage scenarios.
- Render observed pipeline stages from the interaction outcome and existing safe event detail; distinguish expectations from actual model findings.
- Deliver allowed generated text only through the existing interaction result into a transient Demo response panel, never reporting/catalog/detail APIs or durable history.

Out of scope: new providers/abstractions, free-form prompt editor, frontend Ollama access, RAG, memory, tools, output inspection, budgets, policy reload/editor, generic tracing and job infrastructure.

## Capabilities

### New Capabilities

- `demo-scenario-workbench`: Server-owned catalog, profile-bound execution and evidence-based live pipeline presentation.

### Modified Capabilities

- `interaction-gateway`: Opt-in scenario request variant using the existing response/error envelopes; original target/content requests remain compatible.

## Impact

Depends on `add-interactive-security-dashboard-mvp` being implemented, verified, independently reviewed and integrated first. Extend its navigation and renderers; consume its reporting routes unchanged. Own new `app/control_layer/demo.py` and Demo assets/tests, with narrowly scoped changes to `api.py` and `composition.py`. Reuse existing registries, policy files, `InteractionService`, `PersistentAuditSink`, Ollama adapters and schema-v2 reporting. No reporting schema or security-core redesign.

Demo composition is explicitly enabled for trusted local challenge use and disabled by default. All profile changes are fixed at startup; browser requests cannot set policy, model, endpoint or fault behavior. A second approval is required before implementing this dependent change.
