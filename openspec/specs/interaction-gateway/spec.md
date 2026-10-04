# interaction-gateway Specification

## Purpose
The interaction gateway accepts bounded text requests and exposes policy decisions while forwarding only content that the control layer has approved for the selected local target.

## Requirements

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

### Requirement: Sanitized HTTP outcomes
The gateway MUST distinguish policy decisions from internal and target failures in its HTTP responses and MUST NOT expose submitted content or internal exception text in error responses.

#### Scenario: Internal evaluation failure
- **WHEN** evaluation fails because a control raises an exception, a finding span is invalid, or policy resolution is inconsistent
- **THEN** the gateway returns a sanitized `503` service response without a security Finding or policy `BLOCK` decision and makes zero target calls

#### Scenario: Target failure after eligible decision
- **WHEN** the local target fails after an `ALLOW` or `REDACT` decision has been audited
- **THEN** the gateway returns a sanitized target-failure response without exposing exception text

### Requirement: Immutable target registration and exact resolution
Internal target registrations SHALL bind bounded server-owned symbolic IDs to adapters in an immutable catalogue. Duplicate or invalid identities MUST be rejected before serving. Resolution SHALL use exact registered IDs without fallback, alias expansion, URL interpretation, discovery, network activity, or adapter invocation. The reserved operational ID `unresolved` MUST NOT identify a registered target.

#### Scenario: Two internal targets
- **WHEN** two distinct local test adapters are registered
- **THEN** resolving either symbolic ID returns only its registered binding without invoking either adapter

#### Scenario: Invalid target registration
- **WHEN** target metadata contains duplicate IDs, invalid types/characters, overlong IDs, or the reserved `unresolved` ID
- **THEN** registration is rejected before interactions are accepted

#### Scenario: Unknown internal target
- **WHEN** the internal service receives a target ID absent from its registry
- **THEN** evaluation fails closed as a sanitized operational failure with zero control evaluations, zero target calls, and no fallback

#### Scenario: Immutable target binding
- **WHEN** caller-owned registration-input collections are changed after construction
- **THEN** the target registry retains its original identities and adapter bindings

### Requirement: Retained target binding through audited dispatch
The service SHALL resolve and retain one target binding before evaluation and SHALL use that same binding for decision audit identity and eligible invocation. It MUST NOT resolve again after audit. ALLOW/REDACT SHALL invoke that adapter exactly once only after successful audit; BLOCK and evaluation/audit failures SHALL invoke no adapter.

#### Scenario: Correct target routing
- **WHEN** interactions for two registered internal targets receive eligible decisions
- **THEN** each reaches only its retained adapter after an audit event naming that adapter's registered target ID

#### Scenario: Original and redacted content
- **WHEN** central policy selects ALLOW or REDACT
- **THEN** the retained adapter receives respectively unchanged original content or only centrally redacted content, preserving interaction identity and target

#### Scenario: Closed dispatch paths
- **WHEN** policy selects BLOCK, evaluation fails, or audit emission fails
- **THEN** neither the resolved adapter nor any other registered adapter is invoked

#### Scenario: Target failure
- **WHEN** the retained adapter fails or returns an invalid result after audit
- **THEN** the service reports a sanitized target failure and retains the earlier decision record without claiming target success

### Requirement: Explicit composition and uniform dependency injection
Default assembly SHALL explicitly register email-address, bearer-credential, pem-private-key, github-token, us-ssn, known-attack-signatures and semantic-security with the local echo and local Ollama targets, validate the trusted startup signature catalog, bind policy at startup, and supply the audit sink. Core policy and orchestration MUST NOT select concrete implementations implicitly. Injected test registries SHALL pass through the same metadata validation and policy-binding path as production without permissive validation modes.

#### Scenario: Default startup
- **WHEN** the default application starts
- **THEN** it binds all seven production control registrations, the frozen validated signature catalog and both `local-echo` and `local-ollama` targets with the selected complete validated startup policy

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
- **WHEN** default target/evaluator settings and policy are valid but no model server is running
- **THEN** startup registers both targets and the semantic control without network activity; local echo remains usable with semantic disabled, while enabled semantic evaluation fails closed if unavailable

#### Scenario: Explicit registry injection
- **WHEN** a test supplies a valid target registry
- **THEN** startup uses it without loading default target-generation runtime settings or contacting a runtime; semantic settings remain independently bound only when the control composition requires them, retaining normal policy and metadata validation

#### Scenario: Baseline and enabled demo policies
- **WHEN** an operator selects the shipped baseline or complete semantic demo policy
- **THEN** baseline explicitly disables semantic-security while preserving all deterministic settings; the demo enables it with threshold 0.75 and all three codes mapped to BLOCK, without changing public schemas or deterministic mappings

#### Scenario: Semantic evaluation failure at HTTP
- **WHEN** an enabled evaluator times out or returns invalid classifier data
- **THEN** the gateway returns fixed 503 evaluation_failed with no policy action or finding list and zero target calls, retaining existing response/error schemas

### Requirement: Generic validated finding-code responses
Decision responses SHALL represent finding codes as strings from validated registered findings, preserving existing list order and multiplicity. The response schema MUST NOT restrict codes to the email-only enum. Unknown or forged codes MUST fail evaluation before response construction and MUST NOT be exposed as security findings.

#### Scenario: Additional registered finding code
- **WHEN** an injected registered control returns a valid non-email finding on a local-echo request
- **THEN** the response includes that code in the existing finding_codes list with the centrally selected action and existing result shape

#### Scenario: Repeated codes
- **WHEN** validated findings contain repeated codes
- **THEN** the response preserves their evaluation order and multiplicity without deduplicating or aggregating them

#### Scenario: OpenAPI schema
- **WHEN** a client inspects the decision response schema
- **THEN** finding_codes remains an array of strings without a `pii.email`-only item enum

#### Scenario: Invalid output cannot reach response
- **WHEN** an evaluator returns an undeclared code or forged identity
- **THEN** the HTTP response is sanitized 503 with no policy action or finding-code list and no target invocation

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

### Requirement: Trusted optional target model metadata
Immutable target metadata SHALL accept an optional non-sensitive administrator-owned model ID, bounded to 128 characters matching `[a-z0-9][a-z0-9._:-]{0,127}` without coercion. Model identity MUST derive only from the retained startup binding, not requests, adapter responses or arbitrary adapter attributes. Default local-model registration SHALL share the same frozen configured model as its adapter; echo SHALL have no model ID.

#### Scenario: Valid model metadata
- **WHEN** default composition configures local-ollama with a valid fixed model
- **THEN** its reporting model metadata matches that adapter's startup setting, without network probes or changes to policy digest or public request schema

#### Scenario: Invalid or forged metadata
- **WHEN** registration has an empty, wrong-type, overlong or malformed model ID, or request/response metadata asserts another model
- **THEN** invalid registration fails startup and untrusted assertions never establish reporting identity

#### Scenario: Target without model
- **WHEN** an injected adapter or echo target has no model metadata
- **THEN** its reporting model ID is null without introspection or discovery

### Requirement: Reporting lifecycle at the gateway
Default startup SHALL initialize required durable reporting storage and close owned resources at shutdown. Injected stores and sinks MUST retain the same validation and audit gate. Unavailable or unsupported storage SHALL fail startup with sanitized codes without exposing paths. Existing interaction response fields, statuses, input validation and public target selection SHALL remain unchanged.

#### Scenario: Unwritable storage
- **WHEN** the configured reporting location cannot be initialized
- **THEN** startup fails safely without accepting interactions or silently disabling required persistence

#### Scenario: HTTP compatibility
- **WHEN** requests produce ALLOW, REDACT, BLOCK, invalid input, evaluation/audit failure or target failure
- **THEN** response schemas and respective 200, 200, 403, 422, 503 and 502 statuses remain intact, and invalid HTTP requests produce no service reporting events
