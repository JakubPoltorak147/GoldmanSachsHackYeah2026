# interaction-gateway Specification

## Purpose
The interaction gateway accepts bounded text requests and exposes policy decisions while forwarding only content that the control layer has approved for the selected local target.

## Requirements

### Requirement: Validated text interaction
The gateway SHALL accept a text interaction for the fixed local echo target, assign its identifier on the server, and reject invalid requests without forwarding them.

#### Scenario: Valid request
- **WHEN** a caller submits a valid nonempty text string of at most 16,384 characters for the local echo target
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

### Requirement: Decision-governed forwarding
The gateway SHALL forward only interactions with an `ALLOW` or `REDACT` decision and SHALL make no target call for a `BLOCK` decision.

#### Scenario: Allowed interaction
- **WHEN** policy decides `ALLOW` for a valid interaction
- **THEN** the local echo target receives the original text unchanged exactly once and the caller receives its echo result with the `ALLOW` decision

#### Scenario: Redacted interaction
- **WHEN** policy decides `REDACT` for a valid interaction
- **THEN** the local echo target receives only the centrally transformed text exactly once and the caller receives its echo result with the `REDACT` decision

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
Default assembly SHALL explicitly register email-address, bearer-credential, pem-private-key, github-token, us-ssn and known-attack-signatures with the local echo target, validate the trusted startup signature catalog, bind policy at startup, and supply the audit sink. Core policy and orchestration MUST NOT select concrete implementations implicitly. Injected test registries SHALL pass through the same metadata validation and policy-binding path as production without permissive validation modes.

#### Scenario: Default startup
- **WHEN** the default application starts
- **THEN** it binds all six production control registrations, the frozen validated signature catalog and local echo target with the selected complete validated startup policy

#### Scenario: Generic test startup
- **WHEN** tests inject two controls with valid definitions, corresponding complete policy entries, a local-echo spy binding, and an audit sink
- **THEN** startup and requests exercise the same registry validation, finding validation, central policy, and audited dispatch contracts as production

#### Scenario: Invalid injected composition
- **WHEN** injected registrations or their selected policy are invalid or incomplete
- **THEN** startup fails closed rather than falling back to production defaults or bypassing validation

#### Scenario: Expanded policy migration
- **WHEN** an administrator selects a historical email-only policy with the expanded default registry
- **THEN** startup fails for missing explicit new control entries; explicit disabled entries permit migration without implicit defaults

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
The public gateway SHALL continue accepting only the fixed local-echo request contract and preserving current text, identity, response, and error behavior. Internal registry expansion MUST NOT expose another public destination. Existing email detection, local echo behavior and wire schemas SHALL remain supported. Historical email-only policies and their digest SHALL remain supported with an explicitly supplied email-only registry; expanded default composition requires explicit policy migration and legitimately changes the default digest.

#### Scenario: Internal registration does not expose a target
- **WHEN** an additional target is registered internally and a caller requests it through HTTP
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
- **THEN** existing email redaction and unchanged ordinary echo outcomes remain compatible, and full OpenAPI schemas/status envelopes remain unchanged
