# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
