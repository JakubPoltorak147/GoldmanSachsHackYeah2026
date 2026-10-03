# AI Control Layer Challenge Requirements

## Purpose

This document is a repository-oriented summary of the external AI Control Layer
challenge requirements.

The original challenge document is preserved under:

`docs/reference/ai-control-layer.pdf`

If this summary conflicts with the original challenge document, the original
document takes precedence.

This file describes external challenge scope. It does not define current
implemented behavior. Current required product behavior is defined by OpenSpec.

## Challenge objective

Build a lightweight and flexible AI Control Layer that can act as a gateway,
proxy, middleware, SDK wrapper, or equivalent intermediary between applications
and AI systems.

The layer should be suitable for interactions involving systems such as:

- AI agents;
- MCP services;
- LLMs;
- external APIs;
- application-to-agent communication;
- agent-to-agent communication;
- agent-to-model communication;
- agent-to-MCP communication.

The control layer must enforce security, privacy, and resource controls from a
centralized configuration source.

It must be able to inspect, redact, allow, or block interactions and provide
reporting suitable for security and management use.

## Defense architecture

The solution must demonstrate a hybrid defense architecture.

The architecture should combine:

- deterministic, non-AI controls;
- AI-based or semantic controls.

Deterministic controls may include pattern matching for PII or secrets and
checks related to authentication or access requirements.

Semantic controls should provide deeper inspection where deterministic rules
alone are insufficient.

The security architecture should remain practical enough to avoid applying an
expensive semantic control when a cheaper deterministic control is sufficient.

## Expected deliverables

### Functional AI Control Layer

Provide a working gateway, proxy, middleware, SDK wrapper, or equivalent
component that can be integrated into AI workflows.

A simple architecture diagram must be provided.

### Sample configuration

Provide documented configuration demonstrating:

- configured controls or guardrails;
- different strictness, threshold, or adherence settings where applicable;
- budget rules.

### Interactive dashboard

Provide a simple interactive UI displaying information such as:

- configured controls;
- security posture;
- blocked threats;
- resource consumption or cost metrics.

### Executable test suite

Provide an automated test suite covering both positive and negative cases for
implemented controls.

The suite should also demonstrate implemented budget-limit and exploit-mitigation
behavior.

## Formal capability requirements

### Centralized Policy Engine

A centralized configuration source must manage security behavior.

Relevant policy areas include:

- enabled controls;
- sensitivity thresholds;
- BLOCK versus REDACT behavior;
- allowed LLM models;
- resource limits;
- financial budgets.

### Deterministic controls

The system must include deterministic security controls.

Examples in the challenge include:

- PII detection;
- secret detection;
- authentication or access checks.

### Semantic controls

The system should use AI-based or semantic controls where appropriate as part
of the required hybrid defense architecture.

### Budget and resource governance

The design must address resource and financial governance.

Relevant examples include:

- resource access;
- compute time;
- token consumption;
- commercial API spend;
- locally hosted model resource consumption.

### Historical attack mitigation

The solution should address detection or mitigation of known attack patterns.

Examples include:

- malicious code execution;
- unsafe deserialization;
- supply-chain attacks affecting model repositories.

The design should allow externally managed attack signatures or equivalent
security intelligence to influence enforcement.

### Security reporting and auditing

The system must provide security reporting and audit information suitable for
security teams and management.

Relevant information includes:

- blocked interactions;
- policy violations;
- system usage;
- budget usage;
- resource consumption;
- security events.

### Self-testing

Automated tests must demonstrate that implemented controls behave correctly for
both allowed and rejected or transformed interactions.

## Validation expectations

Assume evaluators may:

- execute the provided automated test suite;
- send unprepared, ad-hoc prompts;
- attempt to bypass implemented controls;
- modify configuration files;
- enable or disable controls;
- adjust thresholds;
- modify external feeds where supported;
- exceed configured budgets;
- inspect logs;
- inspect dashboard information;
- observe control-layer latency and performance telemetry.

The system should behave coherently under those conditions.

## Technical constraints and freedoms

The implementation stack is unrestricted.

Open-source tools may be used subject to their licenses.

The challenge does not provide proprietary datasets, paid API subscriptions, or
specific hardware.

The solution should therefore be runnable on the team's own environment without
depending on a provided commercial AI subscription.

Local models, including models exposed through systems such as Ollama, may be
used.

## Evaluation criteria

The challenge evaluation weights are:

| Area | Weight |
| --- | ---: |
| Robustness of the solution and quality of guardrails | 30% |
| Architecture and performance efficiency | 20% |
| Security reporting | 20% |
| Completeness of the self-testing suite | 15% |
| Practical implementability and scalability | 15% |

## Relationship to internal product goals

This document records the external challenge requirements.

`docs/project-context.md` may intentionally define stronger internal product
goals than the challenge itself.

For example, an internal goal can promote an example or architectural direction
from the challenge into an explicit project requirement.

Such strengthening must not be represented as wording from the original
challenge.

OpenSpec remains authoritative for concrete behavior that the repository is
currently required to implement.
