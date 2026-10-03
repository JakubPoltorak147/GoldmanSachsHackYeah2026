# Design

## Context

See [proposal.md](proposal.md) for motivation and the four delta specs for required behavior. The repository has no application implementation or current capability specs. The first runtime must prove a complete local request path and support deterministic tests without a provider, database, or paid API.

## Goals / Non-Goals

**Goals:**

- Keep HTTP validation, security evaluation, policy resolution, dispatch, and audit serialization at distinct boundaries.
- Make the content observed by the target and the absence of target calls directly testable with a spy adapter.
- Prevent untrusted content and exception details from crossing into audit records or error responses.

**Non-Goals:**

- Claiming comprehensive email or PII detection, durable audit retention, target completion telemetry, identity verification, response controls, or guarantees about request throughput or ordering across requests. Complete per-request audit records are still required under concurrent evaluation.
- Adding a generic pipeline, plugin framework, remote target discovery, policy reload, or a separate whole-request byte limit.

## Decisions

### 1. Small synchronous application and contracts

Use Python 3.12+, Poetry with `package-mode = false`, FastAPI and Pydantic at the HTTP boundary, PyYAML for configuration, and a plain synchronous service path. Use Uvicorn to run the app; pytest, httpx and Ruff support tests and checks. FastAPI thread-pool scheduling is an implementation detail, not a spec requirement. A representative layout is `app/control_layer/{api,domain,controls,policy,service,targets,audit}.py`, `config/policy.yaml`, `tests/unit/`, and `tests/integration/`. Prefer a single module per concern until a real need to split it appears.

Use frozen standard-library dataclasses and enums for the core. `Interaction(id: UUID, target_id: str, content: str)` is immutable; the server creates the UUID after HTTP validation. There is no principal field or arbitrary metadata. The first target registry contains only `local-echo`, so request input cannot select a URL. Text is the JSON-decoded string exactly as received; there is no trimming, case conversion, or Unicode normalization. Python string indices are the coordinate system for spans.

`Finding(control_id, code, span: Span | None)` contains only trusted identifiers and optional source location. It contains neither detected text nor an enforcement action. `Control` is a protocol with a stable ID and `evaluate(interaction) -> tuple[Finding, ...]`. `FindingResolution(finding, rule_id, action)` records the policy mapping. `Decision(action, evaluated_controls, resolutions, reason_code)` is the completed policy result. These objects can be tested without FastAPI, YAML, or an external target. A control exception or invalid contract is represented by a separate internal evaluation error, never by `Finding` or `Decision(BLOCK)`.

Alternative considered: Pydantic models throughout the core. Boundary-only Pydantic keeps domain rules independent from transport validation and serialization.

### 2. Strict, fixed policy snapshot

At startup, load a configured YAML file, defaulting to `config/policy.yaml`, and construct one immutable policy snapshot. An administrator can select another file through a documented configuration path for tests and demonstrations; request data cannot select policy. The initial schema has a version, a safe policy ID, and an explicit `controls.email-address.enabled` flag with a `findings.pii.email` mapping to one of `ALLOW`, `REDACT`, or `BLOCK`. The checked-in default enables the control and maps its finding to `REDACT`.

Parse YAML safely while detecting duplicate keys; reject malformed syntax, unknown fields, unsupported schema versions, unknown controls or codes, unsupported actions, and missing mappings for enabled controls. Validate configured mappings even when the control is disabled. Fail startup on an unreadable or invalid policy file. There is no fallback permissive policy and no hot reload. Produce a digest from the validated policy configuration for audit correlation; the digest is of policy configuration, never interaction content.

Alternative considered: permissive defaults for missing rules. They would make a typo capable of silently weakening enforcement.

### 3. Email detection with an explicit bounded grammar

The one control inspects the original `content` and emits `pii.email` findings. It recognizes unquoted ASCII dot-atom local parts with ASCII letters, digits, and `!#$%&'*+-/=?^_`{|}~` in atoms, separated by single dots. The local part has 1–64 characters, cannot start or end with a dot, and cannot contain consecutive dots. The domain has at least two ASCII DNS labels, each 1–63 characters; labels contain letters, digits, or internal hyphens and cannot start or end with a hyphen. The final label contains 2–63 ASCII letters. The complete domain is at most 253 characters. Matching is case-insensitive but never changes the source text.

Inspect complete address-like candidates around each `@`, then validate the whole candidate rather than searching for a valid suffix or shortened prefix. Surrounding `< >`, parentheses, comma, whitespace, and a sentence-ending period are delimiters, not part of a finding. A period inside the domain remains part of the candidate; trailing sentence punctuation is excluded. Characters immediately adjoining a candidate that make it a larger malformed address-like token must cause rejection rather than substring detection. In particular, test consecutive dots, overlong local parts, overlong domain labels, invalid domain continuations, and adjacent non-ASCII address characters. A detector may use regular expressions internally, but tests must establish full-candidate behavior and exact spans, including when Unicode text precedes the address.

Quoted local parts, Unicode address characters, domain literals, and internationalized domain encodings are unsupported. Reject a candidate if any domain label begins with `xn--` (case-insensitive), even though it otherwise fits the ASCII DNS-label grammar. HTML/percent/base64 encoded text and obfuscations such as `alice [at] example.com` are also unsupported. JSON escapes that decode to ordinary ASCII before evaluation are treated as ordinary text; no secondary decoding is performed. This control must be named email-address detection in documentation, not general PII protection.

Alternative considered: a broad RFC email parser or secret detector. Both add complex coverage and more ambiguous false-positive and bypass claims to the first vertical slice.

### 4. Central decision and redaction

Run enabled deterministic controls in configured order. This change has one production control and one production finding code. Validate that each returned finding identifies the control that produced it, uses a known code, and has a valid optional span within the original content. The email control always supplies a span. Map each finding through the fixed policy; no findings yields `ALLOW`. Choose the strongest mapped action with `BLOCK > REDACT > ALLOW` and record rule resolutions and safe reason codes. A finding mapped to `ALLOW` remains explainable but does not alter content. Test mixed-action precedence and selective redaction with locally constructed policy snapshots and test-only trusted finding codes at the pure decision-engine boundary; these test fixtures are never accepted by the production policy loader or HTTP API.

For `REDACT`, require valid nonempty spans from every finding mapped to that action. Gather only those spans, sort and merge overlapping or adjacent intervals, and build new text from slices of the original content with one `[REDACTED]` marker per merged interval. Do not perform sequential replacements on already changed text. Create a new immutable Interaction carrying the redacted content; retain the original only inside the current request's evaluation path. For `ALLOW`, pass the original Interaction unchanged. For `BLOCK`, call no target. The service, not the control, makes these choices.

An exception in control execution, inconsistent finding identity or mapping, or invalid required span raises an internal evaluation failure. The service stops before dispatch and returns a safe operational outcome. It does not fabricate a security Finding or a policy BLOCK. Tests assert zero target calls for each failure.

Alternative considered: allowing controls to return actions or directly edit content. That would split enforcement among controls and make policy precedence difficult to prove.

### 5. Dispatch and audit ordering

`TargetAdapter.invoke(interaction) -> TargetResult` is the target boundary. The local echo adapter returns only the content it received. The service creates a decision audit event before invoking the target, and synchronous event emission is a gate: if the audit sink cannot accept the event, it makes zero target calls and reports a sanitized service failure. An emitted decision event records forwarding eligibility, not successful execution. A subsequent target failure produces a sanitized target error; it does not rewrite the earlier event.

Use a dedicated `AuditEvent` type and an allowlisted serializer, rather than serializing Interaction, Finding, Decision, or exception objects directly. Include event type, server interaction ID, UTC timestamp, fixed target ID, policy digest, evaluated control IDs, an explicit enabled/disabled status for the registered email control, decision action, trusted finding codes/counts, forwarding eligibility, and evaluation duration. Exclude raw content, matched values, snippets, content hashes, spans, and raw exception text. A simple synchronous JSON-lines sink to application stdout is sufficient for this slice; no retention guarantee is claimed. Serialize a complete JSON line before acquiring a sink lock, then write that line and flush while holding the lock; verify the write count equals the line length, and only a completed write and flush counts as accepted. Mark the sink unhealthy after any write/flush failure, including a short write without an exception, so subsequent calls cannot dispatch behind a corrupted stream. Avoid raw request-body and exception logging in application code; run the demo server without access logs that may include untrusted query strings.

If evaluation fails before a decision, create a separate safe operational event with a fixed error code when the audit sink is available. It carries no Finding and no `BLOCK` action. If the sink itself fails, the service still stops dispatch; guaranteed emission is impossible without a working sink or durable store. The response stays sanitized. Tests inject a failing sink and inspect emitted fields with sensitive input.

Alternative considered: emitting the decision event after the target call. A sink failure then permits a target interaction with no audit record.

### 6. HTTP behavior and validation

Expose `POST /v1/interactions` with a strict Pydantic request containing `target_id` and `content`. Reject extra fields, missing fields, wrong types, empty content, unsupported targets, lone Unicode surrogates, malformed JSON syntax, and content longer than 16,384 Python characters. Exactly 16,384 characters is valid. Count Python characters only after JSON decoding; a lone surrogate is not a valid Unicode scalar for this text contract. Do not add the previously proposed 64 KiB whole-request limit. Use sanitized validation and exception handlers for both model and JSON parsing errors so Pydantic input echoes, rejected-body fragments, framework tracebacks, and exception strings do not enter responses.

The response includes the server interaction ID, decision action, safe reason and finding codes, and the target result only for eligible decisions. No raw match values or source spans appear in audit events; the response also need not expose spans. Use `200` for forwarded `ALLOW`/`REDACT`, `403` for policy `BLOCK`, `422` for invalid requests, `503` for internal evaluation or audit failure, and `502` for target failure. A `503` has no policy decision or synthetic Finding. The endpoint itself stays thin; core security tests call the service and decision components directly, while httpx verifies HTTP behavior.

Alternative considered: returning `BLOCK` for every failure. That would blur a policy enforcement result with an unavailable security service.

## Risks / Trade-offs

- Narrow ASCII grammar may miss real addresses → label the control narrowly and test documented unsupported forms without implying broad PII protection.
- Candidate boundary errors can detect an invalid substring → test malformed, overlong, adjacent-Unicode, and punctuation cases before relying on the detector.
- Sensitive values can leak through automatic validation errors or serialization → use strict allowlisted DTOs and sanitized error handlers; assert absence of input in response and audit tests.
- stdout audit has no durable delivery guarantee → gate dispatch on synchronous emission, describe the record as a decision event, and defer durable storage to a later change.
- No whole-request byte limit leaves transport resource consumption outside this change → enforce the approved 16,384-character content limit and treat transport limits as a deployment concern for later review.

## Migration Plan

This is a new API with no existing clients or data migration. Start the service only after its policy file validates. A rollback removes the new service deployment; no persistent application state needs migration. Policy edits take effect after restart.

## Assumptions to confirm at review

- The proposed HTTP response fields and `200`/`403`/`422`/`502`/`503` status mapping are acceptable before the first client integrates.
- The chosen ASCII grammar, including its final-label rule and unsupported forms, matches the intended first-control demonstration.
- A flushed stdout decision event, with no durability or target-completion claim, is sufficient audit behavior for this foundation.
