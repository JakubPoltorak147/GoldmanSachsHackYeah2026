# Interaction workspace

The local console at `/dashboard` supports prepared synthetic scenarios and a
single custom text interaction. Security overview remains read-only and works
with Demo disabled and no model runtime. The shared presentation uses a light
neutral console with top navigation, readable tables and labelled outcomes.

## Run locally

From the repository root, start the application with Demo and semantic scenarios
enabled:

```bash
CONTROL_LAYER_DEMO_ENABLED=true CONTROL_LAYER_DEMO_SEMANTIC_ENABLED=true poetry run uvicorn app.control_layer.api:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
```

Open `http://127.0.0.1:8000/dashboard` and select **Interactions**. Under the
baseline policy, choose **Local echo**, enter text and select **Run interaction**.
Echo returns only centrally approved input and needs no Ollama while semantic
inspection is disabled. `alex@example.invalid` is a safe synthetic email example
that demonstrates REDACT. The immediate echo result is labelled explicitly.

The default benign case is deliberately a drafting task: it asks the model for a
professional meeting-change email with a subject and body. The local model target
also supplies a fixed system instruction that treats requests as text/planning,
helps draft emails, and never claims to have sent, scheduled, delivered, or read an
email. The target cannot perform external actions, so the response should describe
what was drafted rather than inventing a delivery confirmation.

The flags `CONTROL_LAYER_DEMO_ENABLED` and
`CONTROL_LAYER_DEMO_SEMANTIC_ENABLED` accept exactly `true` or `false`; both
are false by default. Invalid values prevent startup. Omit the second flag for
deterministic-only scenarios. Both settings are read at startup, so restart the
server after changing them.

Generation and evaluation use the existing configured local runtimes; generation
defaults to `qwen2.5:0.5b` and semantic evaluation defaults to `qwen2.5:3b`.
The semantic model can be replaced with `CONTROL_LAYER_SEMANTIC_MODEL` when a
different supported local model is available.
`CONTROL_LAYER_OLLAMA_MODEL` and `CONTROL_LAYER_SEMANTIC_MODEL` select already
installed local models at startup. The application does not download models,
probe availability at startup, call a commercial service or offer runtime URLs
in the UI. Refer to README for trusted, cloud-disabled runtime preparation and
adapter transport limits.

## Application policy and scenario profiles

Custom input sends the ordinary `{target_id, content}` request to
`POST /v1/interactions`. The target selector exposes only registered
`local-echo` and `local-ollama` targets. Choosing Local model does not enable
semantic inspection. The composer displays the application's configured policy
digest and explicit enabled/disabled controls. To enable semantic inspection
for custom text, select `CONTROL_LAYER_POLICY=config/policy-semantic-demo.yaml`
at application startup; this also makes custom echo depend on the evaluator.

Prepared scenarios send only `{scenario_id}`. Payloads and profiles are fixed
on the server; the UI never loads hidden scenario payloads into the editor or
sets policy/model/endpoint/fault fields. The nineteen scenarios are:

| Scenario | Profile | Expected observation |
| --- | --- | --- |
| benign | deterministic-live | ALLOW and generation |
| email-pii | deterministic-live | REDACT and redacted-only forwarding |
| api-secret | deterministic-live | credential BLOCK |
| private-key | deterministic-live | synthetic key-envelope BLOCK |
| historical-signature | deterministic-live | known literal BLOCK |
| github-pat | deterministic-live | GitHub personal-token shape BLOCK |
| github-oauth | deterministic-live | GitHub OAuth-token shape BLOCK |
| labelled-ssn | deterministic-live | fictional labelled SSN REDACT; label retained |
| pickle-os | deterministic-live | inert OS serialization indicator BLOCK |
| pickle-posix | deterministic-live | inert POSIX serialization indicator BLOCK |
| encoded-exec | deterministic-live | inert encoded-execution indicator BLOCK |
| multiple-pii | deterministic-live | email and labelled SSN both REDACT |
| pii-and-secret | deterministic-live | email plus bearer credential; BLOCK wins over REDACT |
| prompt-injection | semantic-live | semantic prompt-injection BLOCK |
| indirect-override | semantic-live | semantic instruction-override BLOCK |
| exfiltration-intent | semantic-live | semantic exfiltration BLOCK |
| hybrid-controls | semantic-live | PII plus semantic finding, central BLOCK |
| evaluator-unavailable | semantic-unavailable | operational evaluation failure |
| generation-unavailable | target-unavailable | audited ALLOW followed by target failure |

Semantic cards are disabled unless semantic Demo is enabled. Live model findings
may disagree with expected codes/actions: the workspace reports the actual result
and an expectation mismatch. Expected labels never influence enforcement. The
last two cases are labelled **controlled unavailable-transport simulations**;
they inject a failure only into the selected existing adapter transport. They do
not claim the installed daemon is down. All profiles retain independent startup
bindings and share the required audit stream/store and poisoned write-gate health.

Every catalog entry includes a safe `expected_explanation` and
`runtime_requirements` purpose labels. Benign and redaction examples need
generation to complete. Semantic attack/hybrid examples need the evaluator;
generation can still be attempted if the actual classification permits it.
Expected deterministic BLOCK needs no model runtime because the target is never
called; this is an expectation, not a readiness check or alternate routing rule.
Both transport-fault simulations need no available runtime, although the
evaluator-failure card requires semantic Demo enabled.

These examples cover the ten existing deterministic finding codes. Token controls
recognize specific shapes without authenticating credentials; the SSN control
recognizes supported labelled fictional syntax without checking identity. Attack
signatures are exact inert text indicators, not general exploit or binary-model
scanning. Payloads are never executed, deserialized or exported. Budgets,
authorization, output DLP and policy reload are not implemented by these cards.

## HTTP and privacy contracts

`GET /v1/demo/workspace` returns a closed version-1 object with
`custom.policy_digest`, `custom.controls` (ID/enablement), and `custom.targets`
(public ID/model identity). `GET /v1/demo/scenarios` returns version-1 safe catalog
metadata, including code-owned expected explanations and runtime-purpose labels.
Neither route returns prompts, transformed text, output, raw policy,
paths, configuration URLs, evaluator scores or secrets. Neither makes runtime
calls or history writes. These are configured identities, not readiness checks.

Both GETs use `Cache-Control: no-store`. Demo disabled is fixed 404/not_found;
query parameters are fixed 422/invalid_request; unsupported methods are fixed
405/method_not_allowed; unavailable service is fixed 503/service_unavailable.
Trailing-slash routes return fixed 404 without query-reflecting redirects.

Scenario POST requires exactly one same-origin Origin. Ordinary POST may omit
Origin for CLI/API clients; if supplied, Origin must match application scheme,
host and effective port. Foreign, null, malformed and duplicate origins are
rejected before evaluation with sanitized 422 and zero calls. Keep the app on
loopback with proxy headers disabled; this check is not user authentication.

For example, an enabled local scenario can be run with:

```bash
curl -sS http://127.0.0.1:8000/v1/interactions -H 'Origin: http://127.0.0.1:8000' -H 'Content-Type: application/json' -d '{"scenario_id":"api-secret"}'
```

Custom text remains bounded to 1–16,384 Unicode scalar values. The UI counts code
points, preserves whitespace, and never trims/truncates input; strict server
validation remains authoritative. Accepted ALLOW/REDACT/BLOCK and failure status
codes retain existing meanings (200/200/403, validation 422, evaluation/audit 503,
target 502). BLOCK calls no generation target; evaluation failure has no policy
action or partial findings. Target failure preserves an earlier eligible decision
in reporting when available.

Drafts and immediate echo/model results remain only in the current interaction
view, render as plain text and never enter local/session storage, URLs, history,
metadata or application logs. New runs clear prior output; leaving Interactions
clears draft/output. Generated output is uninspected. There is no separate
forwarded-input preview or chat history.

One run lock covers custom and scenario actions, including leaving/reopening the
view while a POST is pending. No automatic POST retry occurs. Network interruption
means outcome unknown, not safe cancellation. Read inactivity limits do not promise
a total daemon execution deadline.

## Evidence and verification

Pipeline stages render only after the response from its UUID-correlated safe
reporting detail. Pending stages never pretend to be measured progress. Separate
evaluator/target identities, evaluation/semantic/invocation/total timing, disabled,
not-reached, failed, unknown and unavailable labels retain reporting meanings.
Missing reporting cannot erase an immediate result or trigger execution retry.
The matching audit-event button opens safe detail; the overview refreshes on return.

Before running a prepared case, read **What this tests**, the expected outcome
and **Before you run** prerequisites. Disabled cards can be selected to read
their explanation; Run remains disabled. Technical expectation details retain
profile and finding identifiers without displaying the hidden synthetic input.

After a run, **What happened**, **Why** and **What happens next** explain the
actual response and UUID-matched evidence. Readable names accompany the original
control/finding codes in the workspace, overview and audit detail. Unknown codes
remain visible with neutral labels; strings are rendered as text.

An allowed policy decision is separate from successful generation. Normal
ALLOW/REDACT scenarios only fully match when a successful immediate result and
durable target completion are present. BLOCK requires the expected findings and
recorded not-invoked status. Fault simulations require their expected failure
and corresponding recorded evaluation/target outcome. Missing detail or unknown
completion displays **Cannot verify full expectation**, even if the immediate
response contains generated text. Extra valid semantic categories are shown and
do not invalidate an otherwise satisfied expectation.

| Outcome | Meaning | Suggested next step |
| --- | --- | --- |
| ALLOW | Configured checks permitted forwarding, without guaranteeing safety | Read the labelled result and inspect the checks |
| REDACT | Policy removed detected values before eligible forwarding | Review echo or model result; no forwarded-text preview is reconstructed |
| BLOCK | Policy stopped the request; target was not invoked | Remove the described restricted material before a new explicit submission |
| evaluation_failed | A check could not finish; no decision or generation call | Operator checks configured evaluator/runtime; the code alone does not identify the cause |
| audit_failed | Required auditing failed; target was not invoked | Operator checks audit/reporting health |
| target_failed | Target execution failed after eligibility | Operator checks generation runtime/model; recorded action remains separate |
| invalid_request | Gateway rejected the request | Check input/workspace configuration |
| Disconnected or unknown completion | Immediate or historical outcome cannot be confirmed | Inspect available evidence; do not assume cancellation or retry |

Required tests use real controls and existing adapters with deterministic HTTP
doubles; no Ollama is required:

```bash
poetry run pytest tests/unit/test_demo_catalog.py tests/unit/test_demo_composition.py tests/integration/test_demo_api.py
poetry run pytest tests/unit tests/integration
poetry run pytest tests/browser --browser chromium
poetry run ruff check app tests
poetry run ruff format --check app tests
openspec validate add-demo-scenario-workbench --strict
```

For live acceptance, use preprovisioned models and rehearse all nineteen cases, custom
baseline echo without generation, custom model generation and separately enabled
application semantic policy. Record only case IDs, action/codes/status/model IDs
and measured timings, never input/output or raw classifier scores. A genuine
unavailable-runtime rehearsal can bind an independently verified unused loopback
runtime port at application startup rather than stopping another user's daemon.
This is distinct from the labelled injected transport cases. Required live
rehearsal is recorded PASS/FAIL/NOT RUN separately from the automated suite;
missing runtime or model prerequisites leave acceptance incomplete.

## Diagnose live prerequisites

Run administrator checks separately from the browser. This read-only check prints
only the configured evaluator identity and presence; it does not print runtime
responses, prompts, scores, or model output:

```bash
poetry run python - <<'PY'
import httpx
from app.control_layer.ollama_semantic import load_semantic_settings
settings = load_semantic_settings()
try:
    with httpx.Client(timeout=2, trust_env=False, follow_redirects=False) as client:
        response = client.get(settings.base_url.rstrip('/') + '/api/tags')
        response.raise_for_status()
        installed = {item['name'] for item in response.json()['models']}
    print({'purpose': 'semantic', 'model': settings.model,
           'status': 'present' if settings.model in installed else 'NOT RUN: absent'})
except Exception:
    print({'purpose': 'semantic', 'model': settings.model,
           'status': 'NOT RUN: metadata unavailable'})
PY
```

Generation and evaluation have separate bindings. Generation defaults to
`qwen2.5:0.5b`; evaluation defaults to `qwen2.5:3b` unless overridden. The semantic adapter uses
the local `CONTROL_LAYER_SEMANTIC_BASE_URL` (default
`http://127.0.0.1:11434`). Dashboard target selection cannot change these
bindings. The adapter limits are 2-second connect, 30-second read inactivity,
16,384 input characters / 65,536 UTF-8 bytes, an 8,192-byte response and 1,024
output characters. A completed response must contain exactly three finite numeric
scores in [0, 1]: `prompt_injection`, `instruction_override` and
`exfiltration_intent`. Missing/extra/duplicate fields, booleans, malformed JSON,
nonfinite or out-of-range scores fail closed. Never weaken this validation to make
a demonstration pass; the UI's `evaluation_failed` does not identify its cause.

Repeat the deterministic adapter checks with:

```bash
poetry run pytest tests/unit/test_ollama_semantic.py tests/unit/test_semantic_control.py
```

For a live rehearsal, run deterministic cases first, then the generation-dependent
benign/redaction cases, semantic attack/hybrid cases, and both labelled fault
simulations. Separately check baseline custom echo, custom generation, and custom
benign/attack input with the semantic application policy selected at startup.
For genuine unavailability, use a separate temporary application and an unused
loopback runtime port; never stop the operator's daemon. Record only case IDs,
actions/codes/statuses, model IDs, fixed stage labels and timings. Missing models
are `NOT RUN`, operational failures are `FAIL`, and classifier mismatches are
`FAIL`; do not retain raw envelopes, exceptions, input, output or scores.

The earlier 2026-10-04 rehearsal recorded only `qwen2.5:0.5b` installed while
the configured `qwen2.5:3b` evaluator was absent; the smaller model succeeded
for benign input but failed classifier score validation for the synthetic
prompt-injection case. With `qwen2.5:3b` provisioned, the bounded live smoke
now returns valid findings for benign, prompt-injection, instruction-override
and exfiltration cases. The strict parser remains fail-closed for malformed
model output.
