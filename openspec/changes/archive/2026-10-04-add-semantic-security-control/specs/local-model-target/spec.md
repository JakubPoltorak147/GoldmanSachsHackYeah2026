# Spec Delta

## MODIFIED Requirements

### Requirement: Local registered text generation
The system SHALL expose `local-ollama` alongside `local-echo`, using one operator-configured local model. Eligible dispatch SHALL submit one non-streaming generation request containing exactly approved content and return only generated text. The adapter MUST NOT interpret findings, change enforcement, retry or fall back to another target/model.

#### Scenario: Successful generation
- **WHEN** eligible dispatch receives a valid completed generation response
- **THEN** exactly one runtime generation request uses the configured model and the caller receives its response text through the existing content-only result

#### Scenario: Original and centrally redacted prompts
- **WHEN** central policy selects ALLOW or REDACT for a local-model interaction
- **THEN** the submitted prompt is respectively exact original content or exact centrally redacted content, with no adapter-added prompt/history

#### Scenario: Closed dispatch gates
- **WHEN** policy selects BLOCK or evaluation or required audit emission fails
- **THEN** there are zero target-generation runtime requests, including target probes; a separately enabled semantic evaluator can already have made its bounded classification request during evaluation, without invoking this target adapter

### Requirement: No output inspection or model governance claim
Documentation SHALL explicitly state that generated output is not security-inspected and local-model input approval does not certify output safety. One fixed operator model SHALL be a deployment restriction only; centralized allowed-model policy governance and resource budgets remain future capabilities; input semantic detection is separately defined by semantic-security-detection and does not inspect generated output. Security reporting SHALL be covered by the security-reporting capability and MUST NOT imply those governance or output-inspection capabilities.

#### Scenario: Generated unsafe text
- **WHEN** a valid bounded model response contains sensitive or unsafe text
- **THEN** it returns unchanged as uninspected text without output filtering or a claim of output security

#### Scenario: Local-only deployment
- **WHEN** an operator follows the supported runtime setup
- **THEN** it uses a preprovisioned local model with Ollama cloud disabled, no paid API or credentials, and documents the separately administered daemon as trusted


### Requirement: Invocation-only availability
Normal startup and required tests MUST NOT require an installed/running runtime or existing model. Startup SHALL perform only local configuration/registration validation. Actual availability SHALL be determined during eligible generation; absence or unavailability MUST NOT silently change target/model or disable controls.

#### Scenario: Runtime not installed or stopped
- **WHEN** valid application configuration starts without Ollama installed or running
- **THEN** startup succeeds without network probes, local echo succeeds when semantic evaluation is explicitly disabled, and an otherwise eligible model request returns sanitized target_failed after its decision audit; enabled semantic unavailability instead returns evaluation_failed before target dispatch

#### Scenario: Model absent
- **WHEN** the configured model does not exist and generation returns a missing-model status
- **THEN** the request returns sanitized target_failed without downloading a model, fallback, retry or synthetic security decision
