# Spec Delta

## ADDED Requirements

### Requirement: Strict semantic threshold policy
The semantic-security policy entry SHALL require threshold when enabled and optionally accept it when disabled. Values MUST be finite exact numbers with 0 < threshold <= 1, excluding booleans/coercion. Threshold SHALL be frozen with the bound policy and included in its digest when supplied. Enabled semantic entries MUST map every registered semantic code to ALLOW/BLOCK. Unsupported REDACT, unknown keys and missing entries MUST fail startup.

#### Scenario: Enabled threshold and mappings
- **WHEN** a complete policy enables semantic-security with threshold 0.75 and all three registered codes mapped to BLOCK
- **THEN** startup binds that threshold and mappings, and central policy resolves semantic findings using unchanged precedence

#### Scenario: Invalid enforcement configuration
- **WHEN** threshold is missing for enabled semantic, zero, negative, above one, nonfinite, boolean, string, duplicated, or supplied to a nonsemantic control, or any semantic mapping uses REDACT
- **THEN** startup fails with sanitized invalid_policy without weakening controls, including invalid supplied settings on a disabled semantic entry

#### Scenario: Disabled configuration
- **WHEN** semantic-security is explicitly disabled with threshold omitted and otherwise valid optional mappings
- **THEN** no semantic evaluation occurs and disabled status remains audited

#### Scenario: Digest attribution
- **WHEN** only a valid configured semantic threshold changes
- **THEN** the policy digest changes; equivalent numeric thresholds and reordered keys produce equal digests

#### Scenario: Historical registry compatibility
- **WHEN** a historical policy is loaded with its unchanged explicit nonsemantic registry
- **THEN** no semantic threshold/default is added to its canonical form and its previous digest remains unchanged

### Requirement: Trusted optional control model metadata
Registration SHALL accept an optional administrator-owned model identity using the existing trusted target-model identifier grammar and bound. The semantic registration SHALL bind the same frozen model as its evaluator. Evaluator output, caller assertions and arbitrary attributes MUST NOT establish this metadata. Finding ownership, span capability validation and stable startup execution SHALL remain unchanged.

#### Scenario: Registered evaluator model
- **WHEN** semantic evaluation is bound at startup
- **THEN** its immutable registration model matches its configured evaluator model without runtime probes

#### Scenario: Invalid or mutated identity
- **WHEN** registration supplies malformed/wrong-type/overlong model metadata or a later evaluator response asserts another model
- **THEN** malformed registration fails startup and runtime assertions never change trusted identity
