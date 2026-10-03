## Project context

Before substantial exploration, planning, review or implementation, read:

1. `docs/project-context.md`;
2. the relevant current specs under `openspec/specs/`;
3. the active change under `openspec/changes/<change>/`, when one exists;
4. `docs/architecture.md` only for architecture that is already implemented.

Keep these responsibilities separate:

- `AGENTS.md` defines how work is done.
- `docs/project-context.md` defines what the product is and its long-lived goals.
- `openspec/specs/` defines current required behaviour.
- `openspec/changes/` contains proposed or approved changes in progress.
- `docs/architecture.md` describes architecture that actually exists.
- `docs/worklog.md` records completed work and verification.

Do not treat roadmap ideas or proposed designs as implemented behaviour.

## Planning authority

OpenSpec is the authoritative planning system for product changes.

Do not create a second execution plan that duplicates an OpenSpec change.

For product work use:

`explore → propose → review → apply → independent review → archive`

During exploration, no implementation is allowed.

Create or modify an OpenSpec change only when the user explicitly asks.

Before apply, resolve material decisions and assumptions in the change artifacts.
Review the proposal, specs, design, and tasks, then obtain explicit user approval
of that scope before implementation. Creating a proposal is not approval to apply.
Record the approval and its scope in the change's `tasks.md`, referencing the user
instruction that grants it.

Task completion, including an OpenSpec `all_done` state, does not mean a change
is complete. Required verification and fresh independent review must return `PASS`
before declaring a change complete or archiving it. Record the verification and
review evidence in `docs/worklog.md` and reference it from the change's `tasks.md`.
Do not archive incomplete or failing work.

These project gates take precedence over generated OpenSpec skills that suggest
archive after task completion or permit archive with incomplete-work warnings.
Keep generated skills unchanged; enforce project gates through these instructions.

During apply, follow `tasks.md`. Do not silently extend scope.

If implementation reveals that an approved design or requirement is wrong, stop that part of the implementation and update the OpenSpec artifacts before continuing.

## Delegation

The primary agent owns coordination, final decisions, integration, verification and commits.

Use subagents when independent work can improve coverage or keep noisy investigation out of the primary context.

Good delegation targets include:

- repository exploration;
- security research;
- threat modelling;
- specification review;
- test-gap analysis;
- adversarial test design;
- log or test failure analysis;
- independent code review.

Prefer read-heavy delegation.

Do not let multiple agents edit overlapping files in the same working tree.

For normal changes, the primary agent performs the implementation after exploration and design are settled.

A subagent that edits code must receive:

- exact files or directories it may modify;
- exact behaviour it is implementing;
- relevant OpenSpec artifacts;
- verification commands;
- an explicit list of files or areas it must not touch.

Subagents do not commit, change branches, archive OpenSpec changes, or modify user data.

## Independent review

Implementation and review are separate responsibilities.

After implementation and verification, delegate review to fresh agents that did not implement the change.

For security-relevant changes, perform at least:

- a specification and correctness review;
- a security / bypass review.

Reviewers may return `FAIL`.

A review must report concrete findings with file references and a reproducer or failing scenario where possible.

The primary agent fixes confirmed findings and requests a fresh review.

Do not mark a change complete until the final independent review returns `PASS`.

## Security project rules

Treat all input handled by the control layer as untrusted.

Never log raw secrets merely to make debugging easier.

Security controls return structured findings. Central policy owns enforcement decisions.

Keep provider-specific and protocol-specific behaviour outside the policy and control core.

Deterministic controls should run before expensive semantic controls unless an approved design documents a reason not to.

Core security behaviour must be testable without external commercial services.

Where practical, tests for controls and policy decisions must use deterministic local inputs.

Every `BLOCK` or `REDACT` decision must be explainable through structured findings.

Configuration changes that affect enforcement must have automated tests.

## Test layers

Use three layers of tests.

Fast tests validate:

- domain rules;
- controls;
- policy evaluation;
- decisions;
- redaction;
- authorization;
- budgets;
- audit event generation.

Integration tests validate boundaries such as:

- HTTP gateway behaviour;
- policy loading and reload;
- target adapters;
- local model integration;
- persistence.

Playwright tests validate only important dashboard and operator journeys.

Do not use browser tests to validate security logic that can be tested below the UI.

## Adversarial verification

For security controls, happy-path tests are insufficient.

For every new control, include:

- allowed cases;
- clearly blocked cases;
- boundary cases;
- reasonable bypass attempts.

When a vulnerability or bypass is discovered, first add a regression test that demonstrates it, then fix the implementation.

## Git execution

- After a task group is complete and all required verification passes, create exactly one commit for that task group.
- Use Conventional Commits in English.
- Do not commit partial or failing work.
- Never push unless the user explicitly asks.
- Never commit local development environment configuration that is excluded locally.
