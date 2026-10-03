# Design

## Context

See [proposal.md](proposal.md) for motivation and scope. The synchronous foundation already has generic string IDs in `Interaction` and `Finding`, a `Control` protocol, central action/redaction rules, a target adapter protocol, and an explicit audit serializer. Coupling persists in the email-only policy loader, per-request control composition, fixed audit target, separately injected target adapter, and literal response finding code.

Current specs remain the baseline. The default control is `email-address`, its code is `pii.email`, and the only public/production target is `local-echo`. No detector grammar, text normalization, redaction marker, HTTP status, audit sink guarantee, or result envelope changes are needed.

## Goals / Non-Goals

**Goals:** Establish immutable registration and binding contracts that allow multiple local test controls/targets to traverse the same production validation and orchestration path. Keep provider implementations outside policy/security orchestration. Make trusted identities independent of evaluator assertions.

**Non-Goals:** The exclusions in the proposal apply. In particular, registration is not a plugin loading mechanism or target authorization model; redaction remains original-text span replacement. Async evaluation, execution-class scheduling, scores, thresholds, stateful budget lifecycle, richer target results, and generic transformations are deferred.

## Decisions

### 1. Immutable server-owned control metadata and registrations

Use the following conceptual contracts; exact module placement is an implementation detail:

- `FindingDefinition(code, span_required, supports_redaction)`.
- `ControlDefinition(id, findings)` containing an immutable tuple of definitions.
- `ControlRegistration(definition, evaluator)` binding metadata to one existing `Control` evaluator.
- `ControlRegistry(registrations)` providing immutable exact lookup and an ordered tuple of registrations.

Validate metadata when constructing the registry: strict strings and booleans, duplicate control IDs, duplicate/global-colliding finding codes, and inconsistent capabilities are rejected before serving. Each control declares at least one finding code. Control IDs use `[a-z][a-z0-9_-]{0,63}`; finding codes use `[a-z][a-z0-9_.-]{0,63}`. These bounded ASCII identifiers preserve current values and exclude the `:` rule-ID delimiter. Definitions contain no request values or arbitrary audit metadata.

Globally unique codes preserve current code-only HTTP lists and audit count keys. Pair-qualified codes would require a larger public migration. Immutable registration order defines execution order; YAML key order does not select it. No priority/phase configuration is added now. Future scheduling changes must preserve deterministic-before-semantic requirements through their own approved design.

Registry construction copies supplied collections into immutable storage. A retained evaluator can have internal state, but cannot mutate registered metadata or replace a plan entry by changing its own `id`. If an evaluator exposes the existing protocol ID, registration construction checks consistency; runtime producer authority is always the registration.

Alternative rejected: mutable global catalogues or inferring trusted metadata from evaluator output. They make configuration validation and runtime trust disagree.

### 2. Startup produces a bound policy/execution plan

The composition root first freezes the control registry, then loads and validates policy against it. The startup operation returns a `BoundPolicy` containing the immutable policy snapshot/digest and an ordered tuple of `ControlPlanEntry(registration, enabled, mappings)` entries. Each entry holds the exact registration object from the validated registry, including the evaluator binding. Disabled entries remain in the plan for audit status; enabled entries define the expected evaluated-control sequence.

The service receives this bound object, not a freely combinable policy and independent controls tuple. It never reconstructs or substitutes control composition per request. Central resolution consumes validated findings and the same bound mappings. If an entry or resolution is inconsistent at runtime, fail closed as `evaluation_failed`; never synthesize a finding or policy BLOCK.

The policy control keys must equal the registered control IDs. Every registration needs an explicit boolean enabled/disabled entry. Enabled entries map every declared code exactly once; disabled entries may omit `findings` or provide a subset of valid mappings, preserving current disabled-email policy behavior. Unknown controls/codes, duplicate YAML keys, extra fields, malformed syntax/types, invalid policy IDs/actions, and unsupported REDACT mappings fail startup with sanitized policy errors. Existing version-1 policy shape and canonical JSON digest algorithm remain; identical foundation policies keep their current digest. The digest identifies policy configuration, not implementation binaries or registry order.

Compatibility consequence: a future newly registered production control makes older policy files incomplete, even if its intended default is disabled. Deployment must add an explicit entry to every selected policy before enabling that registry. No production registration is added in this change, so the default and existing email-only files remain valid.

Alternative rejected: omitted entries meaning disabled or enabled implicitly, and separate registries for loading/evaluation. These hide deployment drift or permit startup validation against different producers.

### 3. Findings are validated with their actual producer binding

For each enabled plan entry, invoke its retained evaluator on the original interaction. Pass the resulting object and that entry's `ControlRegistration` to validation; do not use `finding.control_id` to look up or select a producer.

Keep the current exact tuple/Finding/string checks. A returned `control_id` is an untrusted consistency assertion: reject a mismatch with the actual registration. Check each code against that registration's definitions. After validation, derive canonical finding identity from the registration for downstream resolution/explanations; preserving the existing Finding shape is sufficient. Controls do not receive authority to select rules or actions.

Validate any supplied span as an exact `Span` with exact integer offsets (booleans rejected), satisfying `0 <= start < end <= len(original_content)`. Every span-required definition needs a span under every action. A REDACT-capable definition MUST also be span-required; reject contradictory metadata at startup. Consequently even ALLOW/BLOCK findings from a REDACT-capable code require a valid span. A non-redactable, span-optional definition can produce spanless ALLOW/BLOCK findings; policy cannot map it to REDACT.

Email declares `span_required=true` and `supports_redaction=true`. Its implementation and bounded grammar remain unchanged. Central redaction continues replacing selected original spans with `[REDACTED]`, merging overlaps/adjacency, preserving interaction ID and target, and never delegating transformation to controls.

Alternative rejected: accepting asserted producer IDs, silently correcting forged identities, or adding transformation callbacks. These weaken the trust boundary or expand this refactor into a new enforcement framework.

### 4. Exact target resolution and retained dispatch binding

Use `TargetDefinition(target_id)`, `RegisteredTarget(definition, adapter)`, and an immutable `TargetRegistry` implementing `TargetResolver.resolve(target_id)`. IDs use the same bounded syntax as control IDs. Reserve `unresolved` for operational audit; it cannot be registered as a target. Reject duplicate/invalid identities at construction. Keep `TargetAdapter.invoke(Interaction) -> TargetResult(content: str)`.

Resolve the interaction's exact symbolic ID once before control evaluation; retain the returned binding through evaluation, audit, and dispatch. Resolution performs lookup only, with no target invocation, network activity, fallback, URL interpretation, aliases, or discovery. After a successful eligible audit, invoke the adapter on that retained binding exactly once. Validate results as today. Target failure remains a sanitized target error after the decision record.

Unknown internal target IDs cause `evaluation_failed`, zero target calls, and safe operational information when possible. Audit uses the reserved `unresolved` token, never the unknown supplied ID. Public unsupported IDs remain rejected before service evaluation with 422 and no service audit.

Registration establishes available adapters, not permission to expose or access external destinations. New public targets or target authorization require a separate approved change.

Alternative rejected: a single injected target unrelated to ID, fallback to echo, or re-resolution after audit. These permit misrouting or mismatched audit identity.

### 5. Trustworthy audit assembly and preserved dispatch gate

Audit target identity comes from the retained registration; control statuses and evaluated IDs come from plan entries; codes/counts come only from validated findings. Operational events record only successfully completed/validated controls as evaluated, preserving the current convention. Failed evaluations are not security BLOCK decisions.

Keep existing field names, fixed error codes, safe serialization allowlist, complete-line concurrency locking, write/flush acceptance, and permanent sink poisoning. Do not serialize entire registrations, domain objects, arbitrary provider metadata, spans, content hashes, values, snippets, or exception text. Default events retain `local-echo`, email IDs/codes, and current semantics. Events describe forwarding eligibility, not target completion.

The security service contains no concrete local-echo selection/audit constant. Pure policy remains target-independent. The reserved unresolved token is safe operational metadata, not a dispatch destination.

### 6. Composition root, dependency injection, and HTTP compatibility

Keep one explicit composition root (a small dedicated module if useful) that registers only the existing email control and local echo, chooses the policy path, binds startup policy, and injects the sink/service. No hidden concrete defaults remain inside policy resolution or service evaluation. No dynamic imports from YAML or requests.

Tests supply explicit control/target registries and sinks through the same startup binding operation. Invalid injected metadata or incomplete test policy fails exactly as production does. A spy can bind to `local-echo`; additional local fake targets exercise the internal service only. Test fixtures may migrate internal Python constructors/factory injection parameters; these are not a promised public SDK. Preserve existing module import paths where practical.

The request DTO continues admitting only `local-echo`, even with additional test target registrations. Response `finding_codes` becomes a strict list of registered-code strings; values originate only from validated resolutions. Preserve finding order/multiplicity, reason codes, result content/envelope, omitted-null behavior, server IDs, exact scalar text, bounds, extra-field/type rejection, and 200/403/422/503/502 behavior.

The OpenAPI item schema loses the email-only enum; generated clients may need regeneration. This is justified because a second valid registered finding otherwise causes response validation failure. Default production values remain `pii.email` or an empty list. No other schema broadening or public target expansion is authorized.

Alternative rejected: expanding public target IDs to registry membership or using permissive test-only loaders. Both introduce behavior beyond architectural extension.

### 7. Small refactor and ownership

Prefer keeping `controls.py` and `targets.py` with small dedicated registry/composition modules. Converting them to packages is optional, justified only if it reduces integration complexity; it is not an acceptance criterion and must preserve imports/semantics if chosen.

Implementation owner: the primary agent/developer assigned to apply this change, with sole responsibility for shared-core edits, integration, verification, and the task-group commit. Use branch `change/generalize-control-layer-extension-points`, preferably a separate worktree. Prerequisite: the archived foundation/current specs; no other active change must merge first.

Owned scope: registration/binding additions in `app/control_layer/`, affected unit/integration tests, README compatibility guidance, `docs/architecture.md`, `docs/worklog.md`, and this change's task evidence. Shared hotspots are domain, policy, service, API, audit, default policy and current specs. Preserve default policy contents; do not edit AGENTS.md, collaboration/context/requirements documents, local environment configuration, dependencies, detector semantics, or unrelated user files. Current specs change only through the later authorized sync/archive workflow.

After this prerequisite merges, one developer can own new control implementation files/tests and another can own new target implementation files/tests using these contracts in separate worktrees. Package migration is unnecessary for file-level ownership. One integration owner serializes production registration, policy-file updates, shared-core/API/audit changes, and overlapping spec archives. Dependent changes record exact files and dependencies in their own artifacts and run the full suite after integration.

## Risks / Trade-offs

- [Validation weakened during generalization] -> Preserve exact-type and fail-closed checks; exercise forged producer IDs/codes and invalid spans across actions.
- [Registry and policy drift] -> Bind exact registrations at startup; require complete explicit control configuration; no per-request reconstruction or mutable rebinding.
- [Audit identity differs from invoked target] -> Retain one resolved binding and derive audit ID from it; test routing and audit together.
- [Sensitive strings enter generic identifiers] -> Bounded server-owned metadata, registration validation, and reserved unresolved token; never audit unresolved supplied IDs.
- [Policy rollout disruption when controls are added later] -> Document mandatory policy updates; keep current production registrations unchanged.
- [OpenAPI/client compatibility] -> Broaden only response finding codes and test the schema diff and existing wire outcomes.
- [Stateful extension thread safety] -> Registrations are immutable, not execution sandboxes. Evaluators/adapters must be safe for concurrent invocation or synchronize internally; stateful lifecycle designs remain future work.
- [Parallel edits collide despite registries] -> Merge this prerequisite first; assign concrete non-overlapping files and serialize shared composition/configuration changes.

## Migration Plan

1. After explicit apply approval, obtain and record a clean pre-change product baseline before any runtime edits. Preserve unrelated existing user documentation changes; isolate or stop on overlapping product edits rather than resetting them. Capture existing default policy digest and response/OpenAPI baseline.
2. Introduce metadata/registries and bind startup policy; adapt validation/central resolution to actual registrations without changing email evaluation logic.
3. Switch service to the bound plan and retained target binding, then wire composition and registry-based test injection.
4. Generalize response finding codes and add cross-control/target and compatibility regressions. Keep default policy and public target unchanged.
5. Update implemented architecture and compatibility documentation only after behavior is verified; obtain fresh independent correctness and security/bypass PASS, record worklog/task evidence, and create the single task-group commit.

Rollback is reverting the complete refactor commit and restoring the prior internal test fixtures. No data/schema migration, new policy format, external target deployment, or policy reload is involved. Archive and push require separate authorization.
