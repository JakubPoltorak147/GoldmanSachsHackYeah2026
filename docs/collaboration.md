# Collaboration and Parallel Development

## Purpose

This document defines coordination rules for parallel development by multiple
developers or coding agents.

It does not define product behavior and does not replace OpenSpec.

OpenSpec remains authoritative for planned product changes.

## Core rule

Parallel implementation is allowed only when ownership boundaries are clear.

Two developers must not independently modify the same security-critical contract
at the same time.

When two pieces of work require the same shared contract, either:

1. create and merge a prerequisite change that stabilizes the contract; or
2. serialize the conflicting part of the work under one owner.

## Branch and worktree isolation

Each active implementation change should use its own Git branch and preferably
its own Git worktree.

A developer or coding agent must not implement a feature in another developer's
working tree.

Recommended branch naming:

```text
change/<openspec-change-name>
```

Examples:

```text
change/generalize-control-layer-extension-points
change/add-deterministic-secret-controls
change/add-local-model-target
```

Each branch must remain associated with one clearly identified OpenSpec change.

## Change ownership

Every active OpenSpec change must have one implementation owner.

Before implementation begins, its design or tasks must identify:

- implementation owner;
- files or directories primarily owned by the change;
- shared contracts it depends on;
- shared files it expects to modify;
- changes that must merge before it;
- verification commands.

The owner is responsible for integration and verification of that change.

Another developer may review the work but must not independently implement a
competing version of the same behavior.

## Shared hotspots

The following files or areas should be treated as shared integration hotspots
unless a later architecture change moves their responsibilities elsewhere:

```text
app/control_layer/domain.py
app/control_layer/policy.py
app/control_layer/service.py
app/control_layer/api.py
app/control_layer/audit.py
config/policy.yaml
docs/architecture.md
AGENTS.md
openspec/specs/
```

Only one active implementation branch should own a behavioral modification to a
shared hotspot at a time.

A second branch may depend on the existing contract but should not silently
change it.

If parallel features both require a hotspot change, prefer a small prerequisite
OpenSpec change that introduces the necessary extension point first.

## Preferred ownership boundaries

After extension points have been introduced through an approved OpenSpec change,
prefer directory-level ownership.

A security-controls workstream may primarily own areas such as:

```text
app/control_layer/controls/
tests/unit/controls/
```

An integration workstream may primarily own areas such as:

```text
app/control_layer/targets/
tests/unit/targets/
tests/integration/targets/
```

An observability workstream may primarily own areas such as:

```text
app/control_layer/reporting/
app/dashboard/
tests/unit/reporting/
tests/integration/reporting/
```

These paths describe preferred future ownership boundaries only. They do not
authorize creating or restructuring them without an approved OpenSpec change.

## OpenSpec concurrency

Multiple OpenSpec changes may be active at the same time when they are genuinely
independent.

Parallel changes should not:

- redefine the same capability contract independently;
- edit the same delta spec in incompatible ways;
- rely on different assumptions about a shared interface;
- both own the same security-critical implementation file.

If one change depends on another, record the dependency explicitly and do not
apply the dependent implementation before the prerequisite contract is available.

Archiving changes that update overlapping current specs should be serialized.

## Integration rule

Shared-core integration should have one owner.

Feature branches should expose behavior through approved interfaces instead of
copying or bypassing central policy, audit, or dispatch logic.

A feature must not bypass:

- central policy resolution;
- audit-before-dispatch behavior;
- fail-closed operational handling;
- trusted finding validation.

## Merge sequence

Before integration, the feature owner should:

1. update the branch with the current integration baseline;
2. resolve conflicts without weakening the approved specification;
3. run the verification required by the OpenSpec change;
4. obtain the required independent reviews;
5. merge only passing work.

After merging a prerequisite or shared-core change, dependent branches should
update to that baseline before continuing implementation.

After two parallel changes have both been integrated, run the complete repository
verification suite to detect integration failures that neither feature branch
could observe independently.

## Codex and agent usage

Each coding-agent session performing implementation must receive:

- the OpenSpec change it is implementing;
- exact files or directories it may modify;
- exact files it must not modify;
- required verification commands;
- dependencies on other active changes.

Do not tell two coding agents to independently solve the same architectural
problem.

Prefer using additional agents for:

- exploration;
- threat modelling;
- adversarial test design;
- specification review;
- independent code review.

Read-heavy parallel work is safer than parallel editing of the security core.

## Conflict escalation

Stop parallel implementation when:

- both changes require a new meaning for the same domain object;
- both changes modify policy schema incompatibly;
- both changes require orchestration changes in the same request path;
- one change invalidates an assumption in the other change's approved design.

Resolve the shared design through OpenSpec before continuing implementation.

## Current assignments

Do not maintain current developer assignments in this document.

Current ownership, dependencies, and implementation scope belong in the active
OpenSpec change artifacts so that this document does not become a stale second
project plan.
