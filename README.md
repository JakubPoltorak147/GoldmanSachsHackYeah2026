# GoldmanSachsHackYeah2026

A local AI Control Layer foundation: strict startup policy, bounded ASCII
email/labelled-SSN and bounded credential/known-attack detection, central
ALLOW / REDACT / BLOCK decisions, and audited
forwarding to local echo or an operator-configured loopback Ollama text model. No external provider or paid API is needed.

## Install

Use Python 3.12+ and Poetry 2.x from the repository root:

```sh
poetry env use python3.12
poetry install
poetry check
```

Poetry runs in non-package mode. The lockfile includes only the approved runtime
and test tooling: FastAPI, Pydantic, PyYAML, Uvicorn, pytest, httpx and Ruff.

## Run and select policy

```sh
poetry run uvicorn app.control_layer.api:create_app --factory --no-access-log
```

The default startup policy is `config/policy.yaml`: all six deterministic controls enabled and semantic-security disabled,
email/labelled SSN mapped to `REDACT`, credentials and known attacks to `BLOCK`. Select an administrator-owned policy file with:

```sh
CONTROL_LAYER_POLICY=/absolute/path/policy.yaml poetry run uvicorn app.control_layer.api:create_app --factory --no-access-log
```

Policy edits require restart. Invalid/unreadable policy prevents startup. There is
no permissive fallback or request-selectable policy. The schema is:

The prepared interaction scenarios are an explicit opt-in demo surface. Start the
dashboard with semantic scenarios enabled:

```sh
CONTROL_LAYER_DEMO_ENABLED=true CONTROL_LAYER_DEMO_SEMANTIC_ENABLED=true poetry run uvicorn app.control_layer.api:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
```

The semantic flag requires the configured local evaluator to be available when a
semantic card is run. Omit that flag for deterministic-only scenarios. Without
the Demo flag the dashboard remains the read-only security overview, so no
scenario cards or run controls are exposed. These settings are read at startup;
restart the server after changing them.

```yaml
version: 1
policy_id: deterministic-security-default
controls:
  email-address:
    enabled: true
    findings:
      pii.email: REDACT
  bearer-credential:
    enabled: true
    findings:
      secret.bearer: BLOCK
  pem-private-key:
    enabled: true
    findings:
      secret.pem_private_key: BLOCK
  github-token:
    enabled: true
    findings:
      secret.github_pat: BLOCK
      secret.github_oauth: BLOCK
  us-ssn:
    enabled: true
    findings:
      pii.us_ssn: REDACT
  known-attack-signatures:
    enabled: true
    findings:
      attack.pickle_os_system: BLOCK
      attack.pickle_posix_system: BLOCK
      attack.python_os_system: BLOCK
      attack.python_exec_base64: BLOCK
```

Supported mappings are `ALLOW`, `REDACT`, `BLOCK`. Disabled controls are skipped;
any configured mapping is still validated. Audit events expose explicit enablement.

## Extension contracts and compatibility

`composition.py` explicitly registers the six deterministic controls, the semantic control and both local echo/local Ollama in production.
`ControlRegistry` holds ordered, frozen `ControlRegistration` objects pairing an
immutable `ControlDefinition` and its `FindingDefinition` catalogue with an
evaluator. Control IDs use `[a-z][a-z0-9_-]{0,63}` and globally unique finding
codes use `[a-z][a-z0-9_.-]{0,63}`. Registration copies input collections; evaluator
IDs cannot change the retained binding. Evaluators and adapters must support
concurrent calls or synchronize their own state.

`load_policy(path, registry)` returns a `BoundPolicy` retaining the exact
registrations. Every registered control needs an explicit boolean `enabled` entry.
Enabled controls need mappings for every declared code; disabled controls may omit
findings or map a subset. Adding a production registration therefore
requires updating every selected policy file before deployment, even when disabled.
Execution follows registration order, independently of YAML key order. The digest
identifies canonical policy configuration, not registry order or executable code.

Findings are validated against the actual invoked registration. A definition that
supports REDACT must require a valid original-text span under every policy action.
Spanless definitions can support ALLOW/BLOCK only. Redaction remains central span
replacement with `[REDACTED]`; controls supply no transformation callbacks.

`TargetRegistry` holds frozen `RegisteredTarget(TargetDefinition(id), adapter)`
bindings. Exact resolution invokes no adapter and has no URL interpretation or
fallback. The service retains one binding from before evaluation through audit
and dispatch; unknown internal targets fail with safe audit ID `unresolved`, which
cannot be registered. Registration does not grant public access: HTTP accepts
only `local-echo` and `local-ollama`.

Tests can pass `control_registry`, `target_registry`, `audit_sink`, `reporting_store` and `policy_path`
to `create_app`. Both defaults and injections use the same startup binder; invalid
injections fail without fallback. The internal service accepts a bound policy,
sink and target registry. Previous Python fixture constructors have changed; these
are internal contracts rather than a public SDK.

Response `finding_codes` is now a strict list of strings from validated findings,
preserving order and repeated codes. OpenAPI removes its former `pii.email` item
constant; the target selector now has a two-value enum. Generated clients may
require regeneration. Default values, all other
schemas, response envelopes and status mappings remain unchanged.
The deterministic pack expands default policy configuration and changes its digest;
the historical email-only digest remains supported with an explicit email-only
registry. The flat module layout is retained.

With the existing extension contracts, separate developers can own new control files and
new target files/tests in separate branches/worktrees. One integration owner must
serialize edits to production composition, policy configuration and shared core,
API, audit and current specs. Each dependent OpenSpec change records exact ownership
and dependencies.

## Try an interaction

```sh
curl -sS http://127.0.0.1:8000/v1/interactions \
  -H 'Content-Type: application/json' \
  -d '{"target_id":"local-echo","content":"Contact <alice@example.com>"}'
```

The target receives `Contact <[REDACTED]>` and the response contains its result,
server interaction ID, action, safe reason and finding codes. Input is preserved
exactly for ALLOW; REDACT replaces only selected original-text spans. BLOCK makes
zero target calls. HTTP statuses are 200 for forwarded decisions, 403 for policy
BLOCK, 422 for invalid requests, 503 for evaluation/audit failure, and 502 for target
failure. Operational errors carry no synthetic finding or policy BLOCK.

Requests require exactly `target_id` and `content`. Only `local-echo` and `local-ollama` are accepted.
Content must be 1–16,384 Python characters after JSON decoding, with no lone
surrogates. Identity fields, extras, coercible wrong types and malformed JSON are
rejected with fixed errors that do not reflect submitted values.

A separately provisioned local model can be selected with the same envelope:

```sh
curl -sS http://127.0.0.1:8000/v1/interactions \
  -H 'Content-Type: application/json' \
  -d '{"target_id":"local-ollama","content":"Describe a sunrise in one sentence."}'
```

Both targets remain registered with valid settings even when no runtime is running.
An eligible model call then fails with sanitized 502 after audit; echo still works.
The historical `EchoResult` OpenAPI name represents either content-only text result.

## Detector and audit limits

Email detection remains deliberately bounded ASCII detection. The additional
controls cover only the precise subsets below, not general PII/secret protection. Local parts are unquoted ASCII dot-atoms (1–64 characters); domains
have at least two DNS labels (1–63 each, total at most 253), with a final label of
2–63 ASCII letters. Labels cannot start/end with hyphens. Quoted local parts,
Unicode addresses, domain literals, `xn--` labels, encoded/obfuscated forms and
malformed candidates are unsupported. No secondary decoding occurs. Detection
uses Python string offsets and never normalizes text.

Decision audit events are complete JSON lines written and flushed to stdout before
eligible dispatch. They include safe identifiers, policy digest, control status,
action, finding counts, eligibility and duration. They exclude input content,
matched values, snippets, source spans, content hashes and exception text. A failed
or short write or flush failure permanently poisons the sink and stops dispatch.
Stdout events record eligibility; SQLite stores durable decisions and separate completion
records. See [reporting](docs/reporting.md). Exports and the dashboard are out
of scope. Run without access logs to avoid logging untrusted query strings.

## Verify

```sh
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest tests/unit
poetry run pytest tests/integration
openspec validate --all --strict
openspec validate --archived --strict
git diff --check
```

The suites use deterministic local inputs and injectable targets/sinks. No browser
suite, dashboard, authentication, policy reload,
response inspection, remote targets or additional infrastructure is implemented.

Project documents: [context](docs/project-context.md),
[implemented architecture](docs/architecture.md), [worklog](docs/worklog.md),
[agent instructions](AGENTS.md), and [OpenSpec](openspec/).
Product workflow: explore → propose → review → apply → independent review → archive.
Archive and push require separate user instructions.

## Known attack literal catalog

The repository-owned `config/attack-signatures.json` contains five exact indicators:
pickle protocol-0 os/posix system globals, both quote variants of Python
`__import__('os').system(`, and `exec(base64.b64decode(`. These reflect known unsafe
deserialization/code-execution patterns (see the Python pickle security warning
and the approved change's reference links). They are text indicators, not binary
artifact scanning or proof of malicious intent; quoted documentation also matches.
Spacing, aliases, CRLF substitutions, other dangerous globals and encoded forms
are unsupported. Never execute the examples to test detection.

The strict version-1 JSON file has `version`, `catalog_id`, and `signatures`; each
signature has `id`, `code`, and `literal`. Bounds are 64 KiB UTF-8, 1–32 entries,
and 8–256 Unicode scalar characters per literal. IDs/literals must be unique;
quote variants may share a code owned solely by the attack control. Unknown fields,
duplicate JSON keys, invalid metadata, nonstandard constants and malformed data
fail startup with sanitized errors. Matching is exact, case-sensitive and preserves
overlapping occurrences. It uses no regex rules, execution or network service.

The catalog is trusted administrator/deployment data, loaded once from a
module-resolved repository path and frozen until restart. User input cannot supply
signature IDs or finding definitions. Review catalog changes and update policy for
new codes together; missing mappings fail startup. An external manager can later
deliver a reviewed conforming local file, but remote fetch, polling and provenance
services are not implemented. The policy digest identifies policy configuration,
not catalog contents: record the deployed catalog revision separately.

## Policy migration and rollback

The expanded default registry requires explicit entries for all seven controls. Old
email-only policies fail startup; no implicit disabled entries or default actions
are added. To preserve an email-only deployment behavior, retain the email entry
and add `enabled: false` entries for each of the six additional controls. Supplied
mappings remain validated even when disabled, so attack REDACT is always invalid.
Policy and catalog edits take effect only after restart. Rollback requires the
baseline code **and** its matching baseline policy; an expanded policy is invalid
against the old registry. Historical policy/digest tests use an explicit email-only
registry, while the expanded default policy legitimately has a new digest.

## Deterministic detector boundaries

| Control / finding | Supported subset and default action |
| --- | --- |
| email-address / pii.email | Existing ASCII whole-candidate grammar remains unchanged; REDACT |
| bearer-credential / secret.bearer | Entire Authorization-shaped physical line, ASCII case-insensitive keywords, spaces after Bearer, token 1–4096 characters from ASCII alphanumeric or `._~+/-` followed only by `=` padding; BLOCK |
| pem-private-key / secret.pem_private_key | Exact whole-line five-hyphen BEGIN/END markers, matching PRIVATE KEY/RSA PRIVATE KEY/EC PRIVATE KEY/OPENSSH PRIVATE KEY/ENCRYPTED PRIVATE KEY; 1–64-character base64 body lines, canonical encoding, at least 32 decoded bytes; BLOCK |
| github-token / secret.github_pat, secret.github_oauth | Whole maximal Unicode alphanumeric/underscore/hyphen run, exactly case-sensitive ghp_ or gho_ plus 36 ASCII alphanumerics; BLOCK |
| us-ssn / pii.us_ssn | ASCII case-insensitive SSN or US SSN label with optional horizontal whitespace and colon, followed immediately by DDD-DD-DDDD; area 001–899 except 666, group 01–99, serial 0001–9999; REDACT |
| known-attack-signatures / four attack codes | Exact versioned local literals described above; BLOCK |

Bearer framing permits leading/trailing spaces/tabs and spaces/tabs around the
colon; only ASCII spaces separate Bearer from the token. LF/CRLF delimit physical
lines; a bare CR is invalid. Inline/quoted headers, standalone tokens, folded lines,
Proxy-Authorization and malformed/overlong candidates are unsupported.

PEM spans cover the complete envelope through END, excluding its following newline.
LF/CRLF, mixed line endings and END at EOF are supported. Recognized markers use
case-sensitive uppercase labels of 1–64 characters matching
`[A-Z][A-Z0-9]*(?: [A-Z0-9]+)*`. Only five approved labels start candidates;
any recognized END terminates a candidate, and nested BEGIN invalidates it.
Truncated, indented, metadata-header, public/certificate, binary/DER and malformed
blocks are unsupported. Base64 is validated only inside these framed envelopes;
there is no encoded-content secret discovery or cryptographic key validation.

GitHub punctuation/quotes/whitespace delimit candidates. Alphanumeric, underscore,
hyphen and Unicode-alphanumeric continuations reject the whole run. Other token
families, fine-grained PATs, old hex tokens and changed-length formats are excluded.
No provider authentication or checksum/entropy gate is used.

SSN labels cannot touch a preceding Unicode alphanumeric or underscore. Value runs
use Unicode alphanumeric/underscore/hyphen continuation checks; only complete ASCII
values match. Unlabelled/compact forms, Unicode digits, quotes or newlines before
the value, other national identifiers and issuance checks are unsupported.

Controls inspect unchanged original text and return only identifiers/spans. Central
policy alone decides ALLOW/REDACT/BLOCK. Credential/PII spans support all three;
attack findings require spans but support only ALLOW/BLOCK. An attack REDACT mapping
fails startup even when disabled. Overlapping bearer/GitHub evidence is intentional;
BLOCK still dominates and centrally selected overlapping redactions merge once.

All detectors report shapes/indicators: syntactically valid synthetic examples and
benign quoted attack examples can match. Unsupported/obfuscated/encoded variants
can escape. No Unicode normalization, reconstruction or general jailbreak/supply-chain
protection is claimed. No findings is not a certificate of safe content. Explicit
ALLOW may return original sensitive content from echo, but audit/errors never
include detected values, submitted content, signature literals, spans or raw exceptions.

## Local model adapter configuration

`ollama_target.py` implements the existing synchronous target contract using runtime
HTTPX 0.28, without an Ollama SDK. Settings are frozen until restart and are outside
security policy; the policy digest is unchanged.

| Environment variable (`CONTROL_LAYER_OLLAMA_` prefix) | Default | Accepted values |
| --- | --- | --- |
| `BASE_URL` | `http://127.0.0.1:11434` | HTTP literal `127.0.0.1` or `[::1]`, explicit port 1–65535, optional trailing slash only |
| `MODEL` | `qwen2.5:0.5b` | 1–128 ASCII characters, `[a-z0-9][a-z0-9._-]*:[a-z0-9][a-z0-9._-]*`, no `cloud` in tag |
| `CONNECT_TIMEOUT_SECONDS` | `2` | Finite decimal 0.1–10 |
| `RESPONSE_TIMEOUT_SECONDS` | `60` | Finite decimal 0.1–120 (read inactivity) |
| `MAX_RESPONSE_BYTES` | `65536` | Decimal integer 1024–1048576 |
| `MAX_OUTPUT_CHARACTERS` | `16384` | Decimal integer 1–65536 Unicode scalars |

Empty, malformed or out-of-range settings fail startup with fixed
`invalid_target_configuration`. URLs cannot contain credentials, hostnames, other
paths, whitespace, query or fragment. Explicit injected registries bypass this
loader. No startup network probe, model load, executable check or download occurs.

Each eligible invocation opens and closes its own client and response, sends one
`POST /api/generate` with only configured `model`, exact approved `prompt` and
`stream: false`, and returns only completed scalar text. Proxies, redirects and
retries are disabled. Raw identity-encoded bytes are bounded before strict JSON
parsing; oversize output is rejected rather than truncated. Runtime absence,
missing model, timeout, status and parsing failures become sanitized `target_failed`.

Connect/write/pool timeouts use the connection bound; read uses the inactivity
bound. These are I/O operation limits, not a wall-clock deadline. A peer delivering
chunks within each timeout may take longer. Client closure does not guarantee
runtime generation cancellation. Per-call buffers/clients support synchronous
thread-pool concurrency; model load, hardware and queueing determine latency, which
can occupy worker threads for seconds or timeout-scale durations.

Operators separately provision a trusted local Ollama daemon and model. Run the
daemon with `OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve` to disable
cloud features and bind loopback. Container deployments must publish on loopback;
remote/container hostnames are unsupported. This application cannot attest or
control separately administered daemon logging/retention. No installation or model
lifecycle automation is provided. Runtime templates/context limits may transform
or truncate inference internally; the submitted prompt field remains exact.

Generated output is untrusted and **not security-inspected**. It may repeat sensitive
input or contain unsafe text. Input approval does not certify output safety. One
fixed operator model is a deployment restriction; centralized model authorization,
budgets and output DLP remain deferred. Durable content-free
reporting is available through the typed in-process boundary. Audit evaluation
duration excludes generation time; eligibility audit does not claim execution success.

## Optional real Ollama smoke

Normal pytest discovery never runs real inference. Separately provision Ollama and
`qwen2.5:0.5b` before this check; the smoke never installs, downloads or pulls. With
an already provisioned daemon started locally using
`OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve`, explicitly run:

```sh
poetry run python scripts/smoke_local_model.py
```

The script uses the HTTP test-client boundary and an in-memory audit sink. It checks
completed model scalar text and pre-dispatch evidence, unchanged echo and blocked
zero-call dispatch. It prints only status/action/length, elapsed time and check
outcomes, without prompt/output text or exact-wording assertions. Missing runtime,
missing model, invalid configuration or failed verification yields fixed sanitized
nonzero failure. Record runtime version, configured model tag, hardware and observed
latency when executed; otherwise record NOT RUN with the missing prerequisite.
The optional run is outside the required verification gate. Deterministic tests of
script checks inject fake targets and require no real runtime.


## Durable reporting storage

Startup requires a private writable local SQLite file selected by
`CONTROL_LAYER_REPORTING_DB` (default `var/security-reporting.sqlite3`). Persistence
is required after JSONL flush and before target dispatch; unavailable storage fails
startup or closes the audit gate. Completion is recorded separately as succeeded,
failed or unknown; BLOCK and operational failures are not_invoked. Completion-write
failure preserves the target response and prevents later dispatch in that process.

The typed in-process listing/detail/summary API is ready for a later dashboard.
See [docs/reporting.md](docs/reporting.md) for schema, query examples, identity
provenance, timings, setup and backup requirements. No reporting HTTP routes, CLI,
exports, output inspection or token/cost telemetry are added. Automated tests need
no Ollama. Injected stores remain caller-owned and still use the validated gate.

### Local semantic input evaluation

The baseline `config/policy.yaml` explicitly disables `semantic-security`.
Select `CONTROL_LAYER_POLICY=config/policy-semantic-demo.yaml` to enable the
complete deterministic pack plus semantic classification at threshold 0.75.
Custom policies using the default registry must add an explicit semantic entry.
Enabled entries require a threshold and all three mappings:

```yaml
semantic-security:
  enabled: true
  threshold: 0.75
  findings:
    semantic.prompt_injection: BLOCK
    semantic.instruction_override: BLOCK
    semantic.exfiltration_intent: BLOCK
```

Change a mapping to ALLOW to observe a finding without blocking; semantic REDACT
is unsupported. A score greater than or equal to threshold emits that category's
fixed finding. Increasing threshold reduces sensitivity. Scores are independent
estimated risks, not calibrated probabilities. Deterministic controls all run
first, independently, on original input; semantic evaluation also sees original
input before central policy resolves BLOCK > REDACT > ALLOW and redacts spans.
An enabled evaluation failure produces `503 evaluation_failed` and zero target
calls, even after a deterministic BLOCK finding. A disabled control makes no calls.

The dedicated evaluator uses a preprovisioned trusted local model with Ollama
cloud disabled (`OLLAMA_NO_CLOUD=1`); it never installs, downloads or probes at
startup. Its frozen settings are independent of target-generation settings:

| `CONTROL_LAYER_SEMANTIC_` suffix | Default | Bounds |
| --- | --- | --- |
| BASE_URL | http://127.0.0.1:11434 | literal HTTP 127.0.0.1 or [::1], port 1–65535, optional trailing slash |
| MODEL | qwen2.5:3b | lowercase local name:tag, 1–128 characters, no cloud tag |
| CONNECT_TIMEOUT_SECONDS | 2 | 0.1–10, also write/pool |
| READ_TIMEOUT_SECONDS | 30 | 0.1–60, read inactivity |
| MAX_INPUT_CHARACTERS | 16384 | 1–16384 Unicode scalars |
| MAX_INPUT_BYTES | 65536 | 1–65536 UTF-8 bytes |
| MAX_RESPONSE_BYTES | 8192 | 1024–65536 entire HTTP body bytes |
| MAX_OUTPUT_CHARACTERS | 1024 | 128–4096 inner classifier JSON scalars |

Settings and policy changes require restart. Numeric environment settings use
unsigned decimal syntax. Invalid settings fail startup with
`invalid_semantic_configuration`. Smaller input caps reject accepted gateway
input operationally rather than truncating it. JSON escaping can expand submitted
text to six characters per scalar inside the prompt, then escape again inside the
HTTP request JSON; the submitted UTF-8 cap is not a serialized request-byte cap.

One non-streaming request uses fixed classifier instructions, JSON-encoded
untrusted input, a closed three-score schema, temperature 0 and num_predict 256.
No history, tools, memory, proxies, redirects, retries or fallback are used.
Prompt/data separation is defense in depth, not a proof against model steering.
Timeouts bound connection/read inactivity, not total wall time or daemon
cancellation; active trickle responses and runtime queueing can take longer.
The separately administered daemon/model are trusted and may handle content
outside the application's logging control. Model identity is an administrator tag,
not artifact attestation. Real classification can have false positives/negatives.
Target output remains uninspected.

For a demo, try ordinary questions, defensive quotations, indirect overrides
such as treating prior constraints as historical notes, and requests to reveal
protected instructions. The fake-runtime suite verifies boundary validation and
central enforcement; it does not establish actual learned-model accuracy:

```sh
poetry run pytest tests/unit/test_ollama_semantic.py tests/unit/test_semantic_control.py tests/integration/test_semantic_security.py
```

Semantic duration/model/status are content-free attempt evidence, separate from
target invocation and model identity; see `docs/reporting.md`.
