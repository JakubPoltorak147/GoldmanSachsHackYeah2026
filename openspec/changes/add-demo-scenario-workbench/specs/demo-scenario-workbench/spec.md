# Spec Delta

## Purpose

Provide an operator workspace for predefined scenarios and spontaneous text interactions that exercises actual policy-governed local targets while explaining observed content-free evidence.

## ADDED Requirements

### Requirement: Readable shared operator console
The dashboard SHALL use a light neutral operator interface with compact navigation, readable tables and labelled status colors. Interactions SHALL contain a scenario list, custom composer and result area; overview SHALL preserve its read-only metrics, filters, polling and safe event detail. The overview MUST remain usable with Demo disabled or no model runtime.

#### Scenario: Desktop and narrow keyboard use
- **WHEN** an operator uses the dashboard at 1440px or 390px viewport width by keyboard
- **THEN** navigation, scenario selection, labelled textarea/target controls, Run buttons, filters and event detail remain usable with visible focus, readable contrast and no body-level horizontal overflow; interaction sections stack on narrow screens

#### Scenario: Disabled Demo
- **WHEN** Demo is disabled
- **THEN** the restyled read-only overview remains available, with no Interactions execution surface or target calls

### Requirement: Single custom text interaction
Enabled Interactions SHALL provide a multiline composer, Unicode scalar count and registered public target selector. Custom execution MUST use the existing target_id/content request and the actual application policy, not a scenario profile. No request SHALL select a model, policy, endpoint, fault or semantic toggle. Input MUST retain exact textarea text without trimming or truncation.

#### Scenario: Echo and local model selection
- **WHEN** the operator submits valid custom text to Local echo or Local model
- **THEN** one ordinary interaction runs through central evaluation, redaction, required audit and eligible dispatch; the result names the selected target and returned UUID

#### Scenario: Scalar bounds and whitespace
- **WHEN** custom text is nonempty whitespace, includes non-BMP characters, or reaches the 16,384 Unicode scalar limit
- **THEN** client validation follows the server scalar contract, preserves exact submitted text and accepts within-bound scalar strings; empty, over-limit and lone-surrogate input cannot be submitted

#### Scenario: Target unavailable
- **WHEN** the selected configured target fails at execution
- **THEN** the workspace displays the sanitized actual failure and available audited decision without switching targets or retrying

### Requirement: Truthful custom configuration
The workspace SHALL display startup-bound application policy identity, enabled/disabled control IDs and registered public target/model identities from safe metadata. It MUST distinguish this configuration from a selected scenario's profile and from runtime availability. Failed metadata reads MUST disable submission and show unavailable rather than invented control states.

#### Scenario: Semantic baseline and echo
- **WHEN** the application baseline disables semantic inspection while semantic scenarios are enabled
- **THEN** custom input still reports semantic disabled and uses the baseline service; Local echo needs no model runtime under that policy

#### Scenario: Enabled application semantics
- **WHEN** the application's startup policy enables semantic inspection and its evaluator is unavailable
- **THEN** custom execution, including Local echo, fails closed as an operational failure without fabricating BLOCK or disabling the control

#### Scenario: Metadata read failure
- **WHEN** workspace metadata cannot be read
- **THEN** Run is disabled and configured controls/targets are unavailable; history is not used to infer current configuration

### Requirement: Understandable custom interaction guidance
The composer SHALL explain Local echo, Local model, ALLOW, REDACT and BLOCK in plain language. It MUST state that target selection and semantic scenario enablement do not change the custom application's checks. Current semantic enablement SHALL derive only from workspace metadata, and ALLOW MUST NOT be described as a guarantee of safety.

#### Scenario: First custom interaction
- **WHEN** the operator opens a configured workspace before submitting text
- **THEN** visible guidance explains that echo returns approved text, the model generates from approved text, redaction occurs before forwarding, BLOCK prevents invocation, and the displayed application policy governs either target

#### Scenario: Separate semantic configuration
- **WHEN** semantic scenarios are enabled but custom metadata records semantic inspection disabled, or workspace metadata fails
- **THEN** the composer respectively explains that semantic scenarios do not enable custom inspection or marks the current checks unavailable without asserting they are disabled

### Requirement: Transient custom draft and echo result
Custom drafts and immediate results SHALL stay in current-page memory and render as text. They MUST NOT enter browser storage, URLs, reporting/history, application logs or metadata. Leaving Interactions SHALL clear draft/output; a new run SHALL clear prior output. Echo result SHALL be labelled approved input returned by Local echo; generated result SHALL be labelled uninspected model response.

#### Scenario: Sensitive HTML-like input or output
- **WHEN** custom text, echo or model output contains sensitive or HTML-like canaries
- **THEN** only the current composer and immediate result may display the corresponding text, no HTML executes and reporting/catalog/workspace/history/logs/storage contain none of it

#### Scenario: Navigation during execution
- **WHEN** an operator leaves and returns to Interactions while a POST remains pending
- **THEN** draft/output are cleared, late results cannot refill the abandoned view and a second run stays disabled until the pending request settles; navigation does not claim server cancellation

### Requirement: Server-owned synthetic catalog
An explicitly enabled Demo view SHALL expose a fixed server-owned scenario catalog with safe titles/descriptions, expected outcomes, prerequisites and simulation labels. Content, target and execution profile MUST be resolved on the server. Catalog/reporting APIs MUST NOT return prompts, transformed content, generated output, semantic raw responses/scores or configuration endpoints.

#### Scenario: Disabled or unavailable semantic demo mode
- **WHEN** Demo is disabled or the startup semantic demo option is disabled
- **THEN** disabled Demo cannot execute scenarios; enabled Demo shows semantic cards as disabled with safe prerequisite instructions, without enabling controls dynamically

#### Scenario: Synthetic payloads
- **WHEN** credential, email and private-key scenarios are inspected by automated tests
- **THEN** fixed values are synthetic detector fixtures, no usable private key or real credential is present, and attack signature text is never executed

### Requirement: Readable scenario expectations and prerequisites
Every scenario SHALL explain its test, why its expected action follows its fixed profile and which runtime purposes are needed. Safe explanations MUST contain no payloads or configuration endpoints. Disabled scenarios SHALL remain selectable for explanation while execution stays disabled. Prerequisites MUST describe configuration needs without asserting runtime readiness.

#### Scenario: Scenario selection before execution
- **WHEN** the operator selects any enabled or disabled scenario
- **THEN** its title, safe test explanation, expected action/error with readable reason, synthetic/simulation label and configuration/runtime prerequisites are visible without copying its hidden payload into the composer or dispatching any interaction

#### Scenario: Runtime independence of expected blocking
- **WHEN** a deterministic blocking scenario is selected with no local model runtime
- **THEN** its explanation states that expected BLOCK needs no generation call; it does not promise availability or change the configured target if actual enforcement permits forwarding

### Requirement: Real governed scenario execution
Every scenario SHALL enter the existing interaction boundary and control pipeline with a server-generated UUID. Deterministic controls, enabled semantic evaluation, validated findings, central policy, redaction and required audit/reporting MUST precede any eligible target invocation. Browser clients MUST NOT call Ollama or set profile, runtime, policy, model, target or content for a scenario.

#### Scenario: Forged scenario override
- **WHEN** a request mixes scenario ID with target/content or supplies unknown ID, policy, model, endpoint or fault fields
- **THEN** it is rejected before evaluation with sanitized validation failure and zero evaluator/target calls

#### Scenario: Profile and interaction isolation
- **WHEN** concurrent scenarios use different startup-bound profiles
- **THEN** each retains its own policy/model/control bindings and UUID, shares required reporting health and cannot alter another run or ordinary interaction service

### Requirement: Deterministic live demonstrations
The catalog SHALL retain the eleven original scenarios and add github-pat, github-oauth, labelled-ssn, pickle-os, pickle-posix, encoded-exec, multiple-pii and pii-and-secret for nineteen total. Each existing deterministic finding code MUST have a prepared example. Eligible live runs SHALL use the existing local model target; BLOCK MUST make zero target calls. Runtime-free tests SHALL verify exact redacted target input.

#### Scenario: Benign real response
- **WHEN** the benign scenario runs with a provisioned available local target
- **THEN** actual policy ALLOW precedes one audited generation call and the existing interaction result delivers actual generated text

#### Scenario: Redacted-only forwarding
- **WHEN** the synthetic email scenario runs under the deterministic demo policy
- **THEN** pii.email maps to REDACT and only centrally transformed input reaches the target once, with no raw/transformed text in reporting

#### Scenario: Three deterministic attack families
- **WHEN** supported synthetic credential, complete private-key envelope and historical signature scenarios run
- **THEN** their existing registered findings centrally map to BLOCK and each has zero target calls

#### Scenario: GitHub credential shapes
- **WHEN** github-pat or github-oauth runs with its fabricated supported token shape
- **THEN** secret.github_pat or secret.github_oauth respectively centrally maps to BLOCK with zero target calls, without claiming provider authentication or coverage of unsupported token forms

#### Scenario: Labelled SSN redaction
- **WHEN** labelled-ssn runs under its fixed deterministic policy
- **THEN** pii.us_ssn maps to REDACT, the fictional number alone is replaced before one audited target call, the label is retained and no identity verification is claimed

#### Scenario: Remaining inert attack indicators
- **WHEN** pickle-os, pickle-posix or encoded-exec runs with its supported literal
- **THEN** the corresponding attack.pickle_os_system, attack.pickle_posix_system or attack.python_exec_base64 finding maps to BLOCK, zero target calls occur and no literal is executed, unpickled or decoded for execution

#### Scenario: Multiple sensitive values
- **WHEN** multiple-pii runs with a synthetic email and fictional labelled SSN
- **THEN** both pii.email and pii.us_ssn map to REDACT, only centrally transformed text with both values removed reaches one audited target call and reporting contains neither original nor transformed text

#### Scenario: Deterministic blocking precedence
- **WHEN** pii-and-secret runs with a synthetic email plus a supported separately framed bearer header line
- **THEN** pii.email and secret.bearer are both recorded, central BLOCK wins over REDACT and the target is not invoked

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

### Requirement: Plain-language observed reasons
The workspace, overview finding labels and event detail SHALL show readable control/finding meanings with technical identifiers retained as supporting text. Actual reasons MUST derive only from the interaction response and matching recorded evidence, never scenario expectations. Unknown codes SHALL retain neutral labels and literal identities. No explanation SHALL expose content, scores or raw diagnostics.

#### Scenario: Actual decision explanation
- **WHEN** recorded findings produce REDACT or BLOCK
- **THEN** the result identifies their readable meanings, recorded mapped actions and resulting forwarding consequence while the matching overview/detail uses consistent labels; detection limits are described without identity, credential-authenticity or general safety claims

#### Scenario: Recorded details unavailable
- **WHEN** only an immediate response is available
- **THEN** its actual codes/action/result remain explainable but recorded counts, mapped actions, audit persistence and completion are unavailable rather than reconstructed from expected findings

### Requirement: Separate failures from security decisions
The result SHALL explain what happened, why it can be established and a relevant next step. Evaluation failure MUST show no policy decision and no target invocation. Target failure SHALL retain an eligible action only when recorded evidence supplies it. Validation, audit, service and connection failures MUST stay distinct from BLOCK. No error alone SHALL identify an unrecorded runtime cause.

#### Scenario: Evaluation failure explanation
- **WHEN** evaluation_failed is returned
- **THEN** the UI says a safety check could not finish and nothing was sent to the target, attributes a failed semantic attempt only if recorded, and suggests checking configured evaluator/runtime without claiming a specific missing-model, transport or schema cause

#### Scenario: Generation failure explanation
- **WHEN** target_failed is returned with a matching audited ALLOW or REDACT decision
- **THEN** the UI shows both the eligible policy action and unsuccessful target execution, recommends checking the configured runtime/model and neither declares full success nor retries or switches targets

#### Scenario: Validation and audit failures
- **WHEN** invalid_request or audit_failed is returned
- **THEN** the UI respectively explains request rejection without invented control findings or failure of required auditing with zero target dispatch, and supplies a relevant input/configuration or reporting-health next step

#### Scenario: Unknown connection outcome
- **WHEN** connectivity is lost after submission or historical completion is unknown
- **THEN** the UI separates available immediate and historical facts, explains the uncertainty and directs the operator to evidence without promising cancellation or repeating the POST

### Requirement: Full expected versus observed comparison
Scenario results SHALL compare expected action/error and required findings against actual evidence. Full success MUST also establish expected target/semantic completion. Missing evidence SHALL yield an unverifiable expectation, not invented success or failure. Extra valid semantic categories MUST remain visible and SHALL NOT fail an otherwise satisfied required-category expectation.

#### Scenario: Eligible action with unsuccessful target
- **WHEN** a normal ALLOW or REDACT scenario records its expected action but target execution fails
- **THEN** the UI shows the action match and execution failure separately, and does not claim that the scenario fully matched its expectation

#### Scenario: Blocking and fault outcomes
- **WHEN** a BLOCK scenario or labelled transport-failure scenario completes
- **THEN** full match requires the expected action/error and findings plus respectively durable not_invoked, failed semantic with not_invoked, or retained eligible decision with failed target completion evidence; missing detail is labelled cannot verify full expectation

### Requirement: Live semantic acceptance of the workbench
Workbench acceptance SHALL require separate live rehearsal of nineteen scenarios and custom input with preprovisioned generation/evaluator runtimes. Mock scores MUST NOT establish live semantic success. Missing prerequisites or valid contrary outcomes SHALL leave acceptance incomplete. Strict classifier validation, fixed thresholds and failure behavior MUST remain intact; normal tests MUST remain runtime-independent.

#### Scenario: Required live semantic observations
- **WHEN** the configured preprovisioned evaluator is rehearsed
- **THEN** custom benign input under semantic policy is actually allowed, each semantic attack emits its required category and BLOCK, hybrid records both deterministic and semantic findings with no target dispatch, and only safe status/identity/timing evidence is retained

#### Scenario: Missing model or failed live evaluation
- **WHEN** a required model/runtime is absent, evaluation fails, or actual findings do not satisfy a required category
- **THEN** rehearsal records NOT RUN or FAIL as appropriate and workbench acceptance remains incomplete without automatic provisioning, repaired scores, weaker validation, lowered thresholds or fabricated decisions

#### Scenario: Precise cause not established
- **WHEN** historical evidence contains only evaluation_failed
- **THEN** the operator instructions distinguish configuration/prerequisite verification from an unproven cause, retain prior failure evidence and require separate reviewed scope authorization for any confirmed adapter/core contract fix

### Requirement: Transient result and deterministic verification
Successful target text SHALL be delivered only via the existing interaction result and displayed transiently as plain text with echo/model labels. It MUST NOT enter reporting/catalog/workspace APIs, historical detail, logs or browser storage. Required automated tests SHALL use deterministic doubles without Ollama; real evaluator/generation SHALL be exercised separately for live rehearsal.

#### Scenario: HTML-like output and privacy
- **WHEN** an allowed interaction returns sensitive or HTML-like generated text
- **THEN** only its current transient result panel receives the uninspected text, no HTML executes and catalog/reporting/history/logs/storage exclude it

#### Scenario: Runtime-free test suite
- **WHEN** required tests run with Ollama absent
- **THEN** all catalog, policy, redaction, audit-order, zero-call, semantic-category and sanitized failure assertions run deterministically

### Requirement: Predictable single-run controls
The workspace SHALL allow one active run across custom and scenario actions, show waiting and actual measured completion states, refresh matching reporting after completion and never automatically retry execution. A disconnected request MUST be labelled outcome unknown rather than assumed failed or safely cancelled.

#### Scenario: Double click or network interruption
- **WHEN** an operator double-clicks Run or connectivity is lost after submission
- **THEN** the panel issues one POST, avoids retry and explains unknown outcome without claiming daemon cancellation

#### Scenario: Switching execution modes
- **WHEN** a custom interaction is running and the operator attempts Run scenario, or vice versa
- **THEN** one shared run lock prevents a second POST and each outcome remains associated with its own submitted target/profile and UUID
