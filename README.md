# GoldmanSachsHackYeah2026

A lightweight AI Control Layer intended to govern interactions between applications,
agents, MCP services, models, and external APIs through centralized policy and
explainable `ALLOW`, `REDACT`, and `BLOCK` decisions.

## Current status

This repository contains project documentation and the OpenSpec workflow setup.
No application code, product tests, capability specs, or active changes exist yet.
Python tooling, runtime, persistence, and deployment have not been selected.

## Project documents

- [Project context](docs/project-context.md): mission, goals, and conceptual direction.
- [Architecture](docs/architecture.md): architecture that actually exists.
- [Worklog](docs/worklog.md): completed work and verification.
- [Agent instructions](AGENTS.md): planning, implementation, review, and Git rules.
- [OpenSpec](openspec/): current capability specs and proposed or approved changes.

## Product workflow

`explore → propose → review → apply → independent review → archive`

Create or revise a change only on an explicit user request. Review and user approval
are required before apply. Task completion alone does not establish completion:
verification and independent review must pass before a change is completed or archived.
Generated OpenSpec skills are kept in `.agents/skills/`; project rules in `AGENTS.md`
take precedence over their generic completion and archive guidance.

## OpenSpec tooling

The bootstrap was verified with OpenSpec CLI **1.14.0** and the `spec-driven` schema.
To install that version in your development environment:

```sh
npm install --global @fission-ai/openspec@1.14.0
```

From the repository root, inspect the existing setup without creating a change:

```sh
openspec --version
openspec context --json
openspec list --json
openspec list --specs --json
openspec schemas --json
```

The CLI uses Node tooling; the repository does not contain a Node application.
Product installation and test commands will be introduced by an approved product change.
