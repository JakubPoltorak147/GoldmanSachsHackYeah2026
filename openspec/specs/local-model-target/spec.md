# local-model-target Specification

## Purpose

Provide one bounded local text-model destination behind existing centralized input enforcement and required decision audit, without commercial service dependencies.

## Requirements

### Requirement: Local registered text generation
The system SHALL expose `local-ollama` alongside `local-echo`, using one operator-configured local model. Eligible dispatch SHALL submit one non-streaming generation request containing exactly approved content and return only generated text. The adapter MUST NOT interpret findings, change enforcement, retry or fall back to another target/model.

#### Scenario: Successful generation
- **WHEN** eligible dispatch receives a valid completed generation response
- **THEN** exactly one runtime generation request uses the configured model and the caller receives its response text through the existing content-only result

#### Scenario: Original and centrally redacted prompts
- **WHEN** central policy selects ALLOW or REDACT for a local-model interaction
- **THEN** the submitted prompt is respectively exact original content or exact centrally redacted content, with no adapter-added prompt/history

#### Scenario: Closed dispatch gates
- **WHEN** policy selects BLOCK or evaluation or required audit emission fails
- **THEN** there are zero target-generation runtime requests, including target probes; a separately enabled semantic evaluator can already have made its bounded classification request during evaluation, without invoking this target adapter

### Requirement: Explicit bounded runtime settings
Runtime settings SHALL be validated and frozen at startup outside security policy: loopback base origin, single model, connection/read timeouts, response byte cap and output character cap. Invalid settings MUST fail startup with fixed sanitized configuration error, without fallback. Callers MUST NOT set runtime/model/limits through interaction requests.

#### Scenario: Documented defaults
- **WHEN** runtime environment settings are absent in default composition
- **THEN** settings are HTTP loopback port 11434, model `qwen2.5:0.5b`, connect 2 seconds, read inactivity 60 seconds, 65536 response bytes and 16384 output characters

#### Scenario: Supported overrides
- **WHEN** an operator configures a literal 127.0.0.1 or ::1 HTTP origin with explicit port 1–65535, a 1–128-character ASCII model matching `[a-z0-9][a-z0-9._-]*:[a-z0-9][a-z0-9._-]*` with no `cloud` in its tag, finite connect 0.1–10 seconds, read 0.1–120 seconds, integer bytes 1024–1048576 and characters 1–65536
- **THEN** startup accepts and freezes the settings until restart without changing security policy or its digest

#### Scenario: Invalid or unsafe settings
- **WHEN** settings are empty, malformed, out of bounds, nonfinite, wrong typed values including numeric booleans, or the URL includes a non-loopback hostname, credentials, path beyond optional trailing slash, query, fragment or whitespace
- **THEN** default startup fails with fixed invalid_target_configuration without reflecting settings or exception causes

#### Scenario: Public model override
- **WHEN** a caller adds model, URL or timeout fields to a public interaction
- **THEN** the gateway rejects it under unchanged extra-field validation without runtime dispatch

### Requirement: Invocation-only availability
Normal startup and required tests MUST NOT require an installed/running runtime or existing model. Startup SHALL perform only local configuration/registration validation. Actual availability SHALL be determined during eligible generation; absence or unavailability MUST NOT silently change target/model or disable controls.

#### Scenario: Runtime not installed or stopped
- **WHEN** valid application configuration starts without Ollama installed or running
- **THEN** startup succeeds without network probes, local echo succeeds when semantic evaluation is explicitly disabled, and an otherwise eligible model request returns sanitized target_failed after its decision audit; enabled semantic unavailability instead returns evaluation_failed before target dispatch

#### Scenario: Model absent
- **WHEN** the configured model does not exist and generation returns a missing-model status
- **THEN** the request returns sanitized target_failed without downloading a model, fallback, retry or synthetic security decision

### Requirement: Bounded transport without destination escape
Generation SHALL use only the configured loopback origin with redirects, environment proxies and retries disabled. Connection timeout SHALL bound connection establishment; response timeout SHALL bound read inactivity, not total execution. Write/pool timeouts SHALL use the connection bound. Responses SHALL be bounded before parsing and rejected rather than truncated on overflow.

#### Scenario: Connection and response delays
- **WHEN** connection establishment exceeds its configured bound or response headers/body stall longer than read inactivity bound
- **THEN** dispatch fails as sanitized target_failed, closes resources and makes no retry; the earlier decision audit remains intact

#### Scenario: Active slow response
- **WHEN** a response continues delivering within each read timeout
- **THEN** documentation does not claim an absolute wall-clock deadline or runtime cancellation, and byte/output limits still apply

#### Scenario: Redirect or environment proxy
- **WHEN** a server redirects to another destination or the application environment configures a proxy
- **THEN** approved content is not forwarded to the redirect/proxy; redirects fail as unexpected status

#### Scenario: Response body bound
- **WHEN** a response exceeds the configured byte bound regardless of absent, chunked or inaccurate Content-Length
- **THEN** reading stops and resources close before parsing or returning the over-limit result, with sanitized target_failed

#### Scenario: Exact body and output limits
- **WHEN** otherwise valid responses are exactly at the configured byte/Unicode-scalar limits or one unit beyond
- **THEN** exact limits are accepted and overflow is rejected without truncation; non-identity Content-Encoding is rejected without decompression

### Requirement: Validated text response and sanitized failures
Only HTTP 200 with valid UTF-8 JSON object, no error field, exact boolean completed status and Unicode-scalar response string SHALL produce a result. Duplicate keys/nonstandard constants MUST be rejected. Connection, timeout, status, protocol, decoding, limit and adapter exceptions SHALL map to existing target_failed/502 without raw exception, body or configuration disclosure.

#### Scenario: Malformed response
- **WHEN** response is invalid UTF-8/JSON, duplicate-key/nonstandard JSON, a nonobject, lacks response/completion, has non-string response, lone surrogate, nonboolean/false completion or an error field
- **THEN** dispatch returns only sanitized target_failed without a result or synthetic finding

#### Scenario: Unexpected status
- **WHEN** runtime returns a non-200 status including 3xx, 400, 404, 429 or 500 with prompt-bearing error text
- **THEN** caller receives fixed 502 target_failed without runtime status/body/message and no retry or fallback

#### Scenario: Connection failure and client exception
- **WHEN** a connection is refused/reset or a client exception embeds submitted content, generated text or connection details
- **THEN** caller errors and application audit/logs exclude those values and raw exception causes

#### Scenario: Empty response and extra metadata
- **WHEN** a completed valid response has empty text or additional runtime metadata
- **THEN** empty text is accepted and only response text is returned; metadata does not establish trusted audit state

### Requirement: Preserved audit and input security boundaries
Local-model dispatch SHALL preserve retained registration-derived audit identity and successful audit-before-invocation. Unknown requested strings MUST NOT become audit metadata. Failures after eligibility audit MUST remain target failures, not policy BLOCK or success records. Raw prompts/responses/secrets MUST NOT enter application audit or default operational logs.

#### Scenario: Audit ordering and binding
- **WHEN** an eligible local-model decision is audited and registry state later changes
- **THEN** the already retained adapter is invoked once and its registered local-ollama identity remains in audit without re-resolution

#### Scenario: Sensitive unresolved target
- **WHEN** internal selection contains an unknown sensitive string or URL
- **THEN** safe operational audit uses unresolved, no policy action/findings or supplied string, and no control/runtime calls

#### Scenario: Post-audit invocation failure
- **WHEN** runtime invocation fails after decision audit
- **THEN** the prior record remains forwarding eligibility evidence without claiming successful generation and the HTTP outcome is sanitized target failure

#### Scenario: Prompt and output privacy
- **WHEN** sensitive prompts or responses occur on success, redaction, block or runtime error paths
- **THEN** application audit/errors/default logs contain neither raw content nor snippets/hashes/spans or client exception text; successful returned text is not claimed safe

### Requirement: No output inspection or model governance claim
Documentation SHALL explicitly state that generated output is not security-inspected and local-model input approval does not certify output safety. One fixed operator model SHALL be a deployment restriction only; centralized allowed-model policy governance and resource budgets remain future capabilities; input semantic detection is separately defined by semantic-security-detection and does not inspect generated output. Security reporting SHALL be covered by the security-reporting capability and MUST NOT imply those governance or output-inspection capabilities.

#### Scenario: Generated unsafe text
- **WHEN** a valid bounded model response contains sensitive or unsafe text
- **THEN** it returns unchanged as uninspected text without output filtering or a claim of output security

#### Scenario: Local-only deployment
- **WHEN** an operator follows the supported runtime setup
- **THEN** it uses a preprovisioned local model with Ollama cloud disabled, no paid API or credentials, and documents the separately administered daemon as trusted

### Requirement: Deterministic integration and concurrent isolation
Required automated tests SHALL run without real Ollama/model using deterministic client doubles and a loopback fake server. Concurrent invocations MUST keep request/response state separate and preserve per-request audit ordering. A separately invoked optional smoke test SHALL use a preprovisioned local runtime and never install/download models or enter normal test discovery.

#### Scenario: Required suite without runtime
- **WHEN** the normal unit/integration suite runs without an installed model server
- **THEN** registration, successful and failed transport, enforcement, audit ordering/privacy, limits, exactly-once dispatch, echo and deterministic-control regressions execute deterministically

#### Scenario: Concurrent distinct prompts
- **WHEN** multiple model requests with distinct prompts/results run simultaneously
- **THEN** each response corresponds only to its approved prompt, each eligible request invokes once after its own audit, and no shared content state leaks across requests

#### Scenario: Optional real smoke
- **WHEN** an operator explicitly invokes the smoke test with installed Ollama and the documented preprovisioned model
- **THEN** it checks model text success, echo compatibility and blocked dispatch without exact-wording assertions or prompt/output logs; absent prerequisites return sanitized nonzero failure and omission is recorded NOT RUN separately from required verification
