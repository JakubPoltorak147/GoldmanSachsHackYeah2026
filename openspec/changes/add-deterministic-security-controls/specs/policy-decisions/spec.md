# Policy Decisions Delta

## ADDED Requirements

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
