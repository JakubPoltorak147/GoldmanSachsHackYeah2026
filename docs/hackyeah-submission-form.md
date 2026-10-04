# HackYeah 2026 - submission form (copy-paste)

Every field below is a separate block. Copy the block content into the matching form field.

## Project Name

```
GoldenGateHolder
```

## Team lead

```
Jakub Półtorak
```

## Challenges

```
PARTNER TASK [Goldman Sachs]: AI control layer
```

## Idea stage

```
Work on progress project
```

## Problem

```
Companies are connecting LLMs, agents and MCP services to internal data faster than they can govern them. Every prompt can leak personal data or credentials, every untrusted input can carry a prompt-injection attack, and every uncapped call burns tokens and money.

- IBM's Cost of a Data Breach Report 2025: 13% of organisations reported a breach of their own AI models or applications, and 97% of those had no proper AI access controls. Unsanctioned "shadow AI" added about $670,000 to the average breach cost ($4.74M vs $4.07M).
- OWASP Top 10 for LLM Applications 2025 lists prompt injection (LLM01), sensitive information disclosure (LLM02) and unbounded consumption (LLM10) among the top risks.

Today these risks are handled separately inside each application or agent framework, so there is no single place to enforce policy, prove what was blocked, or cap usage.
```

## Solution

```
GoldenGateHolder is a lightweight, provider-independent AI control layer: a gateway that every request passes through before it reaches a model, agent or API.

- One central policy (YAML) decides the outcome of every interaction: ALLOW, REDACT or BLOCK. Each decision is explained by structured findings.
- Hybrid defence: cheap deterministic controls run first (PII, secrets such as bearer tokens, PEM keys and GitHub tokens, known attack signatures such as pickle/exec payloads). An optional semantic control backed by a local LLM catches prompt injection and exfiltration attempts that patterns miss.
- Every decision is audited into a content-free SQLite log before anything is dispatched. A live dashboard shows blocked threats, finding rankings, policy digest and measured latency.
- Runs fully locally (local echo target or local Ollama model). No cloud provider, API key or paid service is needed.
- Automated positive and negative tests cover each control, with allowed, blocked, boundary and bypass-attempt cases.

Benefit: security and compliance teams get one auditable enforcement point instead of ad-hoc checks in every AI application.
```

## What's done so far and goal of your project

```
Done before the event:
- HTTP gateway (POST /v1/interactions) with a central, strictly validated YAML policy and ALLOW / REDACT / BLOCK enforcement.
- Six deterministic controls: email, labelled US SSN, bearer credentials, PEM private keys, GitHub tokens, known attack signatures.
- Semantic security control (prompt injection / override / exfiltration) using a local Ollama model with a configurable threshold.
- Targets: local echo and local Ollama.
- Content-free audit trail (stdout JSONL + SQLite, written before dispatch) and security reporting.
- Interactive dashboard with a demo workbench (prepared scenarios and a free-text composer).
- Unit, integration and browser test suites.

Goal during the event: close the remaining challenge gaps. First priority is usage and budget governance (request and token limits over a time window, a usage endpoint and a dashboard panel, plus an evaluator script that tries to exceed the budgets). Then we want to explore output inspection (output DLP), authentication/authorization, and policy hot reload.
```

## Team status

```
Full team
```

## Current team size

```
4
```

## Needed skills (optional - team is full)

Tick if the form requires it: Cybersecurity, Backend Developer, AI & Data Science, QA & Testing.

## Skills comment

```
Team is complete. Areas we cover: backend (Python/FastAPI), cybersecurity and threat modelling, local LLM integration, QA with adversarial tests, and dashboard UX.
```

## Code Repository

```
https://github.com/JakubPoltorak147/GoldmanSachsHackYeah2026
```

## Website (https://...)

Optional. The repository link above can be reused:

```
https://github.com/JakubPoltorak147/GoldmanSachsHackYeah2026
```

## Instructions on how to open project

```
Requirements: Python 3.12+ and Poetry 2.x. Ollama is optional (only for the semantic control and the local-ollama target).

git clone https://github.com/JakubPoltorak147/GoldmanSachsHackYeah2026
cd GoldmanSachsHackYeah2026
poetry env use python3.12
poetry install

# PowerShell
$env:CONTROL_LAYER_DEMO_ENABLED = "true"
poetry run uvicorn app.control_layer.api:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers

Open http://127.0.0.1:8000/dashboard (Overview + Interactions with prepared scenarios).

Optional semantic control: ollama pull qwen2.5:3b, then start with CONTROL_LAYER_POLICY=config/policy-semantic-demo.yaml and CONTROL_LAYER_DEMO_SEMANTIC_ENABLED=true (see README section 4).

Tests: poetry run pytest tests/unit tests/integration
Juror walkthrough (15 min): docs/juror-evaluation.md
```

## Files and fields still to fill in by hand

- **Presentation (PDF/PPTX, max 10 MB):** `docs/presentation/ai-control-layer-presentation.pdf` (1.5 MB). Check it is the version you want to send.
- **Cover image:** not prepared yet.
- **Your video presentation (YouTube link):** not prepared yet.
- **Team name, Table number, Additional field:** not known, fill in manually.

## Sources for the statistics in "Problem"

- IBM Cost of a Data Breach Report 2025: https://www.techrepublic.com/article/news-ai-breach-risks-rise-as-governance-lags/
- Summary of the same report: https://www.bakerdonelson.com/ten-key-insights-from-ibms-cost-of-a-data-breach-report-2025
- OWASP Top 10 for LLM Applications 2025: https://coralogix.com/ai-blog/owasp-top-10-for-llm-applications/
