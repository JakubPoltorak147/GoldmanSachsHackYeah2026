# Spec Delta

## Purpose

Provide a curated interactive challenge console that exercises actual policy-governed local generation and semantic security while explaining observed content-free evidence.

## ADDED Requirements

### Requirement: Server-owned synthetic catalog
An explicitly enabled Demo view SHALL expose a fixed server-owned scenario catalog with safe titles/descriptions, expected outcomes, prerequisites and simulation labels. Content, target and execution profile MUST be resolved on the server. Catalog/reporting APIs MUST NOT return prompts, transformed content, generated output, semantic raw responses/scores or configuration endpoints.

#### Scenario: Disabled or unavailable semantic demo mode
- **WHEN** Demo is disabled or the startup semantic demo option is disabled
- **THEN** disabled Demo cannot execute scenarios; enabled Demo shows semantic cards as disabled with safe prerequisite instructions, without enabling controls dynamically

#### Scenario: Synthetic payloads
- **WHEN** credential, email and private-key scenarios are inspected by automated tests
- **THEN** fixed values are synthetic detector fixtures, no usable private key or real credential is present, and attack signature text is never executed

### Requirement: Real governed scenario execution
Every scenario SHALL enter the existing interaction boundary and control pipeline with a server-generated UUID. Deterministic controls, enabled semantic evaluation, validated findings, central policy, redaction and required audit/reporting MUST precede any eligible target invocation. Browser clients MUST NOT call Ollama or set profile, runtime, policy, model, target or content for a scenario.

#### Scenario: Forged scenario override
- **WHEN** a request mixes scenario ID with target/content or supplies unknown ID, policy, model, endpoint or fault fields
- **THEN** it is rejected before evaluation with sanitized validation failure and zero evaluator/target calls

#### Scenario: Profile and interaction isolation
- **WHEN** concurrent scenarios use different startup-bound profiles
- **THEN** each retains its own policy/model/control bindings and UUID, shares required reporting health and cannot alter another run or ordinary interaction service

### Requirement: Deterministic live demonstrations
The catalog SHALL include benign ALLOW, email/PII REDACT, supported credential/API-secret BLOCK, private-key BLOCK and known historical signature BLOCK scenarios. Eligible live runs MUST use the real existing local-ollama target; BLOCK MUST invoke zero generation calls. Automated tests SHALL verify exact centrally redacted target input without real Ollama.

#### Scenario: Benign real response
- **WHEN** the benign scenario runs with a provisioned available local target
- **THEN** actual policy ALLOW precedes one audited generation call and the existing interaction result delivers actual generated text

#### Scenario: Redacted-only forwarding
- **WHEN** the synthetic email scenario runs under the deterministic demo policy
- **THEN** pii.email maps to REDACT and only centrally transformed input reaches the target once, with no raw/transformed text in reporting

#### Scenario: Three deterministic attack families
- **WHEN** supported synthetic credential, complete private-key envelope and historical signature scenarios run
- **THEN** their existing registered findings centrally map to BLOCK and each has zero target calls

### Requirement: Real semantic and hybrid demonstrations
Enabled semantic demo runs SHALL use the existing real local evaluator and existing threshold/mappings. The catalog SHALL include prompt injection, indirect instruction override, exfiltration intent and combined deterministic/semantic scenarios. Expected outcomes MUST be distinguished from actual results; only validated observations SHALL determine displayed findings and decisions.

#### Scenario: Three semantic categories
- **WHEN** deterministic evaluator doubles return above-threshold scores for each corresponding attack scenario
- **THEN** registered semantic.prompt_injection, semantic.instruction_override and semantic.exfiltration_intent respectively lead to central BLOCK, safe semantic observations and zero generation calls

#### Scenario: Actual model disagrees with expectation
- **WHEN** live semantic classification produces different valid findings or no finding
- **THEN** the console shows actual policy outcome and the mismatch without inventing findings, overriding enforcement or silently changing thresholds

#### Scenario: Hybrid precedence
- **WHEN** deterministic email maps to REDACT and semantic override maps to BLOCK
- **THEN** both evaluate original content, both findings are shown, central BLOCK wins and no generation occurs

### Requirement: Labelled unavailable scenarios
The catalog SHALL include evaluator-unavailable and generation-unavailable runs using server-owned isolated transport failure injection through existing adapters, labelled controlled simulations. They MUST traverse normal failure/audit handling without fabricated decisions or evidence. Manual live instructions SHALL also cover genuine runtime unavailability.

#### Scenario: Evaluator unavailable fail closed
- **WHEN** enabled semantic transport fails after deterministic evaluation
- **THEN** actual 503 evaluation_failed has no policy action/findings, available reporting records failed semantic status and prior completed controls, and generation is not_invoked

#### Scenario: Generation unavailable after audit
- **WHEN** eligible benign evaluation is audited and generation transport fails
- **THEN** actual 502 target_failed retains audited ALLOW in reporting, failed invocation completion when persistence succeeds and no model fallback or retry

### Requirement: Observed pipeline and reporting correlation
The Demo SHALL show input, deterministic controls, semantic attempt, findings, central decision, required audit/reporting, target status and final outcome correlated by UUID. Recorded timings/identities MUST retain reporting meanings. Pending stages MUST NOT masquerade as completed telemetry; missing evidence and partial findings MUST NOT be invented.

#### Scenario: Missing reporting evidence
- **WHEN** outcome includes UUID but detail lookup fails or has no durable record
- **THEN** interaction outcome remains visible and audit/recorded stages are labelled unavailable, with no POST retry, invented audit success or invocation claim

#### Scenario: No policy decision after evaluation failure
- **WHEN** semantic evaluation fails
- **THEN** policy is shown as not reached, partial findings as not recorded, and target as NOT INVOKED rather than a fabricated BLOCK

#### Scenario: Completion ambiguity
- **WHEN** a durable eligible decision has unknown completion but the immediate interaction response was received
- **THEN** immediate outcome and historical unknown evidence are shown separately and generation is not retried

### Requirement: Transient result and deterministic verification
Successful generated text SHALL be delivered only via the existing interaction result and displayed transiently as uninspected plain text. It MUST NOT enter reporting/catalog APIs, historical detail, logs or browser storage. Required automated tests SHALL use deterministic doubles without Ollama; real evaluator/generation SHALL be exercised separately for live rehearsal.

#### Scenario: HTML-like output and privacy
- **WHEN** an allowed interaction returns sensitive or HTML-like generated text
- **THEN** only its current transient result panel receives the uninspected text, no HTML executes and catalog/reporting/history/logs/storage exclude it

#### Scenario: Runtime-free test suite
- **WHEN** required tests run with Ollama absent
- **THEN** all catalog, policy, redaction, audit-order, zero-call, semantic-category and sanitized failure assertions run deterministically

### Requirement: Predictable single-run controls
The Demo SHALL allow one active run per panel, show waiting and actual measured completion states, refresh matching reporting after completion and never automatically retry execution. A disconnected request MUST be labelled outcome unknown rather than assumed failed or safely cancelled.

#### Scenario: Double click or network interruption
- **WHEN** an operator double-clicks Run or connectivity is lost after submission
- **THEN** the panel issues one POST, avoids retry and explains unknown outcome without claiming daemon cancellation
