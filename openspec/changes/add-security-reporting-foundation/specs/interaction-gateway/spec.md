# Interaction Gateway Delta

## ADDED Requirements

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
Default startup SHALL initialize required durable reporting storage and close owned resources at shutdown. Injected stores and sinks MUST retain the same validation and audit gate. Unavailable/unsafe storage SHALL fail startup with sanitized codes without exposing paths. Existing interaction response fields, statuses, input validation and public target selection SHALL remain unchanged.

#### Scenario: Unwritable storage
- **WHEN** the configured reporting location cannot be initialized
- **THEN** startup fails safely without accepting interactions or silently disabling required persistence

#### Scenario: HTTP compatibility
- **WHEN** requests produce ALLOW, REDACT, BLOCK, invalid input, evaluation/audit failure or target failure
- **THEN** response schemas and respective 200, 200, 403, 422, 503 and 502 statuses remain intact, and invalid HTTP requests produce no service reporting events
