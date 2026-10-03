# GoldmanSachsHackYeah2026

A local AI Control Layer foundation: strict startup policy, bounded ASCII
email-address detection, central ALLOW / REDACT / BLOCK decisions, and audited
forwarding to a fixed local echo target. No external provider or paid API is needed.

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

The default startup policy is `config/policy.yaml`: email control enabled,
`pii.email` mapped to `REDACT`. Select an administrator-owned policy file with:

```sh
CONTROL_LAYER_POLICY=/absolute/path/policy.yaml poetry run uvicorn app.control_layer.api:create_app --factory --no-access-log
```

Policy edits require restart. Invalid/unreadable policy prevents startup. There is
no permissive fallback or request-selectable policy. The schema is:

```yaml
version: 1
policy_id: foundation-default
controls:
  email-address:
    enabled: true
    findings:
      pii.email: REDACT
```

Supported mappings are `ALLOW`, `REDACT`, `BLOCK`. Disabled controls are skipped;
any configured mapping is still validated. Audit events expose explicit enablement.

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

Requests require exactly `target_id` and `content`. Only `local-echo` is accepted.
Content must be 1–16,384 Python characters after JSON decoding, with no lone
surrogates. Identity fields, extras, coercible wrong types and malformed JSON are
rejected with fixed errors that do not reflect submitted values.

## Detector and audit limits

This is deliberately bounded ASCII email-address detection, not general email or
PII protection. Local parts are unquoted ASCII dot-atoms (1–64 characters); domains
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
Events record eligibility; durable retention and target-completion records are out
of scope. Run without access logs to avoid logging untrusted query strings.

## Verify

```sh
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest tests/unit
poetry run pytest tests/integration
openspec validate establish-control-layer-foundation --strict
git diff --check
```

The suites use deterministic local inputs and injectable targets/sinks. No browser
suite, dashboard, authentication, policy reload, semantic control, database,
response inspection, remote targets or additional infrastructure is implemented.

Project documents: [context](docs/project-context.md),
[implemented architecture](docs/architecture.md), [worklog](docs/worklog.md),
[agent instructions](AGENTS.md), and [OpenSpec](openspec/).
Product workflow: explore → propose → review → apply → independent review → archive.
Archive and push require separate user instructions.
