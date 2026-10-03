# policy-decisions Specification

## Purpose
Policy decisions combine control findings under one validated startup configuration and determine whether original, redacted, or no content may reach a target.

## Requirements

### Requirement: Strict startup policy
The service MUST load and validate policy against immutable registered controls before accepting interactions. Every registered control MUST have an explicit enabled/disabled entry, and every enabled control MUST have a supported mapping for every declared finding code. Invalid policy MUST prevent startup rather than disabling or weakening enforcement.

#### Scenario: Valid explicit mapping
- **WHEN** policy enables the email control and explicitly maps its finding code to a supported action
- **THEN** the service starts with that mapping available for decisions

#### Scenario: Invalid policy configuration
- **WHEN** policy contains malformed syntax, duplicate keys, unknown fields or controls, unknown finding codes, an unsupported action, or a missing mapping for an enabled control's finding code
- **THEN** the service rejects startup

#### Scenario: Disabled control
- **WHEN** valid policy explicitly disables the email control
- **THEN** that control is not evaluated and its disabled state is observable in the decision audit event

#### Scenario: Multiple registered controls
- **WHEN** two registered controls have explicit boolean enablement and every enabled control has mappings for all its declared codes
- **THEN** startup validates mappings against each control's own registered definitions

#### Scenario: Missing registered control configuration
- **WHEN** an additional control is registered but the selected existing policy file has no entry for it
- **THEN** startup fails closed, even if the operator intended the new control to be disabled

#### Scenario: Explicitly disabled registration
- **WHEN** a registered control is explicitly disabled with omitted findings or a subset of valid mappings
- **THEN** startup accepts it, never evaluates it, and retains its disabled status for audit

#### Scenario: Unsupported redaction mapping
- **WHEN** any supplied policy mapping selects REDACT for a definition that does not support span redaction
- **THEN** startup is rejected even if that control is disabled

#### Scenario: Existing policy compatibility
- **WHEN** an existing valid foundation policy is loaded with the unchanged production email registration
- **THEN** it remains valid with the same effective action mappings and canonical policy digest

### Requirement: Central action resolution
The decision engine SHALL map findings to actions using policy and SHALL apply `BLOCK` over `REDACT` over `ALLOW`. No findings SHALL produce `ALLOW`.

#### Scenario: No findings
- **WHEN** enabled controls return no findings
- **THEN** the final decision is `ALLOW`

#### Scenario: Same finding, different policies
- **WHEN** the same email finding is evaluated under policies mapping its code to `ALLOW`, `REDACT`, and `BLOCK` respectively
- **THEN** each policy produces its configured action with a structured explanation of the finding and applied rule

#### Scenario: Mixed actions
- **WHEN** one finding maps to `BLOCK` and another maps to `REDACT`
- **THEN** the final decision is `BLOCK` and zero target calls occur

#### Scenario: Unmapped runtime finding
- **WHEN** a control produces a finding code that the active policy cannot resolve
- **THEN** evaluation fails closed as an internal service failure, without turning that failure into a security Finding or calling the target

### Requirement: Central redaction
For a `REDACT` decision, the service SHALL replace spans selected by policy with `[REDACTED]` before forwarding, using offsets into the original text.

#### Scenario: Selected spans only
- **WHEN** findings mapping to both `ALLOW` and `REDACT` exist and no finding maps to `BLOCK`
- **THEN** only spans from `REDACT` findings are replaced before the target receives the text

#### Scenario: Multiple and overlapping spans
- **WHEN** selected spans are multiple or overlapping
- **THEN** every selected portion is masked exactly once without exposing text because of shifted offsets

#### Scenario: Invalid required span
- **WHEN** a `REDACT` finding has no valid source span
- **THEN** evaluation fails closed as an internal service failure and makes zero target calls

### Requirement: Immutable control registration catalogue
Control registrations SHALL bind server-owned control identities and finding definitions to evaluators. The catalogue SHALL be immutable and deterministically ordered, with bounded machine identifiers, unique control IDs, and globally unique finding codes. Invalid or duplicate metadata MUST prevent startup; evaluator output MUST NOT establish registration metadata.

#### Scenario: Independent registrations
- **WHEN** two evaluators are registered with distinct control IDs and finding codes
- **THEN** each has an immutable identity, definition catalogue, and evaluator binding available for startup validation

#### Scenario: Duplicate or unsafe metadata
- **WHEN** registrations contain duplicate control IDs, colliding finding codes, empty code catalogues, invalid types, overlong identifiers, or identifiers containing unsupported characters
- **THEN** registration is rejected before serving interactions

#### Scenario: Metadata mutation
- **WHEN** a caller changes its original registration-input collections or an evaluator changes its asserted ID after registration
- **THEN** registered metadata, ordering, and evaluator bindings remain unchanged

### Requirement: Stable startup-bound evaluation
Startup SHALL produce an immutable policy execution plan retaining the exact validated control registrations, mappings, and enablement. Evaluation SHALL reuse those bindings without reconstructing control composition per request. Enabled controls SHALL run in stable registration order; disabled controls SHALL be skipped and remain represented in status metadata.

#### Scenario: Repeated evaluation uses startup bindings
- **WHEN** multiple interactions are evaluated after startup
- **THEN** each uses the same validated registration bindings and mappings without rebuilding the control catalogue

#### Scenario: Policy key order
- **WHEN** equivalent policy files list controls or finding mappings in different key orders
- **THEN** evaluation follows the same registered order and their canonical policy digests are equal

#### Scenario: Mixed enabled and disabled entries
- **WHEN** a plan contains enabled and disabled controls
- **THEN** only enabled registrations are evaluated and all entries retain explicit audit status

#### Scenario: Inconsistent runtime resolution
- **WHEN** runtime resolution cannot reconcile validated findings, enabled evaluations, or the bound mappings
- **THEN** evaluation fails closed as an operational service failure with no synthetic finding, no policy BLOCK, and zero target calls

### Requirement: Actual-producer finding validation
Each evaluator's findings MUST be validated against the server-owned registration actually invoked. Asserted producer IDs MUST NOT select validation metadata; mismatches or undeclared codes MUST fail closed. Downstream producer identity SHALL derive from that registration. Findings SHALL contain no matched values or enforcement decisions.

#### Scenario: Forged producer identity
- **WHEN** one registered evaluator returns a finding asserting another registered control's ID or code
- **THEN** evaluation fails closed without accepting the other control's policy mappings or calling a target

#### Scenario: Malformed finding output
- **WHEN** output has an invalid container, finding type, identifier type, code, or supplied source span
- **THEN** evaluation returns a sanitized operational failure with zero target calls and no security decision

#### Scenario: Registered findings and central policy
- **WHEN** distinct registered controls return valid findings mapped to ALLOW, REDACT, and BLOCK
- **THEN** central policy applies BLOCK over REDACT over ALLOW and retains structured explanations using trusted producer identities

#### Scenario: No findings from multiple controls
- **WHEN** all enabled registered controls return no findings
- **THEN** central policy produces ALLOW and preserves the original interaction

### Requirement: Span-redaction capability contract
Any finding definition supporting REDACT MUST require a source span. Contradictory definitions MUST be rejected at startup. Every span-required finding MUST carry a validated span into original content under every action. Supplied spans MUST use exact integer offsets satisfying original-text bounds. Central redaction SHALL remain span replacement with no evaluator-provided transformations.

#### Scenario: Contradictory definition
- **WHEN** a definition supports REDACT but does not require a source span
- **THEN** registration is rejected before interactions are accepted

#### Scenario: Missing span regardless of policy action
- **WHEN** a REDACT-capable definition produces a spanless finding under ALLOW, REDACT, or BLOCK policy
- **THEN** evaluation fails closed as an operational failure with zero target calls

#### Scenario: Invalid source span
- **WHEN** a finding has boolean or non-integer offsets, negative bounds, an empty/reversed span, or offsets beyond original text
- **THEN** evaluation fails closed with zero target calls

#### Scenario: Spanless non-redactable finding
- **WHEN** a span-optional definition without redaction support returns a valid spanless finding mapped to ALLOW or BLOCK
- **THEN** central policy resolves that mapping without inventing a source span

#### Scenario: Cross-control selective redaction
- **WHEN** findings from multiple controls select overlapping or adjacent REDACT spans and other findings map to ALLOW, with no BLOCK
- **THEN** only selected original-text portions are replaced with `[REDACTED]`, masked once, with interaction identity and target preserved

#### Scenario: Unchanged email semantics
- **WHEN** the existing email evaluator runs through its registration
- **THEN** its supported grammar, whole-candidate rejection, finding multiplicity, and original character spans remain unchanged

### Requirement: Default deterministic pack policy
The default policy SHALL explicitly enable email-address, bearer-credential, pem-private-key, github-token, us-ssn and known-attack-signatures. It SHALL map `pii.email` and `pii.us_ssn` to REDACT, and all declared credential and initial attack codes to BLOCK. Each finding code MUST remain independently configurable according to its registered capabilities.

#### Scenario: Complete default startup
- **WHEN** the expanded production registry and shipped catalog bind the default policy
- **THEN** every control has explicit enablement and every enabled finding code has its default mapping without implicit entries

#### Scenario: Alternative per-code actions
- **WHEN** an administrator changes valid credential/PII mappings independently to ALLOW, REDACT or BLOCK, or attack mappings to ALLOW/BLOCK
- **THEN** the same detector outputs receive those centrally configured actions without detector changes

#### Scenario: Selected control disabled
- **WHEN** an administrator explicitly disables a pack control using valid optional mappings
- **THEN** it is skipped, its disabled status remains audited, and the remaining controls enforce their mappings

### Requirement: Cross-control enforcement and original offsets
Real production-pack findings SHALL compose under existing central precedence and span redaction. No control SHALL redact before another control evaluates original content. BLOCK MUST dominate all other actions regardless of finding order; only REDACT-selected original spans SHALL be replaced, merging overlap/adjacency without shifted-offset exposure.

#### Scenario: Email and credential
- **WHEN** email maps to REDACT and a supported credential maps to BLOCK in the same interaction
- **THEN** the final action is BLOCK with both controls' structured resolutions and no target invocation

#### Scenario: New PII and credential
- **WHEN** labelled SSN and credential findings both map to REDACT with Unicode before their spans
- **THEN** both original values are masked with exact original-character offsets and unrelated text remains unchanged

#### Scenario: Attack and sensitive data
- **WHEN** an attack literal maps to BLOCK and another sensitive-data finding maps to REDACT or ALLOW
- **THEN** BLOCK prevails, retaining all trusted findings in the explanation

#### Scenario: Simultaneous controls and permutations
- **WHEN** all six registered production controls return findings and tests permute control/finding order under equivalent mappings
- **THEN** every valid composition produces the same effective strongest action and redacted content where eligible

#### Scenario: Overlapping bearer and GitHub token
- **WHEN** one header token matches both independent controls and both findings map to REDACT
- **THEN** central redaction masks the shared original span exactly once; an ALLOW mapping for either code cannot weaken a BLOCK mapping for the other

#### Scenario: Allowed and selectively redacted findings
- **WHEN** findings map only to ALLOW, or some map to ALLOW and others to REDACT without BLOCK
- **THEN** ALLOW preserves original content, while REDACT masks only selected findings and preserves labels, separators, identity and target

### Requirement: Production pack fail-closed verification
Automated tests SHALL exercise unknown codes, mismatched producer/code ownership, invalid or missing required spans, unsupported REDACT, incomplete policy entries and control exceptions with the expanded registry. Failures MUST retain sanitized operational semantics with zero target calls, never a synthetic finding or policy BLOCK.

#### Scenario: Forged runtime output
- **WHEN** a pack evaluator asserts another registered producer or an undeclared/foreign code
- **THEN** invoked-registration validation fails closed before decision/audit finding construction or target invocation

#### Scenario: Span required under all actions
- **WHEN** a credential, SSN or attack finding lacks a required span or supplies an invalid original-text span under ALLOW, REDACT or BLOCK
- **THEN** evaluation fails closed, independently of action precedence

#### Scenario: Catalog code and policy mismatch
- **WHEN** an enabled attack catalog declares a code absent from policy, or any selected policy omits a newly registered control
- **THEN** startup fails rather than assigning an implicit action or disablement
