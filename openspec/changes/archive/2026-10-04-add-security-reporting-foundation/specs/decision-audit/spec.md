# Decision Audit Delta

## ADDED Requirements

### Requirement: Durable required audit gate
Default application auditing SHALL retain existing JSON-lines emission and require successful durable safe reporting persistence before target dispatch. Storage failure SHALL fail the gate as audit_failed, with zero target calls. Existing decision fields and upstream write/flush poisoning MUST remain unchanged. There SHALL be no silent stdout-only fallback.

#### Scenario: Dual gate ordering
- **WHEN** an eligible interaction is evaluated
- **THEN** existing JSON-lines emission succeeds and its safe reporting transaction commits before the retained target is invoked once

#### Scenario: Persistence failure after stdout
- **WHEN** stdout emission succeeds but durable commit fails
- **THEN** no target is called, the service returns audit_failed, later gates fail closed and stdout evidence is not misrepresented as durable execution evidence

### Requirement: Separate reporting completion evidence
Invocation completion SHALL append separate safe reporting evidence, never modify a decision audit record or add raw output to audit. Existing stdout decision records SHALL continue to describe eligibility only. Completion-write failure MUST preserve the obtained target outcome and prevent subsequent dispatch through the unhealthy reporting gate, without retrying invocation.

#### Scenario: Successful or failed target
- **WHEN** the adapter returns a valid result or fails after required decision auditing
- **THEN** separate durable reporting evidence records the invocation outcome, while the original stdout event remains unchanged and does not claim target success

#### Scenario: Missing completion
- **WHEN** the process crashes or completion persistence fails
- **THEN** an eligible decision without durable completion remains unknown; an already committed completion remains authoritative, without a false completion claim, evidence deletion or another target call
