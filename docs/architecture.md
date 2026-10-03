# Architecture

## Implemented decision core

The runtime is Python 3.12+ with Poetry in non-package mode. The implemented
modules under `app/control_layer/` currently provide a pure synchronous core;
HTTP serving, target dispatch, and audit emission are not implemented yet.

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
