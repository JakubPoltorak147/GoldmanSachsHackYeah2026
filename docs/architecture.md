# Architecture

## Implemented decision core

The runtime is Python 3.12+ with Poetry in non-package mode. The implemented
modules under `app/control_layer/` provide a synchronous core and audited
execution service behind a strict FastAPI HTTP boundary.

- `domain.py`: frozen Interaction, Span, Finding, FindingResolution and Decision
  dataclasses, Action enum, Control protocol, and separate operational errors.
  Interaction IDs are server-generated UUIDs; content is preserved exactly.
- `controls.py`: bounded ASCII email-address detection with `email-address` /
  `pii.email` identifiers. It validates whole candidates and reports original
  Python character spans without copying matched content into findings.
- `policy.py`: strict YAML startup loader, immutable policy snapshot and policy
  digest, finding validation, central resolution and original-text redaction.
  Duplicate keys, unknown configuration and unsupported mappings are rejected.
  The default `config/policy.yaml` enables email detection and maps it to REDACT.

Central resolution uses BLOCK > REDACT > ALLOW; no findings yields ALLOW.
ALLOW preserves the original interaction. REDACT merges overlapping or adjacent
selected spans and constructs a new interaction from original slices with
`[REDACTED]` markers. BLOCK produces no forwarding interaction. Invalid findings,
spans or mappings raise an operational evaluation error, never a synthetic finding
or policy BLOCK. Production policy accepts only the registered email finding code.

This is deliberately bounded ASCII email-address detection, not general email or
PII protection. Quoted local parts, Unicode addresses, domain literals, `xn--`
labels, encoded and obfuscated forms are unsupported. No secondary decoding occurs.

Fast deterministic tests live in `tests/unit/`. No external service is required.

## Audited execution path

`service.py` orchestrates the immutable policy snapshot and registered control.
Disabled controls are skipped. It validates control results, resolves policy,
constructs the forwarding interaction, and emits a decision event before dispatch.
ALLOW forwards the original object once, REDACT forwards the transformed object
once, and BLOCK makes zero calls. Operational evaluation or audit failure makes
zero calls and returns a fixed error code with no policy decision or synthetic
finding. Target failures after auditing return a separate sanitized target error.

`targets.py` defines TargetAdapter and TargetResult. LocalEchoTarget returns only
its received content. The service supports injection of a test spy at this boundary;
its only accepted production target ID is `local-echo`.

`audit.py` defines the allowlisted AuditEvent and JsonLinesAuditSink. Events contain
server ID, UTC time, fixed target, policy digest, evaluated controls, explicit control
enablement, action, trusted finding counts, forwarding eligibility and duration.
Operational events have a fixed error code and no action or findings. Neither event
contains content, matched values, source spans, content hashes or exception text.
A decision event records eligibility, without claiming target completion.

The sink serializes a complete JSON line, then writes and flushes under a lock.
Exceptions, short writes and flush failures poison the sink permanently; subsequent
requests cannot dispatch behind a damaged stream. There is no durable retention.
The HTTP application wires one stdout sink for its lifespan.


## HTTP boundary and startup

`api.py` exposes `create_app` and POST `/v1/interactions`. Its lifespan loads the
administrator-selected `CONTROL_LAYER_POLICY` file (default `config/policy.yaml`)
before accepting requests and creates the service with a stdout sink and local
echo target. Invalid startup policy raises sanitized PolicyError; no fallback exists.
Policy is fixed until restart. Test injection preserves the same startup loader.

Strict Pydantic request DTOs forbid extras, coercion, unsupported targets, empty
or over-16,384-character strings, and lone surrogates. JSON-decoded text reaches
Interaction.create unchanged with a new server UUID. Response DTOs expose only
safe codes and the eligible target result. Validation, body parsing and unexpected
errors have fixed sanitized handlers; exception/body details are never serialized.
The endpoint maps forwarding to 200, policy BLOCK to 403, invalid input to 422,
evaluation/audit failure to 503, and target failure to 502.

The synchronous endpoint runs through FastAPI's thread pool. A shared sink lock
keeps per-request records complete under concurrency without promising request
ordering. Uvicorn is documented with access logs disabled. There is no response
inspection, remote target, verified identity, reload, durable audit, database or UI.
Integration tests use httpx at the HTTP boundary; security logic remains covered
by deterministic unit tests. README contains installation, policy and run commands.
