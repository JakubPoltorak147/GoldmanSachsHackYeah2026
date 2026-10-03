# Baseline relationship and approval — 2026-10-03

Before behavioral edits, inspected `git show`, tree differences, parent hashes,
branch state and the baseline worklog. `4584f2cf8bee75fd7b9d12a8bb3f1993c11aa26b`
and `4b451203a28d50f0c381185760f4674a4fa57c3a` both have parent
`6f167a3122044698fff8d6d9990b56501bed2c94`. They are replacement commits, not an
ancestor/descendant pair. The ancestor check correctly exits 1.

The complete tree delta is limited to AGENTS.md, docs/collaboration.md,
docs/project-context.md, docs/reference/ai-control-layer.pdf,
docs/requirements/challenge-requirements.md, docs/requirements/traceability.md
and additive historical/authorization entries in docs/worklog.md. Runtime,
configuration, tests, fixtures, current specs, archived change artifacts and
repair evidence are identical. The worklog follow-up records the user's
instructions “Ok add those untracked files to the commits” and “and not staged”,
authorizing the additional baseline scope in the same commit.

Therefore `4b45120` is the correct verified successor *snapshot*, an amended
replacement retaining the full `4584f2c` repair plus accepted governance/docs.
Reported this relationship to the user before behavioral edits. Dedicated branch
`change/add-deterministic-security-controls` has HEAD `4b45120`; initial status
contains only this requested untracked planning directory, no unrelated edits.

The user's current instruction explicitly grants APPLY APPROVAL for the approved
proposal/design/deltas/tasks subject to this resolved baseline gate. Approval is
recorded in tasks.md; all exclusions and no-archive/no-push instructions persist.
