# Design

## Context

See proposal.md for motivation. Baseline `136f483` has archived extension points and the deterministic security pack; there are no active prerequisite changes. `targets.py` provides immutable registrations and generic `TargetResult(content)`. `service.py` resolves once, validates all enabled controls, centrally decides/redacts, audits, and invokes the retained adapter once. Target exceptions already become `target_failed`. `api.py` restricts public selection to `local-echo`; its synchronous endpoint uses FastAPI's thread pool. There is no output-control stage.

## Goals / Non-Goals

**Goals:** consume existing contracts to expose one local text model; retain echo and every enforcement/audit guarantee; make absent-runtime startup and deterministic tests work; constrain transport and sanitize failures.

**Non-Goals:** semantic controls, output inspection, reporting/storage, token/resource budgets or accounting, policy reload, authentication/authorization, tools, MCP, cloud providers, provider frameworks, streaming, conversation memory, RAG, downloads and model lifecycle management. Transport/output caps are defensive adapter bounds, not budget governance.

## Decisions

### 1. Ollama through the existing synchronous adapter

Add flat `app/control_layer/ollama_target.py`, owning a frozen `OllamaSettings`, a small settings loader and `OllamaTextTarget`. Implement existing `invoke(Interaction) -> TargetResult`; do not alter the protocol, registry, domain, service, policy or audit. `composition.default_targets()` registers `local-echo` first and `local-ollama` second with server-owned `TargetDefinition` objects. Target lookup remains local and side-effect-free.

Use HTTPX 0.28 (already a dev dependency), promoted to runtime with lockfile update, without the Ollama SDK. Each invocation creates and closes its own synchronous client and response context; inject a client factory/HTTPX transport only into this concrete adapter for deterministic tests. No new core client abstraction. A per-call client avoids shared mutable cookies, buffers and lifecycle changes to injected registries; connection reuse can be considered later if measurement warrants it.

Send one `POST /api/generate` with JSON containing only `model` (settings), `prompt` (exact received interaction.content), and `stream: false`. No template/system overrides, history, tools or adapter-side policy interpretation. Runtime model templates may process the prompt internally; the guarantee is that the submitted prompt field is exactly approved content, not that the runtime uses no template or truncation. Require HTTP 200, JSON object, no `error` key, exact boolean `done: true`, and a Unicode-scalar string `response`. Empty response text is valid. Ignore other generation metadata; never return thinking/context/timing data. Reject malformed UTF-8/JSON, duplicate keys and nonstandard JSON constants. Return only `TargetResult(response)` after validation; response text is untrusted and not security-inspected.

Ollama fits the challenge's explicit local-runtime allowance and offers a simple generation boundary without credentials. A direct embedded inference library would introduce hardware/model-loading complexity; a provider framework would repeat the existing registry architecture. Sources verified 2026-10-03: [generate](https://docs.ollama.com/api/generate), [errors](https://docs.ollama.com/api/errors).

### 2. Small explicit startup configuration outside policy

Read only these environment variables at default target assembly, freeze once until restart, and accept typed settings directly in adapter tests. No YAML configuration framework or policy schema/digest change.

| Variable | Default | Accepted values |
| --- | --- | --- |
| `CONTROL_LAYER_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | HTTP origin with literal `127.0.0.1` or `[::1]`, explicit port 1–65535, optional trailing `/`; no userinfo/path/query/fragment or whitespace |
| `CONTROL_LAYER_OLLAMA_MODEL` | `qwen2.5:0.5b` | 1–128 ASCII characters, grammar `[a-z0-9][a-z0-9._-]*:[a-z0-9][a-z0-9._-]*`; reject `cloud` anywhere in tag |
| `CONTROL_LAYER_OLLAMA_CONNECT_TIMEOUT_SECONDS` | `2` | Finite decimal, 0.1–10 inclusive |
| `CONTROL_LAYER_OLLAMA_RESPONSE_TIMEOUT_SECONDS` | `60` | Finite decimal, 0.1–120 inclusive; read inactivity timeout |
| `CONTROL_LAYER_OLLAMA_MAX_RESPONSE_BYTES` | `65536` | Decimal integer 1024–1048576 inclusive |
| `CONTROL_LAYER_OLLAMA_MAX_OUTPUT_CHARACTERS` | `16384` | Decimal integer 1–65536 inclusive |

Reject empty, malformed, nonfinite and out-of-range values; typed settings reject boolean numeric values. Invalid settings raise a fixed `invalid_target_configuration` startup error without showing values or exception causes. Invalid default settings prevent startup rather than silently replacing them. Explicit injected target registries bypass default target assembly/settings loading, as today, while retaining normal registration and policy validation.

Restrict literal loopback origins to eliminate DNS, remote destinations and accidental cloud endpoints. Local container setups must publish the runtime on host loopback; remote/container-host names are deliberately unsupported. Disable environment proxy use (`trust_env=False`), redirects and transport retries. Never derive URL or model from caller text. The documented runtime deployment must disable Ollama cloud features with `OLLAMA_NO_CLOUD=1`; rejecting cloud-looking tags alone cannot prove a separately administered server's behavior. This is a trusted local runtime, not remote attestation. [Ollama local-only configuration](https://docs.ollama.com/faq#how-do-i-disable-ollama-cloud-features).

One configured model is sufficient: the public request cannot select another model. This is a deployment restriction, not completion of challenge allowed-model policy governance. Full centralized model allow-lists require a later OpenSpec. Future model identity/configuration can extend the adapter behind the same target result boundary; do not add model fields to Interaction, policy or audit now.

### 3. Availability at invocation, never network startup checks

Startup validates settings and registrations only; no runtime executable probe, model list, health call, preloading or download. Both targets remain registered even when Ollama/model is absent. This keeps normal startup and echo independent of server availability and avoids treating a stale health result as eligibility.

After an eligible decision has been emitted, the generation request checks actual availability. Runtime not installed, stopped or unreachable yields connection failure. Missing model ordinarily yields 404. All connection, timeout, HTTP status, protocol, parsing, size and client exceptions become existing `TargetError()` with suppressed exception chaining and then existing service `target_failed` / HTTP 502. No fallback to echo or another model, no retries. The earlier audit remains an eligibility decision, not execution success; do not add a second audit event, synthetic finding or policy BLOCK. Runtime failure cannot weaken policy or bypass required audit.

### 4. Explicit timeout and response boundaries

Set HTTPX connect timeout from connect settings, read timeout from response settings, and write/pool timeouts to connect settings. These are network-operation/inactivity bounds, not a total wall-clock deadline. A slow peer delivering chunks within each read timeout can take longer than 60 seconds; do not promise a 62-second end-to-end SLA. No retry or secondary model call follows a timeout. Closing the client does not guarantee runtime generation cancellation after delivery.

Use a transport streaming read internally only to bound buffering; the Ollama protocol and public API remain non-streaming. Send `Accept-Encoding: identity`, reject non-identity Content-Encoding, check oversized Content-Length when present, and read raw body chunks while enforcing the byte cap independently of Content-Length before JSON parsing. Reject one byte over; exact bound remains eligible if otherwise valid. Validate output Unicode scalar count independently; reject rather than truncate. Bound checks cover chunked/missing/lying length and prompt-bearing error bodies without logging them. Always close response/client, including failure paths. Do not eagerly call a full-body JSON helper before the byte bound.

HTTPX's documented timeouts are per connect/read/write/pool operation: [timeout semantics](https://www.python-httpx.org/advanced/timeouts/). An absolute execution deadline, cancellation and runtime compute budgets are future work. This deliberate local trusted-server trade-off avoids an async refactor or background-thread timeout mechanism that could leave untracked dispatch running.

### 5. Minimal public API change and trusted audit binding

Expand only `InteractionRequest.target_id` to `Literal["local-echo", "local-ollama"]`. Preserve content bounds, strict validation, fields, server UUIDs, null omission, reason/finding/error codes and 200/403/422/503/502 mappings. Unknown IDs (including `ollama`, URLs and sensitive strings) remain 422 before service/audit. An allowed public ID missing from an injected registry retains internal-resolution behavior: sanitized 503 `evaluation_failed`, safe `unresolved` audit and no controls/dispatch. Arbitrary injected internal destinations remain private.

Keep `EchoResult` and its OpenAPI component name for compatibility: `{content: string}` already represents either target's text. Document its historical name and generic meaning; avoid a generated-client-breaking rename or new response fields. The only new OpenAPI difference from the current baseline is the target selector's two-value enum (historical foundation also has the previously approved finding-code broadening).

Retained `RegisteredTarget` remains authoritative for audit and invocation even if registry state changes after resolution. No adapter metadata or untrusted target/model string enters audit. Existing service applies ALLOW original / REDACT centrally transformed / BLOCK zero calls and prevents any runtime request on control, policy or audit failure. Adapter errors can carry prompts/responses/URLs: convert to fixed errors without raw exception/cause, request/response dumps or logging. Application logs and audit must not include raw prompts or responses by default. Successful output can naturally contain prompt text; returning it to the caller is not a privacy log and is not an output-safety guarantee.

### 6. Deterministic tests and optional smoke

Adapter unit tests inject HTTPX MockTransport/client factories to inspect exact JSON, timeout/proxy/redirect settings, call count, response parsing, bounds and prompt-bearing exceptions. A threaded loopback fake HTTP server in integration tests validates the real client boundary, including delayed headers/body, disconnects, status failures, chunked oversized bodies, missing model and concurrent distinct responses. Use small injected timeouts and event/barrier synchronization rather than model inference or fragile sleep-only ordering assertions.

Gateway/service integration uses real six-control composition and a recording audit sink plus the fake runtime. Assert ALLOW original, REDACT transformed, BLOCK/control/audit failures zero HTTP calls, event-before-request, fixed registered identity, exactly one successful invocation, no retry/fallback, unknown public/internal privacy, no prompt/response leakage in audit/errors/log capture and concurrent separation. Preserve all existing detector/policy/audit/routing/echo regressions. Change existing one-target assertions intentionally; preserve immutable historical fixture JSON and normalize only the approved additional target enum in full OpenAPI comparisons.

Optional `scripts/smoke_local_model.py` stays outside pytest discovery and is explicitly invoked with `poetry run python scripts/smoke_local_model.py`. Use an already installed Ollama with cloud disabled and an already provisioned `qwen2.5:0.5b` (operator preparation documented separately; script never installs/pulls). Start the application with an in-memory recording audit sink, issue a short benign local-ollama interaction, assert 200 and scalar text plus pre-dispatch decision evidence; verify echo and a blocked fixture. Print only status/action/length, never prompt/output. No exact generated wording assertion. An absent runtime/model causes a sanitized nonzero result, never silent PASS; omission is recorded as NOT RUN with reason and does not fail normal required checks. Record runtime version/model tag/hardware and observed latency when run. The [documented small model](https://ollama.com/library/qwen2.5:0.5b) is a smoke example, not a security model or pinned artifact guarantee.

### 7. Ownership, files and performance

Implementation owner: primary agent/developer applying this change; one owner integrates shared hotspots. Fresh independent reviewers perform correctness/specification and security/bypass reviews after implementation verification. Read-heavy proposal review is separate from required implementation review.

Expected additions: `app/control_layer/ollama_target.py`, `tests/unit/test_ollama_target.py`, `tests/integration/test_local_model_target.py`, `scripts/smoke_local_model.py`. Expected edits: `composition.py`, `api.py`, `pyproject.toml`, `poetry.lock`, `tests/unit/test_targets.py`, `tests/unit/test_security_pack.py`, `tests/integration/test_extensions.py`, `tests/fixtures/README.md`, README and implemented-state docs (`architecture.md`, `system-summary.md`, challenge `traceability.md`, `worklog.md`) only after implementation. Tests may extend existing API/service coverage if needed within this scope. Current specs update only through later sync/archive after project gates.

Shared hotspots are composition/API, dependency manifest/lock, compatibility assertions and implemented-state docs/current specs. Serialize edits under this owner; dependencies are the already archived extension surface and deterministic pack. Do not change `domain.py`, `registry.py`, `policy.py`, `service.py`, `audit.py`, detectors, enforcement config/signature catalog, fixture JSON or AGENTS.md. If those contracts must change, stop that scope and revise planning before applying.

Shared frozen settings, no per-request adapter state and per-call clients permit simultaneous thread-pool invocation; runtime requests may queue independently. No global adapter serialization, admission limiter or async architecture. Expected latency is hardware/model/load/queue dependent, typically seconds and potentially timeout-scale during cold loads; do not promise benchmark numbers. Audit evaluation_duration_ms continues to exclude model time. A later reporting layer can observe monotonic invocation duration, status and runtime token metadata without raw text; no metrics/events/storage hooks are implemented now. Later budget checks belong before dispatch in central enforcement, not inside this adapter.

## Risks / Trade-offs

- Missing runtime/model → lazy sanitized failure; echo/startup still work with valid settings.
- Long inference/thread occupation → bounded I/O inactivity, explicit size caps, documented lack of total deadline; throughput/budgets deferred.
- Response may be unsafe or repeat secrets → document no output inspection; no default content logs.
- Trusted local daemon could proxy/retain content → loopback/no proxies/cloud-disabled deployment; no claim of runtime attestation or log control outside this application.
- Model tags can change and generation is nondeterministic → smoke records deployed version/model, ordinary tests use deterministic doubles.
- Configurable model/runtime may truncate context → document runtime behavior; do not claim adapter-level context capacity or token governance.

## Migration Plan

After explicit scope approval: add dependency/adapter tests, integrate registration/API, complete deterministic verification and fresh reviews, then update implemented docs/coverage. No policy migration is required and default digest stays unchanged. Existing echo clients continue to work; clients generating target enums may regenerate for the added value. Operators install/provision runtime separately and run local-only; no server is required for application installation/tests. Rollback code/dependency changes restores echo-only API with unchanged policy; never fall back dynamically on model failures. Archive only after verification and fresh independent PASS, with worklog evidence referenced from tasks.
