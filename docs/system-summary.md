# System summary and approved assumptions

This document summarizes the implemented `establish-control-layer-foundation`
and `generalize-control-layer-extension-points` changes. It explains the current
application and its relationship to the approved assumptions and original product goals. Required behavior remains defined by
OpenSpec; implementation details are recorded in [architecture.md](architecture.md).

## What the system does

The application accepts text, checks it using a deterministic control, applies
central policy, records a safe audit event, and forwards eligible text to a local
echo target. This establishes a working control-layer boundary that can be tested
without an external model, provider, database, or commercial API.

The current target simply returns the text it receives. There is no model or agent
reasoning in this foundation.

### Request flow

1. **Validate the request.** `POST /v1/interactions` requires exactly `target_id`
   and `content`. The target must be `local-echo`; content must contain 1–16,384
   Python characters after JSON decoding. Wrong types, extra fields, caller-supplied
   identity, malformed JSON, and lone Unicode surrogates are rejected. Valid text
   is preserved without trimming or normalization.
2. **Create an interaction.** The server assigns a UUID. The interaction is
   immutable and contains the ID, target ID, and original content.
3. **Resolve the target and evaluate enabled controls.** The service retains one
   exact registered target binding for audit and dispatch. Startup-bound control
   registrations determine evaluation order and trusted producer identities.
   Findings are validated against the registration actually invoked. The
   email-address control returns structured `pii.email` findings with original-text spans. Findings contain trusted
   identifiers and locations, without copying detected addresses or choosing an
   enforcement action. A disabled control is skipped.
4. **Resolve central policy.** Policy maps findings to `ALLOW`, `REDACT`, or
   `BLOCK`. Precedence is `BLOCK > REDACT > ALLOW`; no findings yields `ALLOW`.
   The decision records safe reasons and applied rule resolutions.
5. **Emit the audit event.** A decision record is written and flushed before any
   eligible target invocation. Evaluation or audit failure stops dispatch.
6. **Apply the decision.** `ALLOW` forwards the original interaction exactly once.
   `REDACT` forwards a new interaction whose selected spans are replaced with
   `[REDACTED]`, exactly once. Overlapping or adjacent spans are merged using
   original offsets. `BLOCK` makes zero target calls.
7. **Return the outcome.** Successful responses include the server ID, action,
   safe reason and finding codes, and echo result. Error responses use fixed codes
   and exclude submitted text and internal exception details.

### Policy configuration

The default [policy](../config/policy.yaml) enables email-address detection and
maps `pii.email` to `REDACT`. An administrator can select another file through
`CONTROL_LAYER_POLICY`. Policy loads before the application accepts requests and
remains fixed until restart.

Unreadable files, malformed YAML, duplicate keys, unknown fields or controls,
unsupported versions or actions, and missing required mappings prevent startup.
Configured mappings are validated even for a disabled control. Requests cannot
select policy. There is no permissive fallback.

## How the three approved assumptions are satisfied

| Approved assumption | Implemented behavior | Boundary of the approval |
| --- | --- | --- |
| HTTP response/status mapping | `200` for forwarded ALLOW/REDACT; `403` for policy BLOCK; `422` for invalid input; `503` for evaluation/audit failure; `502` for target failure. Responses expose safe structured fields. | An operational failure is distinct from a policy BLOCK and creates no synthetic security finding. Validation, evaluation, and audit failures make zero target calls. A target failure can occur after eligible dispatch. |
| Deliberately bounded ASCII email detector | Whole supported candidates are detected, including plus tags, mixed case, and subdomains. Findings use original Python string offsets. Policy decides whether to allow, redact, or block them. | This is bounded email-address detection, not general email or PII protection. Unsupported forms can remain undetected and pass under an ALLOW decision. |
| Flushed stdout audit is sufficient | Safe JSON decision records are written and flushed under a lock before eligible dispatch. Short writes, write exceptions, or flush failures permanently disable that sink and prevent subsequent dispatch. | Flush acceptance does not guarantee durable retention. Records describe decisions and forwarding eligibility, not successful target completion. Durable retention and target-completion records remain out of scope. |

### Email detector coverage

Supported addresses use unquoted ASCII dot-atom local parts of 1–64 characters.
Domains have at least two ASCII DNS labels, each 1–63 characters, and at most 253
characters overall. Labels cannot start or end with a hyphen; the final label is
2–63 ASCII letters. Whole-candidate validation prevents reporting a shortened
suffix or prefix of a malformed or overlong address.

Quoted local parts, Unicode address characters, domain literals, `xn--` labels,
HTML/percent/base64 encoded forms, and obfuscations such as
`alice [at] example.com` are unsupported. No secondary decoding occurs. Ordinary
ASCII produced by JSON decoding is evaluated normally. No finding means that no
supported address was detected; it does not establish that the text contains no
email address, personal information, or secret.

### Audit contents and failures

Decision events contain a server interaction ID, UTC timestamp, target ID derived
from the retained registration, policy digest, evaluated controls, explicit control enablement, action, finding
codes/counts, forwarding eligibility, and evaluation duration. They exclude
content, matched values, snippets, source spans, content hashes, and exception text.

Evaluation failure can produce a separate safe operational event when the sink
is available. It carries a fixed error code and no policy action or finding.
Unknown internal targets use the reserved server-owned `unresolved` identity and never expose
the supplied target string. If the sink is unavailable, the service still prevents dispatch. A target failure
leaves the earlier decision record intact; it does not turn that record into a
claim that execution succeeded.

## Relationship to the original product goals

The original goal is a provider-independent layer governing AI, agent, model,
MCP, and external API interactions. This change implements the first local
execution path toward that goal.

| Original goal | Current implementation |
| --- | --- |
| Central policy and explainable decisions | Strict startup configuration, structured findings and resolutions, and central ALLOW/REDACT/BLOCK decisions. Live policy reload is deferred. |
| Deterministic security controls and data handling | One bounded input email detector and central span redaction. General PII, secret detection, and output inspection are deferred. |
| Provider independence and integration boundaries | Immutable target registrations, exact retained dispatch bindings, a TargetAdapter contract, and local echo implementation. External provider, model, agent, and MCP integrations are deferred. |
| Auditability and telemetry | Safe decision/operational records and evaluation duration on stdout. Durable storage, completion records, and a dashboard are deferred. |
| Robust local verification | Deterministic unit tests, HTTP integration tests, injected targets/sinks, and independent correctness/security reviews. |
| Broader governance | Authentication, authorization, budgets, execution limits, semantic controls, prompt-injection controls, and model/tool/resource restrictions are deferred. |

The foundation and extension registrations demonstrate centralized enforcement
and safe dispatch locally.
It does not yet provide the complete security surface described in the product
roadmap.

## Recorded verification and usage

The foundation change's [worklog](worklog.md) records 133 passing unit tests,
40 passing integration tests, passing Ruff/Poetry/OpenSpec/whitespace checks,
a real Uvicorn HTTP smoke test, and fresh independent correctness and security
reviews returning `PASS`. These are the recorded implementation results;
this summary does not claim a new execution of those checks.

The extension-point change subsequently recorded 237 passing unit tests and
63 passing integration tests, compatibility checks and fresh independent
correctness/security PASS reviews. Its approved artifacts are in the
[extension-point archive](../openspec/changes/archive/2026-10-03-generalize-control-layer-extension-points/).
Fresh post-archive baseline verification is recorded separately in the worklog.

Installation, policy selection, request examples, and verification commands are
in the [README](../README.md). Current requirements are in
[OpenSpec specs](../openspec/specs/); the approved design and original deltas remain
in the [archived OpenSpec change](../openspec/changes/archive/2026-10-03-establish-control-layer-foundation/).
