# Decision Audit Delta

## ADDED Requirements

### Requirement: Deterministic pack audit privacy and dispatch
Production-pack audit SHALL retain existing safe fields and expose only trusted registration-derived identities, status and finding counts. Submitted sensitive content, secret/SSN values, attack excerpts, source spans, content hashes, catalog literals and exception text MUST NOT enter records. Eligible invocation MUST follow successful required audit; BLOCK and evaluation/audit failures MUST invoke no target.

#### Scenario: Sensitive values under all actions
- **WHEN** real production detectors find supported credentials, SSNs and emails under ALLOW, REDACT and BLOCK policies
- **THEN** audit records contain appropriate trusted codes/counts/actions but no submitted values, content or spans, including ALLOW cases that intentionally forward original content

#### Scenario: Mixed findings and audit order
- **WHEN** multiple enabled pack controls contribute findings to an eligible decision
- **THEN** one complete safe decision event is emitted before the retained target's exactly-one invocation, with explicit status for every registered control

#### Scenario: Failure paths with sensitive inputs
- **WHEN** a control raises an exception containing submitted secret text, returns forged metadata, or decision audit fails
- **THEN** records/errors remain sanitized and zero target invocations occur, preserving existing sink poisoning guarantees

#### Scenario: Concurrent pack requests
- **WHEN** concurrent interactions contain different sensitive values and attack indicators
- **THEN** findings do not cross requests and each successful audit remains a separate complete parseable record before its corresponding eligible invocation
