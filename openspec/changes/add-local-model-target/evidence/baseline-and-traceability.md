# Baseline and challenge planning evidence

Explored 2026-10-03, planning only, baseline `136f483` (`chore: archive deterministic security controls`). Initial worktree was clean and `openspec list --json` reported no active changes. Planning branch: `change/add-local-model-target`. No baseline implementation verification is rerun or claimed here.

## Observed implementation boundaries

| Evidence | Finding and planning implication |
| --- | --- |
| app/control_layer/targets.py | Generic content-only result and immutable exact registration already exist; add a concrete flat module, no framework/generalization |
| app/control_layer/service.py | One retained lookup, original/central-redacted interaction, audit gate, single dispatch, sanitized target failure already exist; no orchestration change |
| app/control_layer/api.py | Literal local-echo selector and EchoResult component; widen explicit target enum only and retain compatible schema name |
| app/control_layer/composition.py | Explicit six-control/default echo registration; add only one target and leave control order/definitions unchanged |
| app/control_layer/policy.py and config/policy.yaml | Startup-bound central control mappings and redaction; runtime connection/model settings belong outside this policy; no digest migration |
| app/control_layer/audit.py | Allowlisted fields, locked sink and permanent poison on write failure; model integration consumes guarantees without adding content/result/model metadata |
| tests/unit/test_targets.py and test_security_pack.py | Current one-target assertions need deliberate update |
| tests/unit/test_routing.py and test_service.py | Existing retained-binding/unknown-target/closed-gate/concurrency regressions should remain |
| tests/integration/test_extensions.py | Keep private injected targets and historical wire fixtures; normalize only intentional new public target enum in whole-schema comparison |
| pyproject.toml | Python 3.12+, synchronous FastAPI, existing HTTPX dev dependency; promote to runtime rather than introduce SDK |
| README and docs/architecture.md | Existing lint/test commands, sync thread pool, no output stage; preserve verification conventions and document actual feature only after apply |

## Challenge mapping (proposed, not implemented coverage)

| Challenge area | What this feature can demonstrate after verified implementation | Limit |
| --- | --- | --- |
| Control-layer integration with AI systems | Govern actual local text generation via existing target registration | One text model target, no agents/tools/MCP |
| Practical deployment without subscriptions | Local Ollama, configured preprovisioned model, no cloud credentials | Operator provisions trusted runtime/model separately |
| Centralized security/privacy controls | Existing deterministic pack, central ALLOW/REDACT/BLOCK and required safe audit remain before actual model dispatch | Adds no new semantic or output controls |
| Executable self-tests | Deterministic real HTTP boundary and positive/negative/error/adversarial/concurrency cases | Real inference smoke optional, no budget/exploit-governance completion claim |
| Allowed LLM models | Single operator-configured model, no caller model field | Deployment bound only; centralized allowed-model governance remains future |
| Performance | Explicit operation timeouts and size bounds, sync concurrency documented | No benchmark/SLA, total deadline, accounting or compute/token budget |
| Security reporting/auditing | Retains existing safe pre-dispatch audit | No dashboard, historical storage, usage reporting or execution-completion record |
| Hybrid defense and output DLP | No new coverage | Semantic guardrails and output filtering remain future |

The external scope summary explicitly permits local Ollama and supplies no commercial subscription/hardware. This feature is integration evidence, not completion of the broader challenge. Main traceability/current specs/implemented architecture stay unchanged during this planning request.

## Reviewed external protocol facts

Primary documentation accessed 2026-10-03:

- [Ollama generate API](https://docs.ollama.com/api/generate): prompt/model generation boundary, stream selection and completed response fields.
- [Ollama errors](https://docs.ollama.com/api/errors): non-success statuses and potentially sensitive error body; do not expose runtime messages.
- [Ollama FAQ](https://docs.ollama.com/faq): loopback default and local-only cloud-disable configuration; separately administered runtime remains trusted.
- [Qwen2.5 0.5b model](https://ollama.com/library/qwen2.5:0.5b): small local smoke example; no model quality/security guarantee.
- [HTTPX timeouts](https://www.python-httpx.org/advanced/timeouts/): operation/inactivity bounds rather than total wall-clock execution.

All implementation work remains unchecked in tasks.md. No apply approval, implementation review, archive or push is authorized by this proposal request.
