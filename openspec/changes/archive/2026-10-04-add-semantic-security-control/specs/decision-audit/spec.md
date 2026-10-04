# Spec Delta

## ADDED Requirements

### Requirement: Content-free semantic attempt evidence
Audit SHALL optionally include a closed semantic observation with semantic_duration_ms, semantic_model_id and semantic_status succeeded/failed. Duration SHALL cover only the semantic invocation through finding validation, using a monotonic clock, including failed attempts. Identity MUST come from retained startup registration. All fields SHALL be absent together when no attempt occurs. No model scores, output or diagnostic prose SHALL enter audit.

#### Scenario: Successful semantic evaluation
- **WHEN** enabled semantic evaluation succeeds and central policy resolves a decision
- **THEN** audit records finite nonnegative semantic duration no greater than total evaluation duration, registered evaluator identity and succeeded status before any eligible target dispatch

#### Scenario: Failed semantic attempt
- **WHEN** semantic evaluation throws or its findings fail validation
- **THEN** available operational audit records failed attempt duration/registered identity with evaluation_failed, no policy action/findings, and only earlier successfully validated controls in evaluated_controls

#### Scenario: Disabled or not reached
- **WHEN** semantic is disabled, target resolution fails or a preceding control fails
- **THEN** no semantic timing/model/status observation is fabricated and no evaluator call occurs

#### Scenario: Preserved audit gate and privacy
- **WHEN** semantic classification completed but decision audit write/flush or durable commit fails
- **THEN** no target generation occurs, existing poisoning guarantees hold, and no submitted/evaluator content or raw exceptions enter audit; the earlier classifier call does not count as target dispatch
