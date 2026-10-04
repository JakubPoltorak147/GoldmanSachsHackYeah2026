# Spec Delta

## Purpose

Provide a polished read-only operator dashboard that makes existing content-free security and operational evidence understandable during the challenge demonstration.

## ADDED Requirements

### Requirement: Read-only dashboard experience
The system SHALL serve a responsive dashboard with summary cards, finding/control rankings, recent timeline and selectable safe event detail. It MUST read reporting only through HTTP and MUST NOT access SQLite, invoke targets or change policy/history. UI assets SHALL be served locally with the existing application.

#### Scenario: Independently usable dashboard
- **WHEN** the dashboard is opened without the workbench or a running Ollama daemon
- **THEN** stored evidence or a truthful empty state renders with no model calls, execution controls or missing workbench dependency

#### Scenario: Responsive and accessible detail
- **WHEN** an operator selects an event on desktop or a narrow viewport using pointer or keyboard
- **THEN** readable detail opens, focus is visible, labels supplement colors and closing the drawer returns focus to the selection

### Requirement: Honest security and operational metrics
The dashboard SHALL display selected-window interaction totals, ALLOW/REDACT/BLOCK counts, operational evaluation failures, succeeded/failed/unknown/not_invoked target counts, deterministic and semantic findings and top producer/code categories. Finding occurrence and affected-interaction counts MUST remain distinct; operational failures MUST NOT count as BLOCK.

#### Scenario: Mixed evidence
- **WHEN** the window contains multiple findings per event and every decision/invocation status
- **THEN** distinct interaction totals match reporting, rankings preserve finding multiplicity, target failures retain their original decisions and unknown is labelled missing completion evidence

### Requirement: Safe identities and measured timings
Rows/details SHALL show recorded target/model and separate semantic evaluator identity when available, evaluated/enabled controls, finding names/counts/mappings and safe reason/error codes. Evaluation, semantic, invocation and total timings SHALL remain separately labelled with sample counts; unavailable observations MUST NOT become zero or fabricated stage timings.

#### Scenario: Missing and historical observations
- **WHEN** selected evidence has no model identity, semantic attempt or durable completion
- **THEN** absent fields are labelled unavailable/not recorded, no success or invocation is inferred, and historical identities are retained

### Requirement: Polling filters and truthful availability
The dashboard SHALL poll every three seconds while visible, refresh existing event outcomes and selected detail, and support time-window, action, target and invocation-status filters. It MUST discard obsolete requests, avoid overlapping cycles, retain selected detail and distinguish loading, empty, stale and error states. Failed reads MUST NOT display invented zeros.

#### Scenario: Completion without new event
- **WHEN** an existing unknown event receives a durable completion without a new sequence
- **THEN** polling updates its outcome and timings without duplicate rows or losing selected detail

#### Scenario: Filter race and read failure
- **WHEN** a filter changes while an earlier request is pending, or a later read fails
- **THEN** obsolete results cannot replace the new filter state; previous valid values are visibly stale until a successful refresh

### Requirement: Content-free display and reusable surfaces
Dashboard evidence and reporting replies MUST exclude input/transformed content, target output, semantic raw responses/scores, secrets, credentials, PII and exception text. Strings SHALL render as text. Event UUID links and safe detail rendering SHALL be reusable by later views without changing reporting response contracts.

#### Scenario: Sensitive output or HTML canary
- **WHEN** interaction output or failures contain secret and HTML-like canaries
- **THEN** no reporting reply or dashboard event detail includes those values and no untrusted HTML executes
