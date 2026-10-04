# Design

## Context

See proposal.md for motivation. There are no active predecessor changes. Relevant current contracts are policy-decisions, interaction-gateway, local-model-target, decision-audit and security-reporting.

Observed extension points: `Control.evaluate(Interaction) -> tuple[Finding, ...]`, immutable ControlRegistration/FindingDefinition, startup BoundPolicy, actual-producer validation and spanless non-redactable findings already exist. `composition.py` orders six deterministic controls; `service.py` evaluates all enabled controls on original content before central resolution and audited dispatch. No early BLOCK shortcut exists. `ollama_target.py` already demonstrates loopback-only HTTPX, no proxies/redirects/retries, bounded bytes and sanitized errors. It is a target adapter, not an evaluator. Reporting uses a strict version-1 SQLite schema, content-free projection and independent invocation completion.

Exploration was limited to those contracts, their specs, startup/reporting integration points and directly relevant tests. No detector redesign or broad repository analysis is needed.

## Goals / Non-Goals

**Goals:** one focused local input classifier with deterministic verification; trusted score-to-finding conversion; independently configurable central enforcement; visible semantic latency; no content-bearing telemetry.

**Non-Goals:** all exclusions in proposal.md. In particular, no new Control/Finding protocol, score-bearing Finding, generic semantic plugin framework, generic control configuration system, target-adapter reuse for evaluation, policy reload or real-model accuracy benchmark.

## Decisions

### 1. One control and one dedicated evaluator boundary

Add flat `semantic_control.py` and `ollama_semantic.py`. The first implements the existing Control contract and depends on a small injectable semantic-runtime callable taking content and returning validated score data. The second owns Ollama-specific prompting, HTTP and response validation; it never invokes TargetAdapter/InteractionService. The control validates the complete returned score structure and numeric fields even for an injected runtime; the runtime adapter is not a bypass of score validation. A fake runtime/client can be injected without Ollama. No multi-provider abstraction or dynamic discovery is added.

Register `semantic-security` last with exactly these definitions, each `span_required=False`, `supports_redaction=False`:

| Closed classifier field | Server-owned finding code | Meaning |
| --- | --- | --- |
| `prompt_injection` | `semantic.prompt_injection` | Content attempts to redirect the recipient through embedded/untrusted instructions |
| `instruction_override` | `semantic.instruction_override` | Attempts to displace governing instructions, roles or constraints, including indirect phrasing |
| `exfiltration_intent` | `semantic.exfiltration_intent` | Suspicious intent to reveal/export protected instructions, secrets or private data in the same instruction attack context |

Exfiltration is intent classification, not generic DLP, destination authorization or secret discovery. Legitimate discussion, quotations and defensive analysis should receive low risk scores. The classifier does not execute supplied instructions. Categories may overlap; emit at most one finding per category in table order. Only code constants create Findings; never copy any returned identifier. Existing actual-producer validation runs again before policy.

Lifecycle: local startup validation only; startup freezes settings, prompt template, registration and policy threshold. Each evaluate call has request-local buffers, one per-call HTTP client and no retained prompt/response state. Close clients on every path; no daemon/model lifecycle, probes, downloads, retries or fallbacks. Shared instances must support concurrent calls without mutable last-result/last-duration fields.

Alternative: route evaluation through local-ollama target dispatch. Rejected because that path is governed by final policy/audit and returns text to the caller; evaluating inside it would occur too late and blur security versus target failures. Reuse transport concepts, not its target lifecycle; avoid refactoring that target for speculative reuse.

### 2. Deterministic controls remain independent and first

Proposed flow:

```text
validate request --> retain target binding
  --> all enabled deterministic controls on original content
  --> enabled semantic control on original content
  --> validate findings against each actual registration
  --> central policy: BLOCK > REDACT > ALLOW
  --> central span redaction when selected
  --> required safe JSON-lines + durable audit
  --> exactly one eligible target invocation
```

Do not add an early deterministic BLOCK shortcut in this change: stable evaluation/status contracts require all enabled controls and complete mixed-finding explanations. An enabled semantic failure returns existing operational evaluation_failed/503 even if deterministic findings had already been collected: zero dispatch, no synthetic finding, no policy action, no partial security finding report. Deterministic evaluations already ran; their logic and configuration are unchanged. Disabled semantic evaluation requires explicit policy configuration and makes zero evaluator calls.

Alternative: skip semantic work for deterministic BLOCK. Useful later but needs new skipped-status and decision completeness semantics; out of scope for implementation speed and contract stability.

### 3. Strict scores and threshold configuration

The sole classifier response is exactly one UTF-8 JSON object:

```json
{"prompt_injection": 0.02, "instruction_override": 0.01, "exfiltration_intent": 0.0}
```

Every field is mandatory; values are exact JSON numbers (not booleans/strings), finite and in [0,1]. Scores are independent estimated category likelihood/risk, not calibrated probabilities, confidence in an enforcement action or certainty of benignness. A category produces its fixed finding iff `score >= threshold`. There is no argmax, sum-to-one constraint or secondary benign label. A valid all-below-threshold response yields no semantic findings; no automatic action follows from model scores. No scores, rationale, spans or echoed text enter Findings, public responses or diagnostics.

Policy adds `threshold` only to the `semantic-security` entry. Enabled requires it; disabled may omit it, but supplied values are still validated. Accept finite exact int/float values with `0 < threshold <= 1`, rejecting bool/coercion. Recommended demo threshold is 0.75. Require all three enabled mappings; ALLOW/BLOCK supported, REDACT rejected even when disabled. Unknown threshold keys on other controls remain errors. The validated threshold is frozen in the policy snapshot and included in the canonical digest only when supplied; unchanged historical nonsemantic registries retain their digests. No per-category threshold or reload.

Keep generic runtime evaluate unchanged: extend policy snapshot/entry with a narrow optional semantic threshold and finalize the concrete semantic evaluator at startup in composition/bootstrap, never per request. A locally validated preliminary plan can supply the threshold; construct the final immutable registration/evaluator binding and final plan before serving, with identical definitions/mappings/digest. Provider-specific construction stays outside policy. Injected semantic compositions must use the same strict validation/final binding; injected nonsemantic registries need no changes. Do not mutate a shared evaluator's threshold or return a plan retaining an unconfigured enabled semantic evaluator.

Alternative: environmental threshold outside policy. Rejected because sensitivity changes should be attributable to the policy digest. A generalized evaluator-settings framework is unnecessary for one control.

### 4. Local runtime and bounded request/response

Use separate `CONTROL_LAYER_SEMANTIC_` settings, independent of target-generation settings. Proposed defaults and accepted bounds:

| Setting suffix | Default | Accepted values |
| --- | --- | --- |
| `BASE_URL` | `http://127.0.0.1:11434` | Same literal loopback HTTP origin grammar/port validation as current target; no hostnames, userinfo, extra path/query/fragment |
| `MODEL` | `qwen2.5:3b` | Same bounded local `name:tag` grammar as current target; reject cloud tags |
| `CONNECT_TIMEOUT_SECONDS` | 2 | finite 0.1–10 seconds; also write/pool bound |
| `READ_TIMEOUT_SECONDS` | 30 | finite 0.1–60 seconds of read inactivity |
| `MAX_INPUT_CHARACTERS` | 16384 | exact integer 1–16384 Unicode scalars |
| `MAX_INPUT_BYTES` | 65536 | exact integer 1–65536 UTF-8 bytes |
| `MAX_RESPONSE_BYTES` | 8192 | exact integer 1024–65536, entire HTTP body |
| `MAX_OUTPUT_CHARACTERS` | 1024 | exact integer 128–4096, inner classifier JSON string |

Validate exact types, finite numbers, decimal environment syntax and Unicode scalars. Check full input before making a call; reject oversize rather than truncate/chunk. Internal interactions get the same guards even if they bypass HTTP. Smaller operator limits deliberately fail evaluation for content accepted by the outer gateway. Fixed template plus bounded escaped input keeps generated request size bounded; document JSON escaping overhead separately from the submitted byte limit.

POST once to `/api/generate` with configured model, fixed system classifier instructions, JSON-encoded untrusted content in the prompt, `stream: false`, the exact score JSON schema as `format`, and fixed `options` with `temperature: 0`, `num_predict: 256`. Never include policy actions, IDs, tools, history, memory, RAG or caller-selected model/endpoint. The system instructions explain the categories and that submitted text is data, not governing instructions; escaping/separation is defense in depth, not proof against injection.

HTTPX uses `trust_env=False`, `follow_redirects=False`, zero retries and identity encoding. Incrementally read raw transport bytes solely to enforce caps; this is not model-token streaming. Reject non-200, non-identity encoding, invalid/overlimit Content-Length and actual overflow regardless of header. Require strict UTF-8 JSON, duplicate-key rejection, no nonstandard constants, exact `done: true`, no error field and scalar response string within cap. Runtime envelope metadata is ignored and never trusted; any optional model assertion cannot rename the evaluator. Parse the inner string separately with the closed three-field schema. Reject trailing prose, fences, additional JSON values, missing/extra fields, duplicate keys, unknown labels/IDs, action/policy fields, numeric strings, booleans, NaN/Infinity, out-of-range values or lone surrogates. Never repair, extract a JSON substring, clamp, coerce, or ask the model to retry.

Timeouts bound connection and read inactivity, not total wall-clock execution or daemon cancellation. Size and output token bounds limit work; document active trickle/queue latency as a limitation rather than add a cancellation framework. Absent runtime/model fails only enabled evaluation. A well-formed ambiguous classifier score is resolved exclusively by the documented threshold; ambiguous/unparseable response shape fails evaluation.

The separately administered daemon and preprovisioned local model are trusted deployment components; require Ollama cloud disabled. Trusted identity is the frozen administrator-selected model tag, not cryptographic artifact attestation. Model-response identity is never an authority. No cloud keys/services or automatic installation/download.

### 5. Failure and reporting without content

All evaluator timeout/status/protocol/size/schema/runtime exceptions become fixed evaluation_failed, with no raw causes. Startup settings failures use fixed invalid_semantic_configuration; invalid threshold/mapping uses invalid_policy. Never treat failure as benign, synthesize a semantic finding/BLOCK, fall back to deterministic-only mode, retry, or call a target. The only public service code remains evaluation_failed/503. Model output containing even a valid-looking action or forged code is rejected wholesale by the inner closed schema.

Measure semantic_duration_ms in the service around the registered semantic control invocation through actual-producer validation, using a monotonic clock and finally on failure. Include input validation, client setup, local inference, reads, parsing and threshold conversion; exclude deterministic controls, target inference and audit emission. Preserve existing evaluation_duration_ms (whole evaluation, including semantic attempt) and invocation_duration_ms (eligible target only). Measure no latency when disabled or failure precedes semantic attempt.

Add only a closed optional semantic observation to AuditEvent and durable ReportingEvent: `semantic_duration_ms`, `semantic_model_id`, `semantic_status` (`succeeded` or `failed`). All three are null/absent together if no attempt; attempted events have finite nonnegative duration <= evaluation_duration_ms and model ID from the startup registration's explicit optional model metadata, not evaluator attributes or output. Extend ControlDefinition with only optional trusted model_id using existing target model grammar, rather than a generic metadata bag. Service derives identity from the retained entry; projection validates observation against enabled semantic registration and success/operational evaluated-prefix contracts. Operational failed attempts do not add the semantic control to successfully evaluated_controls. No scores or failure details are stored. Target model_id remains separate and unchanged.

Persist this observation atomically with the required event and expose it in existing typed list/detail and a semantic TimingSummary in existing summary results. No new endpoint, export, dashboard or logging pipeline. Historical/no-attempt records supply no semantic timing samples; failed attempts do supply samples and retain operational, not BLOCK, status. Existing field selection, counts, audit gates, sink poisoning and independent completion evidence stay intact.

### 6. Demo and verification priorities

Baseline config explicitly disables semantic-security so echo/development and normal runtime-independent startup remain usable. Add `config/policy-semantic-demo.yaml` containing the entire deterministic pack unchanged plus enabled semantic mappings/threshold. Documentation demonstrates benign, indirect override and exfiltration intent, threshold sensitivity, ALLOW versus BLOCK mapping, fake-runtime tests and outage behavior. Same evaluator can serve echo or model targets; the selected target never chooses evaluator settings.

Required evidence is deterministic behavioral verification, not a claim that scripted fake scores prove actual model accuracy. Fake cases verify the plumbing and enforcement. Optional real smoke uses the preprovisioned configured model; record model/version, qualitative detections/false positives and timing without raw prompt/response logs or exact-wording assertions. Never require it for the normal suite. Clearly state residual semantic false positives/negatives and uninspected target output.

## Risks / Trade-offs

- Model can be steered into valid low scores → fixed classifier instructions, closed schema and deterministic controls provide layered defenses; no claim of comprehensive jailbreak resistance or calibrated accuracy.
- Enabled evaluator outage prevents even echo dispatch → explicit opt-in policy and operational 503, with no silent enforcement weakening.
- All enabled controls run even for a deterministic BLOCK → preserves complete evaluation contracts; bounded semantic requests and separate latency expose the cost.
- Local daemon may hold/log content outside application control → trusted operator deployment, cloud disabled and documented daemon administration; application never logs submitted/evaluator content.
- Larger local model may be slow or unavailable on demo hardware → configurable trusted local model and inactivity limits, no automatic model download; optional smoke measures actual performance.
- Safe telemetry addition requires storage evolution → exactly one additive verified migration, preserving all evidence; no general migration framework or retention/import work.

## Migration Plan

Implementation owner is the primary agent; no parallel implementation of policy/service/audit/reporting hotspots. Dependencies are the already implemented extension, deterministic, local-target and reporting contracts. No additional OpenSpec change is needed.

At apply: update default registry/policy together; explicitly migrate custom policies by adding semantic enablement and, when enabled, threshold/all mappings. Bootstrap without probes, then select demo policy only with a preprovisioned local runtime. Threshold/settings changes require restart.

New stores use schema version 2. For an existing store, recognize exact known version-1 DDL first; one atomic additive migration adds nullable semantic columns with closed checks, preserves all event IDs, sequences, controls/findings/outcomes and sets user_version=2 only on success. Validate resulting exact DDL. Historical observation fields are null. Unknown/modified schemas or migration failure fail startup safely with existing sanitized reporting errors and transactional rollback; never reset/delete data. Update EventView schema_version to 2. Code rollback requires a prior backup/schema-compatible binary; the older binary must reject v2 rather than rebuild it. Reverting semantic policy to explicitly disabled is the normal operational rollback and preserves deterministic enforcement.

## Approval and Completion Gates

No unresolved material design question requires user input. Defaults above are proposal choices, reviewable together with this scope. Planning authorization is the user's request to EXPLORE and create exactly add-semantic-security-control, explicitly saying not to implement. Apply requires a separate explicit approval recorded in tasks.md. Completion requires appropriate automated verification plus fresh independent correctness/specification and security/bypass reviews returning PASS, with worklog evidence referenced by tasks. No implementation or archive occurs during proposal creation.
