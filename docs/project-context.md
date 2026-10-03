# Project Context

## Mission

Build a lightweight AI Control Layer that sits between applications, agents, MCP services, models, and external APIs.

The control layer governs every interaction before it reaches the target system and, where applicable, inspects the response before it returns to the caller.

Its job is to make AI and agentic systems safer to use without coupling security controls to a specific model, agent framework, or provider.

## Product idea

Think of the system as an application gateway and policy enforcement point for AI traffic.

An interaction enters the control layer.

The control layer evaluates it against centralized policy and produces a decision:

- `ALLOW`
- `REDACT`
- `BLOCK`

A decision includes the controls that were evaluated, their findings, and the reason for the final outcome.

Allowed interactions continue to the target adapter. Responses may pass through output controls before returning to the caller.

Every relevant decision produces telemetry and an auditable event.

## Core goals

The system must demonstrate:

- centralized and reloadable policy configuration;
- deterministic security controls;
- semantic AI-based controls;
- authentication and authorization enforcement where applicable;
- data loss prevention for input and output;
- model, tool and resource restrictions;
- budget and resource governance;
- mitigation of known attack patterns;
- security telemetry and audit logging;
- a simple interactive security dashboard;
- an automated positive and negative test suite.

## Architectural direction

This section describes conceptual product direction and constraints, not implemented
components or a selected runtime architecture. The diagram is illustrative;
component contracts, execution order, and integration boundaries must be resolved
in a reviewed and approved OpenSpec change before implementation.

The security core must not depend on a specific LLM provider or agent framework.

Protocol-specific integrations are adapters around a common interaction model.

The conceptual flow is:

```text
Caller
  |
  v
Interaction Adapter
  |
  v
Policy Engine
  |
  +--> Deterministic Controls
  |
  +--> Semantic Controls
  |
  +--> Authorization / Budget Controls
  |
  v
Decision Engine
  |
  +--> BLOCK
  +--> REDACT
  +--> ALLOW
          |
          v
      Target Adapter
          |
          v
      Output Controls
          |
          v
       Response
```

Controls return findings. They do not independently own the final request lifecycle.

The decision engine combines findings with policy and determines the final action.

## Core domain concepts

### Interaction

A normalized request entering the control layer.

It should be able to represent communication such as:

- application to model;
- application to agent;
- agent to model;
- agent to agent;
- agent to MCP service;
- agent to external API.

### Principal

The actor on whose behalf an interaction is performed.

Examples include a user, application, service account, or agent identity.

### Policy

Centralized configuration describing which controls are enabled and how their findings are enforced.

Policy may define:

- enabled controls;
- thresholds;
- `ALLOW`, `REDACT`, and `BLOCK` behavior;
- permitted targets and models;
- permitted tools and resources;
- budgets;
- execution limits.

### Control

A focused evaluator that inspects an interaction or response and produces one or more findings.

Controls should be independently testable.

### Finding

A structured result produced by a control.

A finding contains enough information to explain:

- which control produced it;
- what was detected;
- its severity or score where applicable;
- the action suggested by policy;
- a machine-readable reason.

### Decision

The final result of policy evaluation.

A decision must be explainable and auditable.

### Audit event

A structured record describing a security-relevant interaction or decision.

Audit events must not accidentally persist secrets that controls were intended to protect.

## Initial control families

The project is expected to cover these security areas over its lifetime:

- PII detection and redaction;
- secret detection;
- prompt injection and jailbreak detection;
- authorization and access control;
- model and tool allowlists;
- input validation;
- output data loss prevention;
- budget limits;
- token, execution and iteration limits;
- known attack signatures;
- security audit and telemetry.

This list describes the intended product surface. Individual OpenSpec changes may implement only a clearly stated subset.

## Quality principles

### Policy-driven

Security behavior must be configurable without changing application code.

Important policy changes should be observable without restarting the whole system where practical.

### Explainable

A blocked or redacted interaction must have a structured reason.

The dashboard and audit log should make it possible to understand what happened.

### Testable

Security behavior must be testable without a real external LLM.

Controls, policy evaluation and decision logic must support deterministic tests.

External providers are integration boundaries.

### Provider-independent

The control layer must not require a commercial API.

The project must be runnable with local or mocked targets.

### Secure by default

Failures in security-critical configuration must not silently disable enforcement.

Sensitive values must not be written to logs.

### Performance-aware

Cheap deterministic controls should normally run before expensive semantic controls.

Telemetry should make the latency introduced by the control layer visible.

## Evaluation priorities

When trade-offs are necessary, prioritize work in this order:

1. robustness and quality of controls;
2. architecture and performance;
3. security reporting and auditability;
4. automated testing;
5. practical integration and scalability.

A smaller number of convincing, testable controls is preferable to a large number of shallow demonstrations.

## Demo expectations

Assume that a reviewer may:

- send prompts that were not prepared in advance;
- attempt to bypass controls;
- change policy configuration;
- change thresholds;
- disable or enable controls;
- exceed configured budgets;
- inspect logs and dashboard metrics;
- execute the automated test suite;
- observe control-layer latency.

The implementation must behave coherently under these conditions.

## Non-goals

The project is not primarily an agent framework.

The project is not primarily an LLM application.

The demonstration agent or model exists to prove that the control layer integrates with real AI workflows.

Do not spend substantial project effort building an advanced agent when the same requirement can be demonstrated with a simple existing or local implementation.

## Implementation status

This document intentionally does not track current implementation status.

Use:

- `openspec/specs/` for current required behavior;
- `openspec/changes/` for proposed or approved work in progress;
- `docs/architecture.md` for architecture that actually exists;
- `docs/system-summary.md` for a concise description of current implemented behavior;
- `docs/requirements/traceability.md` for coverage against the external challenge;
- `docs/worklog.md` for completed verification and review evidence.

Implementation decisions belong in reviewed OpenSpec changes and should be added
to `docs/architecture.md` only after they become true.
