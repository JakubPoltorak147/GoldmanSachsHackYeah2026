# Spec Delta

## MODIFIED Requirements

### Requirement: Validated text interaction
The gateway SHALL accept a text interaction for either explicit public target `local-echo` or `local-ollama`, assign its identifier on the server, and reject invalid requests without forwarding them.

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
- **WHEN** a caller submits missing fields, unknown fields, a wrong type, or empty content
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


### Requirement: Decision-governed forwarding
The gateway SHALL forward only interactions with an `ALLOW` or `REDACT` decision and SHALL make no target call for a `BLOCK` decision.

#### Scenario: Allowed interaction
- **WHEN** policy decides `ALLOW` for a valid interaction
- **THEN** the selected registered target receives the original text unchanged exactly once and the caller receives its text result with the `ALLOW` decision

#### Scenario: Redacted interaction
- **WHEN** policy decides `REDACT` for a valid interaction
- **THEN** the selected registered target receives only the centrally transformed text exactly once and the caller receives its text result with the `REDACT` decision

#### Scenario: Blocked interaction
- **WHEN** policy decides `BLOCK` for a valid interaction
- **THEN** the gateway returns an explainable `BLOCK` response and makes zero target calls

### Requirement: Explicit composition and uniform dependency injection
Default assembly SHALL explicitly register email-address, bearer-credential, pem-private-key, github-token, us-ssn and known-attack-signatures with the local echo and local Ollama targets, validate the trusted startup signature catalog, bind policy at startup, and supply the audit sink. Core policy and orchestration MUST NOT select concrete implementations implicitly. Injected test registries SHALL pass through the same metadata validation and policy-binding path as production without permissive validation modes.

#### Scenario: Default startup
- **WHEN** the default application starts
- **THEN** it binds all six production control registrations, the frozen validated signature catalog and both `local-echo` and `local-ollama` targets with the selected complete validated startup policy

#### Scenario: Generic test startup
- **WHEN** tests inject two controls with valid definitions, corresponding complete policy entries, a local-echo spy binding, and an audit sink
- **THEN** startup and requests exercise the same registry validation, finding validation, central policy, and audited dispatch contracts as production

#### Scenario: Invalid injected composition
- **WHEN** injected registrations or their selected policy are invalid or incomplete
- **THEN** startup fails closed rather than falling back to production defaults or bypassing validation

#### Scenario: Expanded policy migration
- **WHEN** an administrator selects a historical email-only policy with the expanded default registry
- **THEN** startup fails for missing explicit new control entries; explicit disabled entries permit migration without implicit defaults

#### Scenario: Runtime-independent startup
- **WHEN** default target settings and policy are valid but no model server is running
- **THEN** startup registers both targets without network activity and local echo remains usable

#### Scenario: Explicit registry injection
- **WHEN** a test supplies a valid target registry
- **THEN** startup uses it without loading default runtime settings or contacting a runtime, retaining normal policy and metadata validation


### Requirement: Preserved public foundation behavior
The public gateway SHALL accept the explicit public targets `local-echo` and `local-ollama`, preserving current text, identity, response, and error behavior. Internal registry expansion MUST NOT expose any other public destination. Existing email detection, local echo behavior and wire schemas SHALL remain supported, with only the intentional public target selector expansion. The historical text-result schema name SHALL remain compatible. Historical email-only policies and their digest SHALL remain supported with an explicitly supplied email-only registry; expanded default composition requires explicit policy migration and legitimately changes the default digest.

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
- **THEN** existing email redaction and unchanged ordinary echo outcomes remain compatible, and full OpenAPI schemas/status envelopes remain unchanged except the public target selector enum

#### Scenario: Result schema compatibility
- **WHEN** either public target successfully returns text
- **THEN** result remains a content-only object using the existing compatible response schema, without model, usage or streaming fields

#### Scenario: Supported ID missing from injected registry
- **WHEN** a valid `local-ollama` request reaches an injected registry without that binding
- **THEN** resolution returns sanitized 503 evaluation_failed with safe unresolved operational audit and zero control evaluations or target calls
