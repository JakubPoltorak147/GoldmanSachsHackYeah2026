# Proposal

## Why

The verified control layer currently governs only deterministic local echo. A real local text model will demonstrate centralized guardrails on an actual AI interaction without paid APIs or cloud credentials, using the existing extension surface.

## What Changes

- Add one synchronous Ollama text adapter, publicly selected as `local-ollama`, alongside unchanged `local-echo`.
- Configure one operator-selected local model and bounded connection/read timeouts and response limits outside security policy. Validate settings at startup without contacting a model server; check availability only during eligible invocation.
- Send exactly centrally approved content to non-streaming generation after required audit. Return text through existing `TargetResult`; sanitize every runtime failure through existing target-failure semantics.
- Add deterministic transport, gateway, privacy and concurrency tests, and an optional real-runtime smoke test that requires separately provisioned Ollama/model.
- Preserve all deterministic controls, retained registered target identity, central enforcement, audit privacy, existing HTTP fields/statuses and echo compatibility. Model output is not security-inspected.

## Capabilities

### New Capabilities

- `local-model-target`: bounded local generation, operator configuration, availability/failure behavior, privacy and deterministic integration testing.

### Modified Capabilities

- `interaction-gateway`: admit the additional explicit public target and register it in default composition while preserving existing request/result contracts and private internal destinations.

`decision-audit` and `policy-decisions` remain unchanged: this adapter consumes their existing guarantees without introducing a second enforcement or audit path.

## Impact

New flat Ollama adapter/configuration module and tests; narrow composition/API integration; promote existing HTTPX dependency to runtime and update lockfile; update compatibility assertions and documentation during implementation. No Ollama SDK, generic provider/configuration framework or security-core redesign.

Primarily advances challenge integration with a real AI system, practical local deployment and centralized guardrails without commercial services. It does not complete allowed-model policy governance, semantic guardrails, budgets, reporting/dashboard or output filtering. Streaming, tools, memory, RAG, cloud providers, model downloads/lifecycle, authentication and policy reload are excluded. This proposal authorizes planning only; apply requires explicit scope approval.
