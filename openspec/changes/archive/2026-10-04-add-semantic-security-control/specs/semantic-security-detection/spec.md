# Spec Delta

## Purpose

Provide one bounded local semantic input classifier for instruction attacks and related exfiltration intent, producing trusted findings for central policy without granting model output enforcement authority.

## ADDED Requirements

### Requirement: Focused registered semantic input detection
The system SHALL register input control `semantic-security` with only `semantic.prompt_injection`, `semantic.instruction_override` and `semantic.exfiltration_intent`. Findings SHALL be spanless, at most one per code in that order, and support ALLOW/BLOCK only. Detection MUST NOT perform enforcement, output inspection, tool execution, RAG or memory access.

#### Scenario: Normal benign request
- **WHEN** a deterministic fake evaluator returns all three valid scores below threshold for ordinary content
- **THEN** the control returns no findings and central policy, rather than the model, determines the final action

#### Scenario: Clear prompt injection
- **WHEN** a fake evaluator returns prompt_injection at or above threshold for an explicit embedded instruction attack
- **THEN** the registered control emits semantic.prompt_injection with no span, content, score or action

#### Scenario: Indirect instruction override
- **WHEN** content using indirect role/priority override wording has no deterministic attack signature but a fake evaluator supplies instruction_override above threshold
- **THEN** the semantic control emits semantic.instruction_override and the configured central mapping determines enforcement

#### Scenario: Related exfiltration intent
- **WHEN** a fake evaluator assigns exfiltration_intent above threshold to a request to disclose protected instructions or send confidential data elsewhere
- **THEN** the control emits semantic.exfiltration_intent without extracting secrets or performing destination authorization

#### Scenario: Legitimate security discussion
- **WHEN** a fake evaluator assigns below-threshold scores to quoted attack wording used for defensive analysis
- **THEN** no semantic finding is produced, without claiming that fake-runtime tests establish real-model accuracy

### Requirement: Closed classifier response
The classifier result SHALL be exactly one JSON object with mandatory numeric fields prompt_injection, instruction_override and exfiltration_intent. Values MUST be finite exact numbers in [0,1], excluding booleans and coercion. Unknown/missing/duplicate fields, invalid Unicode/JSON or surrounding prose MUST fail evaluation. Model-returned identifiers, actions, policy instructions and explanations MUST NOT enter trusted state.

#### Scenario: Forged finding or producer
- **WHEN** a result adds a finding_id, code, control_id or unknown category, including syntactically valid registered-looking identifiers
- **THEN** the entire response is rejected without exposing the supplied identifier or producing any finding

#### Scenario: Enforcement injection
- **WHEN** a result includes action ALLOW/BLOCK, a policy override or rationale text in addition to otherwise valid scores
- **THEN** evaluation fails closed and none of those fields affects central policy

#### Scenario: Malformed or ambiguous output
- **WHEN** output has fences, trailing prose, multiple objects, missing/duplicate fields, a JSON array, numeric strings/booleans, NaN/Infinity, out-of-range values or lone surrogates
- **THEN** it is rejected without repair, coercion, substring extraction or model retry

### Requirement: Documented score and threshold semantics
Scores SHALL represent independent estimated category risk, not calibrated probability or enforcement confidence. For each category, score >= the frozen configured threshold SHALL produce its fixed finding; lower scores SHALL not. A valid ambiguous score SHALL use the same rule with no argmax or implicit benign label. Model scores MUST NOT modify the threshold or mappings.

#### Scenario: Inclusive boundary
- **WHEN** threshold is 0.75 and category scores are separately 0.749, 0.75 and 0.751
- **THEN** the first yields no finding and the latter two yield that category's registered finding

#### Scenario: Overlapping categories
- **WHEN** multiple category scores reach threshold
- **THEN** each produces exactly one fixed finding in registered category order, independently of the sum of scores

### Requirement: Trusted local evaluator lifecycle
Evaluator settings and model identity SHALL be administrator-owned, validated and frozen at startup independently of target selection. The evaluator SHALL use only a literal loopback HTTP origin and one preprovisioned local model with cloud disabled. Startup MUST NOT probe, download or require a running daemon. Evaluation SHALL use isolated request-local state and close owned clients on every path, without retries, fallback, history or cloud dependencies.

#### Scenario: Defaults and overrides
- **WHEN** settings are absent
- **THEN** evaluator defaults are loopback port 11434, qwen2.5:3b, connect 2 seconds, read inactivity 30 seconds, input 16384 scalars/65536 bytes, HTTP response 8192 bytes and classifier text 1024 scalars

#### Scenario: Invalid trusted configuration
- **WHEN** settings violate the supported local origin/model grammar, finite timeout bounds or exact integer size bounds, including wrong types, numeric booleans or coercion
- **THEN** startup fails with fixed invalid_semantic_configuration, reflecting no supplied configuration or raw cause

#### Scenario: Supported bounded overrides
- **WHEN** an administrator supplies literal 127.0.0.1 or ::1 HTTP origin with explicit port 1–65535 and optional trailing slash only; a 1–128-character model matching `[a-z0-9][a-z0-9._-]*:[a-z0-9][a-z0-9._-]*` with no cloud in the tag; finite connect 0.1–10/read inactivity 0.1–60 seconds; exact integer input scalars 1–16384/input UTF-8 bytes 1–65536/response bytes 1024–65536/inner output scalars 128–4096
- **THEN** startup freezes those validated settings without allowing credentials, hostnames, extra URL path/query/fragment, runtime probes or caller overrides

#### Scenario: No runtime at startup
- **WHEN** settings/policy are valid and Ollama or the model is absent
- **THEN** startup succeeds without network activity; disabled semantic makes no calls and enabled evaluation fails operationally without disabling deterministic controls

#### Scenario: Model identity forgery
- **WHEN** request fields or runtime envelope metadata assert a different evaluator model
- **THEN** they cannot change the frozen evaluator selection or trusted reporting identity

#### Scenario: Concurrent requests
- **WHEN** simultaneous evaluations carry distinct sensitive content and fake scores
- **THEN** findings, timing and responses remain attributable to their own interaction without shared prompt/result buffers

### Requirement: Bounded non-streaming evaluator transport
One evaluation SHALL issue at most one non-streaming classifier request, without tools or history, using fixed classifier instructions and structured format. Input SHALL be checked in full for scalar/UTF-8 bounds before transport. Connect/write/pool and read inactivity SHALL be bounded; proxies, redirects and retries MUST be disabled. Whole response bytes and inner classifier text MUST be bounded before acceptance, rejecting rather than truncating overflow.

#### Scenario: Fixed classification request
- **WHEN** a valid input reaches the evaluator
- **THEN** one request uses the frozen model, stream false, the closed score schema, fixed temperature 0 and output token cap 256, with submitted text treated as untrusted data and no policy action/identifier instructions

#### Scenario: Input boundary
- **WHEN** content is exactly at the configured scalar/UTF-8 bounds or one unit beyond either
- **THEN** exact limits permit evaluation and excess fails before any runtime call, including internal requests that bypass HTTP

#### Scenario: Timeout or runtime failure
- **WHEN** connection/read inactivity exceeds its bound, connection fails, the model is absent or HTTP status is non-200
- **THEN** evaluation closes resources and fails with no retry, alternate model or target invocation

#### Scenario: Oversized response
- **WHEN** declared or actual body bytes exceed the cap, or inner classifier text exceeds its scalar cap
- **THEN** evaluation rejects the response without truncation, independent of missing, inaccurate or chunked length metadata

#### Scenario: Runtime envelope validation
- **WHEN** a response has non-identity encoding, invalid UTF-8/JSON, duplicate keys/nonstandard constants, error field, nonboolean/false completion or non-scalar-string classifier text
- **THEN** it fails before score conversion; optional runtime metadata never becomes trusted findings or reporting identity

#### Scenario: Active slow response
- **WHEN** data arrives within each read timeout but total evaluation takes longer
- **THEN** byte bounds still apply and documentation describes read inactivity, without promising a wall-clock deadline or daemon cancellation

### Requirement: Fail-closed hybrid evaluation
All enabled deterministic controls SHALL run independently on original content before enabled semantic evaluation. Only validated semantic findings SHALL join deterministic findings for central resolution. Semantic input/transport/schema/runtime failure MUST return existing evaluation_failed/503 with no security action/findings and zero target calls. It MUST NOT become benign, synthetic BLOCK, a retry or automatic control disabling.

#### Scenario: Deterministic redaction plus semantic block
- **WHEN** real deterministic email findings map to REDACT and fake semantic override findings map to BLOCK
- **THEN** both see original content and central policy selects BLOCK with both trusted resolutions and zero target calls

#### Scenario: Semantic ALLOW cannot weaken deterministic BLOCK
- **WHEN** a real credential finding maps to BLOCK while semantic findings map to ALLOW
- **THEN** deterministic and semantic evaluation both occur and central policy still BLOCKs

#### Scenario: Failure after deterministic evaluation
- **WHEN** deterministic controls completed but enabled semantic evaluation fails, including with a previously collected deterministic BLOCK finding
- **THEN** no target is invoked, operational reporting includes no partial security findings or policy action, and deterministic control behavior/configuration remains unchanged

#### Scenario: Same classifier result under different mappings
- **WHEN** identical semantic scores produce the same findings under ALLOW and BLOCK policies
- **THEN** only central mapping changes final enforcement; semantic REDACT mappings are rejected at startup

### Requirement: Deterministic security verification and privacy
Required unit/integration tests SHALL use injected fake evaluators/clients and a local fake HTTP runtime without installed Ollama. They SHALL cover benign, attack, threshold, malformed/forged/action-injection, timeout, limits and hybrid policy paths. Application audit/reporting/errors/logs MUST exclude raw input, evaluator output, scores, snippets, spans, hashes and raw exceptions. Real-runtime smoke SHALL be separate and optional.

#### Scenario: Sensitive canaries
- **WHEN** input, inner response, runtime error/envelope or client exceptions carry distinct sensitive canaries on success and failure paths
- **THEN** audit JSON, database/query/summary output, default application logs and sanitized HTTP errors contain none of them, with correct fixed codes, registered findings and invocation counts

#### Scenario: Runtime-free suite
- **WHEN** normal tests run without Ollama
- **THEN** all acceptance scenarios and existing deterministic/audit/target regressions execute without commercial or live-model dependency

#### Scenario: Optional smoke
- **WHEN** an operator separately invokes real smoke using a preprovisioned local model
- **THEN** no model is installed/downloaded and omission is recorded NOT RUN without preventing required test PASS
