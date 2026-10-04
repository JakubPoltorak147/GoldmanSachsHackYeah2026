# Spec Delta

## MODIFIED Requirements

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
