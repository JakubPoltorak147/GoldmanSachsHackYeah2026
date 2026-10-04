# Spec Delta

## ADDED Requirements

### Requirement: Opt-in server-owned scenario interaction variant
When local Demo is explicitly enabled, the interaction endpoint SHALL additionally accept an exclusive scenario_id-only request selecting a fixed server-owned catalog entry. It SHALL retain existing outcome/error envelopes and generate the UUID on the server. Ordinary target/content requests MUST remain compatible. Disabled, unknown, mixed or extra-field scenario requests MUST fail sanitized validation before evaluation.

#### Scenario: Scenario request
- **WHEN** enabled Demo receives a valid enabled scenario_id-only request from the same application origin
- **THEN** its server-owned content, local-ollama target and frozen profile enter the existing policy/audit/dispatch pipeline and return the existing status/envelope

#### Scenario: Override, unsupported origin or disabled mode
- **WHEN** a scenario request adds fields, selects unknown/disabled scenario, has wrong types, arrives with missing/foreign/null Origin or Demo is disabled
- **THEN** fixed 422 invalid_request reflects no submitted values and makes zero control/evaluator/target calls

#### Scenario: Original request compatibility
- **WHEN** ordinary explicit target/content requests produce ALLOW, REDACT, BLOCK, validation/evaluation/audit/target failures in either demo mode
- **THEN** existing validation semantics, target selection, UUIDs, status codes, result/null omission and sanitized error envelopes remain unchanged

### Requirement: Retained demo profile and shared required audit gate
Scenario execution SHALL retain immutable server-selected policy/control/target bindings for its entire pipeline and use the same durable reporting store and required audit semantics as ordinary interactions. Neither expected outcomes nor browser fields SHALL establish findings, action, identities or completion. Simulation failure injection MUST remain isolated to the selected scenario's transport.

#### Scenario: Shared gate failure
- **WHEN** required reporting/audit fails during one scenario profile
- **THEN** that eligible run has zero dispatch and later profiles cannot bypass the unhealthy shared gate; existing completion failures preserve obtained outcomes without retry

#### Scenario: Immutable attribution
- **WHEN** different scenario profiles complete or fail concurrently
- **THEN** audit/query identities and findings derive from each retained profile, actual producer and adapter result validation without cross-run content or configuration state

## MODIFIED Requirements

### Requirement: Validated text interaction
The gateway SHALL accept a text interaction for either explicit public target `local-echo` or `local-ollama`, assign its identifier on the server, and reject invalid ordinary text requests without forwarding them. The separately specified opt-in server-owned scenario variant is also permitted when Demo is enabled.

#### Scenario: Valid request
- **WHEN** a caller submits a valid nonempty text string of at most 16,384 characters for either explicit public target
- **THEN** the gateway assigns an interaction ID and evaluates that exact text without trimming or normalization

#### Scenario: Maximum content length
- **WHEN** a caller submits content of exactly 16,384 characters
- **THEN** the gateway accepts it for evaluation

#### Scenario: Over-limit content
- **WHEN** a caller submits content of 16,385 characters
- **THEN** the gateway returns a sanitized validation response and makes zero target calls

#### Scenario: Invalid request shape
- **WHEN** an ordinary target/content request has missing fields, unknown fields, a wrong type, or empty content
- **THEN** the gateway returns a sanitized validation response without reflecting submitted content and makes zero target calls

#### Scenario: Malformed JSON
- **WHEN** a caller submits malformed JSON containing sensitive text
- **THEN** the gateway returns a sanitized validation response without reflecting the body and makes zero target calls

#### Scenario: Invalid Unicode scalar
- **WHEN** a caller submits content containing a lone surrogate through a JSON escape
- **THEN** the gateway returns a sanitized validation response and makes zero target calls

#### Scenario: Untrusted destination or identity
- **WHEN** a caller supplies an unsupported target or a caller-asserted identity field
- **THEN** the gateway rejects the request and makes zero target calls

#### Scenario: Local model selection
- **WHEN** a caller submits valid content for `local-ollama`
- **THEN** the gateway accepts it under the same text and identity validation rules as `local-echo`

### Requirement: Preserved public foundation behavior
The public gateway SHALL accept the explicit public targets `local-echo` and `local-ollama`, preserving current ordinary target/content text, identity, response, and error behavior. The opt-in scenario_id-only variant is a separate intentional request-shape extension; it uses the same outcome/error envelopes. Internal registry expansion MUST NOT expose any other public destination. Existing email detection, local echo behavior and wire schemas SHALL remain supported, with the intentional public target selector expansion and separately specified opt-in scenario request extension. The historical text-result schema name SHALL remain compatible. Historical email-only policies and their digest SHALL remain supported with an explicitly supplied email-only registry; expanded default composition requires explicit policy migration and legitimately changes the default digest.

#### Scenario: Internal registration does not expose a target
- **WHEN** a target other than the two explicit public IDs is registered internally and a caller requests it through HTTP
- **THEN** HTTP rejects it with sanitized 422 before service evaluation, with no target call or service audit event

#### Scenario: Existing wire outcomes
- **WHEN** default production requests produce ALLOW, REDACT, BLOCK, invalid input, evaluation/audit failure, or target failure
- **THEN** they retain the existing response fields/null omission, reason/error codes, and respective 200, 200, 403, 422, 503, and 502 statuses

#### Scenario: Input and identity compatibility
- **WHEN** existing valid or invalid request cases exercise exact text, 16,384-character bounds, Unicode scalar validation, strict types, extra fields, malformed JSON, unsupported targets, or asserted identities
- **THEN** their acceptance/rejection and sanitized responses remain unchanged and accepted interactions retain server-generated IDs

#### Scenario: Email-only compatibility registry
- **WHEN** recorded foundation policies and wire fixtures run with an explicit unchanged email-only registration
- **THEN** original mappings, canonical digest, detector semantics and normalized HTTP outcomes remain unchanged

#### Scenario: Expanded pack compatibility
- **WHEN** email-only or ordinary local-echo content contains no additional supported pack patterns under the expanded default policy
- **THEN** existing email redaction and unchanged ordinary echo outcomes remain compatible, and ordinary request/response OpenAPI shapes and status envelopes remain unchanged; the documented scenario request alternative is the only additional request-shape extension

#### Scenario: Result schema compatibility
- **WHEN** either public target successfully returns text
- **THEN** result remains a content-only object using the existing compatible response schema, without model, usage or streaming fields

#### Scenario: Supported ID missing from injected registry
- **WHEN** a valid `local-ollama` request reaches an injected registry without that binding
- **THEN** resolution returns sanitized 503 evaluation_failed with safe unresolved operational audit and zero control evaluations or target calls
