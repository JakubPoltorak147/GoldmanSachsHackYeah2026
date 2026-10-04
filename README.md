# AI Control Layer

A local, provider-independent gateway that sits between callers and AI targets
(a local echo target or a local Ollama model). Every interaction is evaluated
against one central policy and receives an explainable decision —
`ALLOW`, `REDACT` or `BLOCK` — before it reaches the target. Every decision is
audited and stored in a content-free SQLite log that feeds a live dashboard.

No cloud provider, API key or paid service is needed.

```text
Caller ──► POST /v1/interactions
              │
              ▼
   Deterministic controls ──► Semantic control (local LLM, optional)
   email · SSN · bearer · PEM · GitHub token · known attacks
              │
              ▼
   Central policy (config/*.yaml)  →  ALLOW / REDACT / BLOCK
              │
              ├─► audit: stdout JSONL + SQLite (before any dispatch)
              ▼
   Target: local-echo  |  local-ollama  ──► response
```

| Challenge area | Status |
| --- | --- |
| Centralized policy (controls, thresholds, BLOCK vs REDACT) | Implemented, startup-loaded |
| Deterministic controls (PII, secrets, known attack literals) | Implemented, bounded subsets |
| Semantic control (prompt injection, override, exfiltration) | Implemented, local Ollama model |
| Dashboard, audit and reporting | Implemented |
| Automated positive/negative tests | Implemented |
| Budget governance (request-rate, estimated-token and per-request limits) | Implemented ([`add-usage-budget-governance`](openspec/changes/add-usage-budget-governance/)); input tokens only, no money/compute-time accounting; independent review still pending |
| Authentication/authorization, output DLP, policy hot reload | Not implemented |

Exact coverage and limits: [traceability](docs/requirements/traceability.md) and
[technical reference](docs/technical-reference.md).

---

## 1. Prerequisites

| Tool | Needed for | Notes |
| --- | --- | --- |
| Python 3.12+ and [Poetry 2.x](https://python-poetry.org/) | everything | |
| [Ollama](https://ollama.com/) | semantic control and the `local-ollama` target | optional; echo and all deterministic controls work without it |
| Node + `openspec` CLI | spec validation only | optional |

## 2. Install

```sh
poetry env use python3.12
poetry install
poetry check
```

Browser tests are optional: `poetry run playwright install chromium`.

## 3. Run the gateway (no model required)

**PowerShell**

```powershell
$env:CONTROL_LAYER_DEMO_ENABLED = "true"
poetry run uvicorn app.control_layer.api:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
```

**bash**

```sh
CONTROL_LAYER_DEMO_ENABLED=true poetry run uvicorn app.control_layer.api:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
```

Open <http://127.0.0.1:8000/dashboard>. **Overview** shows decisions, blocked
threats, finding rankings and measured latency; **Interactions** has prepared
scenario cards and a free-text composer. Keep the server on loopback: it is a
local console, not an authenticated service.

Try it from a terminal (the echo target returns what the policy approved):

```sh
curl -sS http://127.0.0.1:8000/v1/interactions -H "Content-Type: application/json" \
  -d '{"target_id":"local-echo","content":"Contact <alice@example.com>"}'
```

`Contact <[REDACTED]>` comes back with `"action":"REDACT"`. A blocked request
returns HTTP 403 and the target is never called. Status codes: 200 forwarded,
403 BLOCK, 422 invalid request, 503 evaluation/audit failure, 502 target failure.

## 4. Connect a local model (Ollama)

The gateway never downloads models and never calls a cloud service. You
provision Ollama yourself, bound to loopback with cloud features disabled.

1. Install Ollama and pull the two default models:

   ```sh
   ollama pull qwen2.5:0.5b   # generation target  (local-ollama)
   ollama pull qwen2.5:3b     # semantic security evaluator
   ```

2. Start the daemon on loopback with cloud disabled.

   **PowerShell**

   ```powershell
   $env:OLLAMA_NO_CLOUD = "1"; $env:OLLAMA_HOST = "127.0.0.1:11434"; ollama serve
   ```

   **bash**

   ```sh
   OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve
   ```

3. Start the gateway with the semantic policy and semantic demo cards enabled
   (PowerShell shown; use `VAR=value` prefixes in bash):

   ```powershell
   $env:CONTROL_LAYER_POLICY = "config/policy-semantic-demo.yaml"
   $env:CONTROL_LAYER_DEMO_ENABLED = "true"
   $env:CONTROL_LAYER_DEMO_SEMANTIC_ENABLED = "true"
   poetry run uvicorn app.control_layer.api:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
   ```

4. Use the model through the same envelope:

   ```sh
   curl -sS http://127.0.0.1:8000/v1/interactions -H "Content-Type: application/json" \
     -d '{"target_id":"local-ollama","content":"Draft a two-line meeting reschedule email."}'
   ```

Different models (any already pulled, lowercase `name:tag`, no `cloud` tag):

| Variable | Default | Purpose |
| --- | --- | --- |
| `CONTROL_LAYER_OLLAMA_MODEL` | `qwen2.5:0.5b` | generation target |
| `CONTROL_LAYER_SEMANTIC_MODEL` | `qwen2.5:3b` | semantic evaluator |
| `CONTROL_LAYER_OLLAMA_BASE_URL` / `CONTROL_LAYER_SEMANTIC_BASE_URL` | `http://127.0.0.1:11434` | loopback only |
| `CONTROL_LAYER_REPORTING_DB` | `var/security-reporting.sqlite3` | audit store |

All settings (timeouts, byte and character caps) and their bounds are in the
[technical reference](docs/technical-reference.md#local-model-adapter-configuration).
Invalid settings fail startup with a fixed error; there is no silent fallback.
Model output is **not** security-inspected, and semantic scores are estimates
from a small local model (false positives and negatives happen).

Optional real-model smoke check: `poetry run python scripts/smoke_local_model.py`.

## 5. Policy and configuration

| File | Use |
| --- | --- |
| `config/policy.yaml` | default: six deterministic controls on, semantic off |
| `config/policy-semantic-demo.yaml` | everything on, semantic threshold `0.75` |
| `config/attack-signatures.json` | trusted catalog of known-attack literals |

Select a file with `CONTROL_LAYER_POLICY=/path/policy.yaml`. Policy is
validated at startup — unknown keys, missing mappings, duplicate keys or an
unreadable file stop the server; there is no permissive fallback. Edit a
mapping (`REDACT` ↔ `BLOCK` ↔ `ALLOW`), flip `enabled`, or change
`threshold`, then restart; the policy digest in the dashboard and audit log
changes with it.

```yaml
controls:
  email-address:
    enabled: true
    findings: { pii.email: REDACT }
  semantic-security:
    enabled: true
    threshold: 0.75          # higher = fewer findings
    findings:
      semantic.prompt_injection: BLOCK
```

### Usage budgets

The `usage-budget` control enforces, per fixed window and process-wide, a request
count, estimated tokens (`ceil(characters / 4)`) and a per-request token cap.
Limits live in each policy under `controls.usage-budget.limits`; breaches emit
`budget.request_limit`, `budget.token_limit`, `budget.request_size` (map to `BLOCK`,
or `ALLOW` for observe-only). Defaults are generous (120 requests / 60,000 tokens /
4,096 per request per minute). `GET /v1/usage` and the dashboard's **Usage and
budget** panel show consumption; counters reset on restart.

Try it without any model: start the gateway with the small-limit profile and run
the evaluator, which exits non-zero on any mismatch.

```powershell
$env:CONTROL_LAYER_POLICY = "config/policy-evaluation-offline.yaml"   # bash: export ...
poetry run uvicorn app.control_layer.api:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers
# in a second terminal, against a freshly started gateway:
poetry run python scripts/evaluate_gateway.py
```

`config/policy-evaluation.yaml` is the same profile with the semantic control on.

## 6. Verify

```sh
poetry run pytest tests/unit tests/integration       # fast, deterministic, no model needed
poetry run pytest tests/browser --browser chromium   # dashboard journeys
poetry run ruff check .
poetry run ruff format --check .
openspec validate --all --strict
```

Unit tests cover each control with allowed, blocked, boundary and bypass-attempt
cases plus policy, redaction and audit privacy; integration tests cover the HTTP
gateway, local-model adapter (fake runtime) and reporting.

## 7. Evaluating this project (jurors)

See **[docs/juror-evaluation.md](docs/juror-evaluation.md)**: a 15-minute manual
walkthrough with exact commands, an adversarial attempt list, a scoring rubric
aligned with the challenge weights, and a copy-paste prompt for evaluating the
repository privately with your own local or hosted assistant. To experiment
on your own, use **[docs/juror-prompts.md](docs/juror-prompts.md)**: ready prompts per
control (allowed, redacted, blocked, bypass attempts, semantic) and ten policy
experiments (change a mapping, threshold or `enabled`, restart, compare).

## Documentation map

- [Technical reference](docs/technical-reference.md) — detector grammars, adapter settings, limits
- [Architecture](docs/architecture.md) and [system summary](docs/system-summary.md)
- [Demo workbench](docs/demo.md) and [reporting](docs/reporting.md)
- [Challenge requirements](docs/requirements/challenge-requirements.md) and [traceability](docs/requirements/traceability.md)
- [Worklog](docs/worklog.md) — verification and review evidence
- [Project context](docs/project-context.md), [agent rules](AGENTS.md), [OpenSpec](openspec/)

## Honest limits

Detectors recognise precise shapes (see the reference); obfuscated, encoded or
unsupported variants can pass, and "no findings" is not proof of safety. Budgets
cover request counts and estimated input tokens only. Authentication/authorization,
output DLP and hot policy reload are not part of the current build.
