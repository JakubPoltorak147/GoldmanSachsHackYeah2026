# Proposal

## Why

The repository has product goals but no application path through which an interaction can be evaluated, governed, and audited. This change establishes the smallest local, testable execution path so later controls can use one policy and decision boundary.

## What Changes

- Add a text-only HTTP interaction API with a server-generated interaction ID and a fixed local echo target.
- Detect a deliberately bounded set of ASCII email addresses with one deterministic control that returns structured findings.
- Load strict policy at startup, map finding codes to `ALLOW`, `REDACT`, or `BLOCK`, and make the final action in a central decision engine.
- Forward original text for `ALLOW`, centrally redacted text for `REDACT`, and no text for `BLOCK`.
- Emit a structured decision audit event before target dispatch, and fail closed on internal evaluation or audit failures without representing them as security findings.
- Add fast and integration tests, run instructions, and documentation of the architecture once it exists.

## Capabilities

### New Capabilities

- `interaction-gateway`: validate a text interaction, expose its decision through HTTP, and forward eligible content through a target boundary.
- `email-address-detection`: detect supported ASCII email addresses and return safe, structured findings.
- `policy-decisions`: validate startup policy, resolve findings into actions, and redact selected input centrally.
- `decision-audit`: produce safe decision events before forwarding and prevent dispatch when the audit sink fails.

### Modified Capabilities

None; there are no current capability specs.

## Impact

This introduces the first Python application, a policy file, automated tests, and `POST /v1/interactions`. The initial runtime uses Python 3.12+, Poetry in non-package mode, FastAPI, Pydantic, and PyYAML, with pytest, httpx, and Ruff for verification. A local echo adapter needs no database, external provider, paid API, dashboard, authentication system, policy reload, response inspection, semantic control, or asynchronous pipeline.

## Assumptions to confirm at review

- The HTTP response shape and status mapping proposed in the design are acceptable for this new API, which has no existing clients.
- A decision audit event records forwarding eligibility rather than target completion; durable retention and completion telemetry are deferred.
- The chosen explicit ASCII email grammar is a suitable first-control boundary, with unsupported forms documented and tested.
