# Local Model Target Delta

## MODIFIED Requirements

### Requirement: No output inspection or model governance claim
Documentation SHALL explicitly state that generated output is not security-inspected and local-model input approval does not certify output safety. One fixed operator model SHALL be a deployment restriction only; centralized allowed-model policy governance, semantic guardrails and resource budgets remain future capabilities. Security reporting SHALL be covered by the security-reporting capability and MUST NOT imply those governance or output-inspection capabilities.

#### Scenario: Generated unsafe text
- **WHEN** a valid bounded model response contains sensitive or unsafe text
- **THEN** it returns unchanged as uninspected text without output filtering or a claim of output security

#### Scenario: Local-only deployment
- **WHEN** an operator follows the supported runtime setup
- **THEN** it uses a preprovisioned local model with Ollama cloud disabled, no paid API or credentials, and documents the separately administered daemon as trusted
