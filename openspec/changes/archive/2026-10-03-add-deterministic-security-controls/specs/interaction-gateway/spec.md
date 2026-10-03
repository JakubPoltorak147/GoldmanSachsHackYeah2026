# Interaction Gateway Delta

## MODIFIED Requirements

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
