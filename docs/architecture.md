# Architecture

## Implemented decision core

The runtime is Python 3.12+ with Poetry in non-package mode. The implemented
modules under `app/control_layer/` provide a synchronous core and audited
execution service behind a strict FastAPI HTTP boundary.

- `domain.py`: frozen Interaction, Span, Finding, FindingResolution and Decision
  dataclasses, Action enum, Control protocol, and separate operational errors.
  Interaction IDs are server-generated UUIDs; content is preserved exactly.
- `controls.py`: bounded ASCII email-address detection with `email-address` /
  `pii.email` identifiers. It validates whole candidates and reports original
  Python character spans without copying matched content into findings.
- `policy.py`: strict YAML startup loader, immutable policy snapshot and policy
  digest, finding validation, central resolution and original-text redaction.
  Duplicate keys, unknown configuration and unsupported mappings are rejected.
  The default `config/policy.yaml` enables all six deterministic controls, REDACTs
  email/labelled SSN and BLOCKs supported credentials/attack indicators.

Central resolution uses BLOCK > REDACT > ALLOW; no findings yields ALLOW.
ALLOW preserves the original interaction. REDACT merges overlapping or adjacent
selected spans and constructs a new interaction from original slices with
`[REDACTED]` markers. BLOCK produces no forwarding interaction. Invalid findings,
spans or mappings raise an operational evaluation error, never a synthetic finding
or policy BLOCK. Default production composition registers the ten codes of the deterministic pack.

This is deliberately bounded ASCII email-address detection, not general email or
PII protection. Quoted local parts, Unicode addresses, domain literals, `xn--`
labels, encoded and obfuscated forms are unsupported. No secondary decoding occurs.

Fast deterministic tests live in `tests/unit/`. No external service is required.

## Audited execution path

`service.py` orchestrates a startup-bound policy plan retaining exact registrations.
Disabled controls are skipped. It validates control results, resolves policy,
constructs the forwarding interaction, and emits a decision event before dispatch.
ALLOW forwards the original object once, REDACT forwards the transformed object
once, and BLOCK makes zero calls. Operational evaluation or audit failure makes
zero calls and returns a fixed error code with no policy decision or synthetic
finding. Target failures after auditing return a separate sanitized target error.

`targets.py` defines TargetAdapter and TargetResult. LocalEchoTarget returns only
its received content. Immutable TargetDefinition/RegisteredTarget/TargetRegistry contracts bind exact
symbolic IDs to adapters. The service resolves once before evaluation, retains that
binding through audit and invokes it after successful eligible emission. Resolution
is lookup only. Unknown internal IDs use `unresolved` operational audit metadata
and perform no control evaluation or dispatch. The reserved ID cannot be registered.
Default composition registers `local-echo` and `local-ollama`; other injected
internal targets remain private.

`audit.py` defines the allowlisted AuditEvent and JsonLinesAuditSink. Events contain
server ID, UTC time, retained registered target, policy digest, evaluated controls, explicit control
enablement, action, trusted finding counts, forwarding eligibility and duration.
Operational events have a fixed error code and no action or findings. Neither event
contains content, matched values, source spans, content hashes or exception text.
A decision event records eligibility, without claiming target completion.

The sink serializes a complete JSON line, then writes and flushes under a lock.
Exceptions, short writes and flush failures poison the sink permanently; subsequent
requests cannot dispatch behind a damaged stream. The HTTP application composes this stdout sink with required SQLite persistence
for its lifespan; see durable reporting below.


## HTTP boundary and startup

`api.py` exposes `create_app` and POST `/v1/interactions`. Its lifespan loads the
administrator-selected `CONTROL_LAYER_POLICY` file (default `config/policy.yaml`)
before accepting requests and creates the service with a stdout sink and local
echo and local-model targets. Invalid startup policy raises sanitized PolicyError; no fallback exists.
Policy is fixed until restart. Test injection preserves the same startup loader.

Strict Pydantic request DTOs forbid extras, coercion, unsupported targets, empty
or over-16,384-character strings, and lone surrogates. JSON-decoded text reaches
Interaction.create unchanged with a new server UUID. Response DTOs expose only
safe codes and the eligible target result. Validation, body parsing and unexpected
errors have fixed sanitized handlers; exception/body details are never serialized.
The endpoint maps forwarding to 200, policy BLOCK to 403, invalid input to 422,
evaluation/audit failure to 503, and target failure to 502.

The synchronous endpoint runs through FastAPI's thread pool. A shared sink lock
keeps per-request records complete under concurrency without promising request
ordering. Uvicorn is documented with access logs disabled. There is no response
inspection, remote target, verified identity, reload, UI. SQLite reporting is described below.
Integration tests use httpx at the HTTP boundary; security logic remains covered
by deterministic unit tests. README contains installation, policy and run commands.

## Immutable extension metadata and startup binding

`registry.py` defines FindingDefinition(code, span_required, supports_redaction),
ControlDefinition(id, findings), ControlRegistration(definition, evaluator) and
ControlRegistry(registrations). Frozen tuples copy supplied collections. Control
IDs follow `[a-z][a-z0-9_-]{0,63}`; globally unique codes follow
`[a-z][a-z0-9_.-]{0,63}`. Strict types, duplicates, empty finding catalogues,
inconsistent evaluator ID assertions and REDACT capability without required spans
are rejected during registration. Target IDs use control-ID syntax.

`load_policy(path, registry)` validates all explicit control entries and returns
BoundPolicy(snapshot, entries). Each ControlPlanEntry retains the exact registration,
boolean enablement and immutable action mappings. All registered controls need a
policy entry; enabled controls map every code, disabled controls may omit findings
or map valid subsets. Unsupported REDACT is rejected even when disabled. Adding a
future production control requires updating every administrator-selected policy.
The existing version-1 format and canonical configuration digest remain unchanged.
Registry order determines evaluation order independently of YAML order; disabled
entries remain observable in audit. Concrete detector/echo selection exists only in
composition.py. Policy and orchestration have no concrete implementation defaults.

Validation uses the invoked producer registration, treats returned identity as an
untrusted consistency assertion, and reconstructs downstream identity from trusted
metadata. Every supplied span requires exact integer original-text bounds; booleans
are rejected. Required spans are enforced under every action. Non-redactable,
span-optional codes allow spanless ALLOW/BLOCK. Central span redaction is unchanged.

`create_app` accepts explicit control_registry/target_registry/sink injections
through the same startup binder as defaults. Response finding_codes contains strict
validated strings in evaluation order with multiplicity. OpenAPI differences from
the historical foundation are the former `pii.email` item constant removal and
the explicit local-echo/local-ollama target enum. Other schemas and public statuses
remain unchanged. Generated clients may need regeneration. The implementation keeps flat modules; no package migration is needed.

Registrations freeze metadata and bindings, not evaluator/adapter internal state;
extensions must be safe for concurrent invocation or synchronize internally. After
this prerequisite merges, new control and target files/tests can have distinct owners
in separate worktrees. Production composition, configuration and shared core/API/
audit/spec integration remain serialized under one integration owner, with concrete
ownership and dependencies recorded in each dependent OpenSpec change.


## Deterministic security pack

New flat bearer_control/pem_control/github_control/ssn_control modules implement
stateless bounded evaluators; controls.py and the email evaluator remain unchanged.
Composition explicitly registers email, bearer, PEM, GitHub, SSN and known attacks,
in that order. The pack leaves core domain, registry, policy, service and audit behavior
unchanged; the subsequent local-model integration changes only composition/API. All controls see original content before central redaction; no early
BLOCK shortcut suppresses other findings. Matching spans use Python characters.

attack_signatures.py reads at most 64 KiB plus one byte from the repository-owned
config/attack-signatures.json using a module-resolved absolute path. Its strict JSON
loader rejects duplicate keys, unknown fields, nonstandard constants, invalid
metadata/scalars and out-of-bounds inputs with sanitized PolicyError. Catalog ID and
1–32 signature entries become frozen dataclasses/tuples. Literals are 8–256 scalar
characters. IDs/literals are unique; related quote variants may share a code. Codes
are deduplicated into registered required-span, non-redactable definitions before
policy binding; cross-control code collisions remain invalid.

The frozen evaluator uses exact case-sensitive string search, retaining overlapping
occurrences and deduplicating only identical code/span triples. It executes no
regex rules, code, pickle or network request. Five repository literals cover four
pickle-global/Python-execution indicator codes. Coverage and false-positive/negative
limits are documented in README; this is not binary-model or general injection defense.

The startup-bound registry and immutable catalog are reused under concurrent calls;
match buffers are request-local. The audit lock and dispatch gate remain unchanged.
Only trusted finding codes/counts/status enter audit, never matched values, literals,
spans or catalog contents. Policy digest covers policy only, not the deployed
catalog revision. Catalog changes require reviewed local replacement, compatible
policy and restart; no remote updates/runtime reload exist.

Default registration expansion intentionally invalidates old email-only policies
unless every new control is explicitly configured (possibly disabled). Historical
email-only tests inject their original registry and preserve the original digest,
wire fixtures and email semantics. Expanded default composition preserves public
local echo, request bounds, status/response shapes and full OpenAPI. Rollback pairs
baseline code with baseline policy, never implicit control disabling.


## Local Ollama text boundary

`ollama_target.py` owns frozen validated settings and a synchronous TargetAdapter.
Default assembly loads six explicit environment settings without contacting a
runtime; invalid configuration raises fixed `invalid_target_configuration`. Explicit
injected registries bypass default settings. HTTPX 0.28 is a runtime dependency.
The literal HTTP loopback origin and single fixed model are server-owned, outside
policy; this change does not alter policy schema/digest or any deterministic control.

After successful eligibility audit, one per-invocation client POSTs exact approved
content to `/api/generate` with model and `stream: false`. Environment proxies,
redirects and retries are disabled. Raw identity-encoded bytes are capped before
strict UTF-8/JSON parsing. Completed scalar text alone becomes TargetResult;
metadata is ignored, overflow rejected and every failure sanitized as target_failed.
Response/client buffers are invocation-local, with resources closed on failures.

Connect/write/pool and read inactivity timeouts are explicit, with no total deadline
or guaranteed runtime cancellation. Synchronous thread-pool calls may queue/occupy
threads for hardware/load-dependent durations. Evaluation audit duration excludes
inference, and eligibility does not imply execution success. There is no output
inspection, centralized model authorization, budget
addition. Deployment trusts the separately administered loopback daemon, with
cloud disabled. No runtime/model installation, download or lifecycle handling exists.

Unit tests inject client doubles; integration uses a deterministic threaded loopback
runtime and real HTTPX plus the full gateway. The optional separately invoked smoke
is documented in README and is excluded from normal test discovery.


## Durable security reporting

`reporting.py` defines closed frozen reporting/query DTOs and startup-bound safe
projection. `reporting_store.py` implements version-2 SQLite audit/control/finding
and separate outcome tables, transactional appends, typed list/detail/summary and
the composed `PersistentAuditSink`. Projection validates digest, identities,
enablement, evaluated order, finding counts, mapped action and final precedence
against retained policy/target metadata. It accepts no request/output content.

The composed sink flushes stdout and commits SQLite before service dispatch.
Required failure poisons the shared gate; completion is appended after valid
result or target failure and leaves the original decision unchanged. Missing
completion derives unknown, while BLOCK and operational errors derive not_invoked.
Completion failure preserves target response, performs no retry and closes later
gates. Timing separates evaluation, invocation and total service-to-completion.
The service's low-level injectable audit protocol remains available for unit tests;
the default HTTP composition always requires persistent reporting.

`TargetDefinition.model_id` optionally records validated administrative identity;
default Ollama adapter and registration share one loaded immutable settings object.
Reporting does not inspect returned model metadata. History retains startup identity.
Application lifespan initializes/owns/closes default file storage; explicitly
injected stores remain caller-owned. WAL/FULL commits and a bounded busy timeout
support local durability. New storage uses private defaults; operators administer
existing directory permissions. Runtime history is not committed to Git.

The in-process typed boundary offers sequence pagination, UUID detail, time/action/
target/status filtering and distinct totals with basic action/target grouping.
Finding multiplicities and completed timing samples aggregate independently of
event totals. Reads use consistent transactions. No CLI, export or reporting HTTP
endpoint is implemented. Storage access requires trusted local filesystem access.
See `docs/reporting.md` for deployment, query contracts and limitations.

## Semantic input control

`ollama_semantic.py` owns the dedicated frozen, bounded local classifier settings
and request boundary, independent of `ollama_target.py`. `semantic_control.py`
validates even injected runtime scores against exactly three finite [0,1] numbers
and converts inclusive threshold hits into fixed spanless findings. It owns no
actions. The production registry includes semantic-security last, after all six
deterministic controls. Baseline disables it; the complete demo enables it.

Policy accepts threshold only for semantic-security and includes supplied,
normalized values in its digest. `bind_semantic_policy` in composition constructs
final immutable registrations with policy thresholds before serving, including
injections. Trusted ControlDefinition.model_id supplies evaluator identity;
runtime metadata cannot rename it. Startup performs no network calls. All controls
see original input; central policy and audit-gated target dispatch remain unchanged.
Enabled classifier failures yield operational evaluation_failed, with no partial
findings/action and zero target calls. Generated target output remains uninspected.

Service timing brackets semantic invocation through actual-producer validation,
including failure, with request-local monotonic timestamps. A closed optional
semantic duration/model/status observation is projected and committed with the
event, independently of invocation completion. Failed attempts contribute semantic
summary samples, never target timing. Missing attempts have no sample.

Reporting storage is version 2. Startup verifies exact v1 DDL before one atomic
additive migration; nullable semantic columns preserve IDs, sequences, findings,
controls and outcomes. Validation and version update occur before commit; failure
rolls back without evidence reset. Fresh stores have the same v2 DDL. Modified or
unknown schemas fail startup. Historical fields are null. Older binaries reject v2;
code rollback requires a backup or compatible binary. Disabling semantic policy
is the normal rollback. See README for evaluator bounds and trust limitations.
