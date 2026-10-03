# Proposal

## Why

The verified post-archive baseline supplies generic registered controls and central enforcement, but production security coverage is still limited to email. A coherent deterministic pack can now demonstrate credential protection, additional bounded sensitive-data protection, and known-attack mitigation without another core refactor or a commercial service.

## What Changes

- Add independent `bearer-credential`, `pem-private-key`, `github-token`, `us-ssn`, and `known-attack-signatures` controls; retain `email-address` unchanged.
- Detect complete Authorization bearer-header values, supported complete PEM private-key envelopes, classic `ghp_` and `gho_` token shapes, and explicitly labelled hyphenated US SSNs. These produce original-character spans and support central REDACT, ALLOW, or BLOCK.
- Add a bounded, versioned repository-owned JSON literal-signature catalog for selected pickle dangerous-global and Python code-execution indicators. Attack findings support ALLOW/BLOCK, never REDACT. Catalog loading occurs once at startup; no remote fetch or arbitrary regex execution.
- Enable the full pack in default production composition. Default policy REDACTs email/labelled SSN and BLOCKs credential and attack findings; each declared code remains independently configurable.
- **BREAKING configuration migration:** administrator-selected email-only policies need explicit entries for the new registrations before deployment, even if disabled. Preserve email-only policy/digest compatibility with an explicitly injected email-only registry; do not silently fill missing entries.
- Require adversarial detector tests and real multi-control policy, redaction, privacy, audited dispatch, concurrency, and HTTP composition tests.

Deliberately exclude unlabeled SSNs, broad PII, arbitrary secret heuristics, other provider formats, cryptographic credential validity checks, general prompt-injection detection, binary/model artifact scanning, and supply-chain provenance validation. No target changes or extension-contract redesign are proposed. Semantic controls, local models, budgets/accounting, model allowlists, reporting/database/dashboard, output inspection, authentication/authorization, policy reload, tool permissions, and remote feeds remain later work.

## Capabilities

### New Capabilities

- `credential-exposure-detection`: focused bearer, PEM and GitHub credential detectors with precise grammars and safe spans.
- `labelled-ssn-detection`: conservative US SSN syntax detection under an explicit label, without identity validation.
- `known-attack-signatures`: trusted startup literal catalog and non-redactable findings for curated dangerous interaction indicators.

### Modified Capabilities

- `interaction-gateway`: expanded default composition and explicit policy migration while preserving the public local-echo contract and existing email behavior.
- `policy-decisions`: production default pack mappings and real cross-control enforcement coverage; existing registry, validation, resolution and redaction contracts are consumed unchanged.
- `decision-audit`: production-pack privacy and audited dispatch coverage without extending event fields.

`email-address-detection` remains unchanged.

## Impact

Add flat detector/catalog modules and local unit/integration tests; modify `composition.py`, `config/policy.yaml`, and composition-sensitive test fixtures. Preserve core domain/registry/policy/service/API/audit/target behavior and the existing email module. No dependency or network requirement is added. After implementation and independent PASS review, update README, architecture, system summary, traceability and worklog to actual coverage.

Planning baseline: `4b45120`, containing archived `generalize-control-layer-extension-points` and verified post-archive repair. Planning lives on `change/add-deterministic-security-controls`. This proposal is not approval to apply. Challenge mapping, precise boundaries, ownership, file inventory and acceptance matrix are in design/specs/tasks.
