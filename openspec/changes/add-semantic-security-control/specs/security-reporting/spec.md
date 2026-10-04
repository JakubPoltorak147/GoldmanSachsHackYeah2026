# Spec Delta

## ADDED Requirements

### Requirement: Durable closed semantic timing projection
Reporting SHALL persist the closed optional semantic observation atomically with its event and expose it through existing typed list/detail queries plus a separate semantic timing summary. Projection MUST validate exact types, finite nonnegative duration bounded by evaluation duration, enabled registration identity and succeeded/failed status consistency. Evaluator and target model identities SHALL remain distinct. No scores or content SHALL be stored.

#### Scenario: Semantic timing summaries
- **WHEN** history contains succeeded/failed semantic attempts, disabled requests and pre-semantic failures
- **THEN** semantic timing summaries count only attempted observations, including failed attempts; missing observations supply no sample, and operational failures remain distinct from policy BLOCK or invocation

#### Scenario: Forged observation
- **WHEN** an observation supplies an unregistered/wrong model, partial fields, numeric bool, nonfinite/negative/over-evaluation duration, disabled control or inconsistent status
- **THEN** reporting rejects it with a fixed sanitized error without partial persistence or target dispatch

#### Scenario: Target accounting preserved
- **WHEN** an evaluator call occurs and policy BLOCKs or evaluation fails
- **THEN** target status remains not_invoked, target inference timing remains absent and semantic duration is not counted as target invocation

#### Scenario: Historical binding and privacy
- **WHEN** a deployment changes evaluator model/threshold after earlier records were committed
- **THEN** earlier observations retain their original trusted identity/digest and expose no content, output, raw score, hashes, spans or exception text

### Requirement: Non-destructive semantic storage upgrade
New stores SHALL use schema version 2. Startup SHALL accept exact known version-1 stores through one atomic additive upgrade preserving all evidence and setting historical semantic observation fields to null. Unknown or modified schemas and failed upgrades MUST fail startup without deletion, permissive recovery or partial migration. Successful queries SHALL expose version 2; existing storage/audit/completion failure guarantees SHALL remain intact.

#### Scenario: Existing reporting history
- **WHEN** an exact version-1 store containing all actions, findings and completion outcomes is upgraded and reopened
- **THEN** IDs, sequences, history, counts and invocation outcomes are preserved; historical semantic timing samples are absent and new observations persist normally

#### Scenario: Failed or unsupported upgrade
- **WHEN** the old DDL is not exact, the version is unsupported or the migration transaction fails
- **THEN** startup returns a sanitized reporting failure, preserves prior data/schema transactionally and never creates an empty replacement store
