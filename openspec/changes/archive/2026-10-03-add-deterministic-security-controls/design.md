# Design

## Context

See proposal.md for motivation. The clean baseline at `4b45120` includes the
archived generic-extension change, 237 unit/63 integration tests and recorded
independent PASS reviews. Those results are historical evidence, not a new run.
Initial checkout was `main` at `97d2c15`; planning was moved to the available
post-archive branch, then isolated on `change/add-deterministic-security-controls`.

`ControlRegistry` already freezes ordered definitions/evaluators. `load_policy`
binds complete explicit entries; validation uses the actual invoked registration.
The service evaluates original content, central policy resolves actions/redacts,
and required audit succeeds before eligible dispatch. No contract redesign is needed.

## Goals / Non-Goals

**Goals:** useful bounded credential/data protection, independently configurable
findings, local historical-pattern mitigation, deterministic adversarial testing,
and deployment documentation that states exactly what is covered.

**Non-goals:** anything outside proposal.md; in particular no parser for arbitrary
Python, no execution/unpickling, no general PII classifier, no credential validity
service, and no claim that absence of findings proves safe content.

## Decisions

### 1. Independent controls and ownership

Use new flat modules. Keep `controls.py` and its email evaluator untouched; no
module-to-package migration. Credential controls have different syntax/security
meaning, so they remain separate. Related GitHub prefixes share one evaluator with
distinct codes. Do not use the old unused `PRODUCTION_CODES` as another registry.

| Control ID | Owned finding codes | span_required / supports_redaction | Default |
| --- | --- | --- | --- |
| `email-address` (existing) | `pii.email` | true / true | REDACT |
| `bearer-credential` | `secret.bearer` | true / true | BLOCK |
| `pem-private-key` | `secret.pem_private_key` | true / true | BLOCK |
| `github-token` | `secret.github_pat`, `secret.github_oauth` | true / true | BLOCK each |
| `us-ssn` | `pii.us_ssn` | true / true | REDACT |
| `known-attack-signatures` | `attack.pickle_os_system`, `attack.pickle_posix_system`, `attack.python_os_system`, `attack.python_exec_base64` | true / false | BLOCK each |

Controls only return `Finding` tuples with IDs/codes/spans, never values, excerpts,
actions or callbacks. Each code has exactly one registered owner. All supplied spans
are half-open Python-character offsets into untouched original content. Span-capable
credentials permit ALLOW/REDACT/BLOCK; signature codes permit ALLOW/BLOCK only.
Removing a signature substring does not establish the remaining program is safe,
so startup policy must reject signature REDACT even for disabled entries.

### 2. Exact candidate grammars

These are deliberately supported subsets, not universal format validators. No
normalization, secondary decoding, Unicode folding, token reconstruction, or secret
authentication occurs. ASCII case-insensitivity means ASCII letters only. JSON
decoding remains the gateway's existing behavior. Each evaluator emits all matching
occurrences in ascending `(start, end, code)` order; no cross-control suppression.

**Bearer:** split physical lines only at LF (strip CR only immediately before LF,
never a bare CR at EOF). A whole
line must be `[ \t]*Authorization[ \t]*:[ \t]*Bearer +TOKEN[ \t]*`, with the two
keywords ASCII case-insensitive and ` +` one or more ASCII spaces. TOKEN is
`[A-Za-z0-9._~+/-]+={0,}` of total length 1–4096. A bare CR, internal whitespace,
quotes, comma, extra field/text, interior `=`, missing token or overlong token rejects
the entire line. Span is TOKEN only, including any trailing `=`. Anchoring avoids
ordinary mentions of 'bearer' and shortened malformed token matches. This inspects
header-shaped text inside interaction content, not HTTP transport credentials.

**PEM:** boundaries are exactly `-----BEGIN LABEL-----` and `-----END LABEL-----`,
on whole physical lines without indentation/trailing
spaces; LF or CRLF is accepted (including mixed line endings). Labels are exactly
`PRIVATE KEY`, `RSA PRIVATE KEY`, `EC PRIVATE KEY`, `OPENSSH PRIVATE KEY`, or
`ENCRYPTED PRIVATE KEY`; labels must match. Body has one or more nonempty lines of
1–64 ASCII base64 characters, with `=` only at the end of the final body line.
Concatenate body lines; require canonical standard base64 (strict decoding and
re-encoding equality) yielding at least 32 bytes. No ASN.1, crypto or OpenSSH parsing.
Span includes BEGIN, intervening line breaks/body and END, excluding the line ending
after END. END may be at EOF. No blank body lines, metadata headers, nested BEGIN,
invalid alphabet/padding or mismatched labels. A candidate runs from a BEGIN to the
first subsequent END boundary of any label; an intervening BEGIN invalidates that
candidate (do not harvest the nested candidate), then scanning resumes after END.
A recognized framing marker uses five ASCII hyphens, uppercase BEGIN or END,
one ASCII space, a case-sensitive LABEL, and five closing ASCII hyphens. Framing
LABEL grammar is `[A-Z][A-Z0-9]*(?: [A-Z0-9]+)*`, length 1–64; this includes
unsupported labels such as PUBLIC KEY for candidate termination/nesting checks.
Only one of the five supported BEGIN labels starts a detection candidate. A malformed
marker (wrong dash count/case/label grammar) is ordinary body text and invalidates
base64 if inside a candidate; it does not terminate that candidate. Physical lines
split only at LF and strip CR only immediately before LF, never bare CR at EOF.
A truncated candidate runs to EOF and is unsupported. Separate later complete
blocks are evaluated independently. The existing 16,384-character request limit
bounds body work; no crypto dependency is introduced.

**GitHub:** scan maximal runs of Unicode alphanumeric characters plus `_` and `-`.
A run matches only if its whole text is `ghp_[A-Za-z0-9]{36}` or
`gho_[A-Za-z0-9]{36}`, case-sensitive. Span is the whole token. Quotes, whitespace,
commas, parentheses and periods delimit runs. Underscore/hyphen/Unicode alphanumeric
continuations, 35/37-character suffixes and prefixed identifiers reject the whole
run. No entropy or checksum gate: this reports a supported credential *shape*, not
whether GitHub issued it. Classic PAT and OAuth codes are independently mapped.
Other prefixes and lengths are deliberately unsupported; provider formats can
change and are not inferred from these two legacy shapes.

**US SSN:** require ASCII case-insensitive `SSN` or `US SSN` (one literal space),
preceded by start of text or a character other than Unicode alphanumeric/underscore.
Label is followed by `[ \t]*:[ \t]*` and a complete maximal candidate run of Unicode
alphanumeric characters plus `_` and `-`. Whole candidate must be ASCII
`DDD-DD-DDDD`; area 001–899 except 666, group 01–99, serial 0001–9999. Span is the
11-character number only; label/separators remain. Unlabelled/digit-only forms,
Unicode digits, quotes before the value, newlines between label/value, suffix continuations and impossible
groups are unsupported. There is no issuance/identity verification or geographical
inference. Explicit context reduces collision with order numbers and dates.

### 3. Examples and detection risks

All examples are synthetic. `A×36`/`A×37` denote generated fixture strings, not
literal text; PEM fixtures use generated canonical base64, not real key material.

| Finding | Positive | Near miss / malformed | Unsupported / FP / FN risk |
| --- | --- | --- | --- |
| `secret.bearer` | `Authorization: Bearer aB_9+/~.==` as entire line | `Bearer aB_9`, `Authorization: Bearer a=b`, quoted token, over 4096 | Inline JSON headers, standalone tokens, Proxy-Authorization, tabs after Bearer, folded lines; examples/placeholders can match; malformed/encoded values can escape |
| `secret.pem_private_key` | complete supported BEGIN/body/END with canonical base64 of 32+ bytes | mismatched label, invalid padding, 31 decoded bytes, nested/unfinished block | certificates/public keys, truncated keys, legacy encrypted metadata headers, DER/binary, indentation; fake but plausible envelopes match; excluded forms escape |
| `secret.github_pat` | `ghp_` + `A×36` in quotes | `ghp_` + `A×35`, `A×37`, Unicode/hyphen extension | changed-length PATs, fine-grained PATs, old hex tokens; synthetic shapes match; unsupported/encoded tokens escape |
| `secret.github_oauth` | `gho_` + `A×36` | uppercase prefix, 35/37 suffix, prefixed identifier | `ghu_`, `ghs_`, `ghr_`; same synthetic FP and changed-format FN risks |
| `pii.us_ssn` | `SSN: 123-45-6789`, `us ssn:\t321-54-6789` | `SSN: 000-45-6789`, `666-45-6789`, `900-45-6789`, group 00, serial 0000, extra digit | unlabelled/compact SSN, other national IDs; examples/fictitious labelled values match; missing context/obfuscation escapes |
| `attack.pickle_os_system` | literal `cos\nsystem\n` | `cos\nsystematic\n`, textual backslash-n | binary protocols, aliases, other dangerous globals; quoted documentation matches; variants escape |
| `attack.pickle_posix_system` | literal `cposix\nsystem\n` | `cposix\ngetcwd\n`, CRLF variant | same limits; do not claim all pickle payloads detected |
| `attack.python_os_system` | `__import__('os').system(` or double-quote variant | `__import__('os').getcwd(`, whitespace variant | aliases, comments/spacing, Unicode/encoded forms, other execution APIs; legitimate code/docs match |
| `attack.python_exec_base64` | `exec(base64.b64decode(` | `print(base64.b64decode(`, spacing variant | import aliases, `eval`, other encodings; legitimate samples match; no general malicious-code verdict |

Boundary tests must exercise start/end, every delimiter/continuation class, Unicode
before and touching candidates, embedded candidates, multiple occurrences and
malformed-neighbor recovery. False negatives are accepted documented subset limits,
not a reason to normalize user content or add broad heuristics silently.

Primary references supporting candidate selection: [RFC 6750 bearer syntax](https://www.rfc-editor.org/rfc/rfc6750#section-2.1),
[RFC 7468 textual envelopes](https://www.rfc-editor.org/rfc/rfc7468),
[GitHub token format design](https://github.blog/engineering/behind-githubs-new-authentication-token-formats/),
[SSA excluded groups](https://www.ssa.gov/employer/randomizationfaqs.html),
and [Python pickle warning](https://docs.python.org/3/library/pickle.html).
Our context/length/framing restrictions are design choices, not claims that those
references mandate this exact detector grammar. GitHub's
[2026 installation-token change](https://github.blog/changelog/2026-10-02-stateless-github-app-installation-tokens-rolled-out/)
reinforces explicitly excluding `ghs_` rather than guessing its grammar.

### 4. Small startup literal catalog

Choose `config/attack-signatures.json` over a code-only catalog: an operator can
replace trusted repository/deployment data and restart without editing policy core.
Choose exact literals over arbitrary regex/DSL matchers: bounded predictable cost
and clearly demonstrable coverage. No dynamic imports, URLs, fetching, polling,
background state, runtime reload or runtime network dependency.

Root has exactly `version` (integer 1), `catalog_id` (bounded registered-ID syntax),
and `signatures` (1–32 objects). File is at most 64 KiB UTF-8. Each object has exactly
`id`, `code`, `literal`; IDs/codes follow existing registry grammar; IDs are unique;
code begins `attack.`; literal is 8–256 Unicode scalar characters, nonempty,
containing no lone surrogates. Duplicate literals also reject startup. Reject
duplicate JSON keys, nonstandard NaN/Infinity, unknown fields, wrong types, unsafe
IDs, unsupported versions, unreadable/malformed/over-limit files. Failure raises
a fixed sanitized startup configuration error, with no raw catalog/content output
and no fallback, even if the attack control would be disabled.

Initial catalog ID `initial-known-attacks-v1` contains exactly:

| Signature ID | Finding code | Literal (JSON escape notation) |
| --- | --- | --- |
| `pickle-os-system` | `attack.pickle_os_system` | `cos\nsystem\n` |
| `pickle-posix-system` | `attack.pickle_posix_system` | `cposix\nsystem\n` |
| `python-os-system-single` | `attack.python_os_system` | `__import__('os').system(` |
| `python-os-system-double` | `attack.python_os_system` | `__import__("os").system(` |
| `python-exec-base64` | `attack.python_exec_base64` | `exec(base64.b64decode(` |

The two quote variants intentionally share `attack.python_os_system`.
Unique codes are deduplicated when constructing
the single control definition; IDs and literals remain unique. Every code has only
this one control owner. Emit one finding per distinct `(code,start,end)`; overlapping
occurrences are found by advancing search one character, not by match length. Sort
by `(start,end,code)`; matching is exact/case-sensitive anywhere, including examples
and quoted strings, without token boundaries or CRLF normalization. A catalog can
intentionally add overlapping literals; tests cover this with a trusted fixture.

Read at most 64 KiB plus one byte before parsing; reject oversize without first
allocating an unbounded file. Load the fixed repository-relative file using a module-resolved absolute path,
not request data or current working directory guessing. Freeze catalog entries
into tuples; derive FindingDefinitions before policy binding and reuse the same
evaluator snapshot for all requests. Inject test catalogs by calling the loader
with explicit local paths and constructing a registry; no new HTTP/environment
selector is needed. Later externally managed sources can deliver a reviewed local
file conforming to this format; authentication/provenance/remote transport would
require a separate change. File permissions/review are the trust boundary today.

The catalog is trusted security configuration, not user-provided data. User content
can trigger a declared literal but cannot create a signature ID/finding code.
Catalog edits adding codes require matching policy edits; missing mappings fail
closed. Signature IDs are not put into audit; trusted finding code/counts suffice.
The existing policy digest remains the digest of policy configuration only. It
does not identify catalog bytes/version; document and record deployed catalog
revision separately (no audit schema/hash extension in this change).

### 5. Production composition and policy interaction

Registration order: email, bearer, PEM, GitHub, SSN, known attacks. Every enabled
control sees original text; no early BLOCK shortcut or sequential redaction. Catalog
definitions are frozen first, then the existing loader binds policy. No target
change; only `local-echo` remains publicly accepted.

Upgrade default policy to explicit enabled entries with all ten codes mapped as
above (email + five new sensitive-data codes + four attack codes). Operators can
independently select ALLOW/REDACT/BLOCK where supported, or disable a control with
an explicit entry. Do not encode enforcement in evaluators/catalog entries.
BLOCK > REDACT > ALLOW irrespective of finding order; central redaction sorts and
merges original selected spans. A bearer token with `ghp_` syntax can produce two
overlapping findings: this is intentional independent evidence; ALLOW for one
cannot weaken BLOCK for the other. Under REDACT the shared secret is masked once.

All attack findings require spans for reliable evidence, but are non-redactable.
Unknown codes, wrong producer, malformed spans, control exceptions, policy failures
and audit failures retain existing fail-closed semantics. Audit contains registered
codes/counts/status only, no values, snippets, content, spans or exception text.
ALLOW intentionally permits the original value to reach echo; privacy assertions
here apply to audit/errors, not the intentional target output of an ALLOW decision.

### 6. Files, implementation ownership and concurrency

Primary agent is sole implementation/integration/verification/commit owner after
scope approval. Read-heavy reviewers may inspect separate areas; fresh reviewers
who did not implement perform correctness and security/bypass reviews. No parallel
code editing in this working tree. Different target work remains outside scope.

| Expected files | Planned responsibility |
| --- | --- |
| New `app/control_layer/bearer_control.py`, `pem_control.py`, `github_control.py`, `ssn_control.py` | focused stateless evaluators/constants |
| New `app/control_layer/attack_signatures.py` | frozen catalog, strict bounded loader, literal evaluator |
| New `config/attack-signatures.json` | reviewed five-entry initial catalog |
| Modify `app/control_layer/composition.py`, `config/policy.yaml` | registration and default mappings only |
| New `tests/unit/test_bearer.py`, `test_pem.py`, `test_github.py`, `test_ssn.py`, `test_attack_signatures.py`, `test_security_pack.py` | grammars, catalog validation and actual-control policy tests |
| New `tests/integration/test_security_pack_http.py` | complete startup/HTTP/dispatch/audit composition |
| Modify `tests/unit/test_registry.py`, `test_binding.py`, `tests/integration/test_extensions.py`, `test_api.py` and any existing composition-dependent fixtures | separate historical email-only fixture from upgraded default; preserve assertions |
| Modify README, `docs/architecture.md`, `docs/system-summary.md`, `docs/requirements/traceability.md`, `docs/worklog.md` after verified implementation | actual scope, migration, limitations, evidence |
| Change artifacts/deltas; `openspec/specs/` only during later authorized sync/archive | planning now, required behavior later |

Shared hotspots owned serially: composition, default policy/catalog, shared test
fixtures, README/architecture/summary/traceability/worklog and current specs.
Domain/registry/policy/service/API/audit/targets are shared contracts consumed
without behavioral edits. Do not modify AGENTS, dependencies, local development
configuration or baseline evidence. If a concrete requirement forces a core change,
stop that part and revise approved artifacts first.

All evaluators are stateless or hold frozen startup data; per-request match buffers
are local. Bound registrations are reused across FastAPI worker threads. Existing
audit lock remains the only shared request-path state. Tests must exercise parallel
requests, prove no cross-request findings/candidate state and retain complete
audit-before-dispatch records. Cost is bounded by content limit, catalog count and
literal lengths; no attacker-selected regex or pathological backtracking.

### 7. Acceptance test matrix and traceability

| Test area | Required cases | Layer |
| --- | --- | --- |
| Every new finding | positive, negative/near-miss, min/max, malformed, multiple, embedded, Unicode offsets, adjacent/overlap where applicable, unsupported/obfuscated forms | unit |
| Bearer | whole line vs inline, ASCII case, SP/TAB distinction, trailing padding, interior `=`, CRLF/LF/bare CR, 1/4096/4097 lengths, malformed line followed by valid line | unit |
| PEM | all labels, 31/32-byte boundary, canonical padding, wrapping, mismatched/nested/truncated markers, public/certificate/metadata exclusions, multiple blocks, mixed LF/CRLF, 16,384-char input | unit |
| GitHub | both prefixes, 35/36/37 suffixes, Unicode/hyphen/underscore touching, punctuation, malformed neighbor, repeated values | unit |
| SSN | both labels/case, all area/group/serial boundaries, missing/embedded label, Unicode digits, compact/unlabelled, same-line separators, suffix continuation | unit |
| Signatures/catalog | every literal/code, quoted match, LF vs CRLF/backslash-n, near misses, repetitions, trusted overlapping fixtures, duplicate/schema/type/version/size limits, collisions with other registrations, frozen snapshot after file mutation, sanitized failure | unit/startup integration |
| Cross-control findings | email+secret, SSN+secret, attack+email/secret, simultaneous all six controls, two overlapping bearer/GitHub findings | unit/integration |
| Policy/transform | no findings and findings→ALLOW; each redactable code under all three actions; attack ALLOW/BLOCK and invalid REDACT even disabled; explicit disable; missing entry/code; BLOCK beats REDACT; permutation invariance; selective original-offset redaction with Unicode, overlap/adjacency | unit |
| Failure/privacy | unknown/foreign codes, producer mismatch, invalid/absent spans under every action; real secret absence from ALLOW/REDACT/BLOCK and operational audit/errors; exceptions containing secrets sanitized; BLOCK/evaluation/audit failure zero target calls; audit failure during multi-control REDACT | unit/integration |
| HTTP composition | default registry/catalog/default policy through endpoint to spy/local echo; 200 ALLOW/REDACT, 403 BLOCK, 503 failure; audit before exactly-one eligible call; code order/multiplicity; public target restriction; concurrent requests | integration |
| Compatibility | unchanged email suite, explicit historical registry/digest and baseline wire fixtures, expanded-policy email-only and ordinary echo cases, unchanged full OpenAPI, startup migration rejection | unit/integration |

Regression-first tests are required for discovered vulnerabilities before fixes.
For adjacency impossible under a detector grammar, state why and cover generic
central merge using trusted fixture findings; do not invent supported syntax.
No Playwright: there is no dashboard journey. Normal suite is fully local and needs
no network, LLM, credentials or paid service. Examples must never execute payloads.

| Challenge requirement (docs/requirements/challenge-requirements.md) | Proposed evidence | Remaining limit |
| --- | --- | --- |
| Deterministic/non-AI controls | five independent new controls via existing registry, local grammar tests | hybrid semantic half deferred |
| PII and secret protection / input DLP | existing email + labelled SSN + bounded credential shapes, safe central spans | broad PII/credentials and output DLP deferred |
| Centralized Policy Engine / configurable enforcement | per-code mappings, enablement, strict startup, precedence, invalid REDACT rejection | reload/model restrictions/budgets deferred |
| Historical attack mitigation | versioned literal catalog, default BLOCK, zero target invocation for known indicators | text subset only; no binary/model/package provenance scan or remote intelligence |
| Positive and negative self-testing / exploit mitigation | full detector matrix and real end-to-end composition | budgets/semantic controls cannot be claimed |
| Sample configuration / auditability | expanded sample policy, safe finding counts/enablement | no reporting database, dashboard or usage metrics |

Coverage remains proposed; do not change the current traceability ledger until
implemented, verified and independently accepted.

## Risks / Trade-offs

- Syntactically valid examples trigger BLOCK/REDACT → document shape-based scope and per-code policy choices; do not hide findings via placeholder heuristics.
- Exact attack literals are easy to evade → list unsupported variations and test them; claim known-signature mitigation only, never general prompt-injection or executable-file protection.
- Valid secret variants can remain undetected → precise coverage documentation, test boundaries and future separately approved extensions.
- Trusted catalog edits can weaken protection or collide with codes → strict startup validation, reviewed local data, explicit policy mappings and immutable snapshots. Compromised administrator configuration is outside the untrusted-content boundary.
- Catalog and policy digest differ → document digest scope and deployment catalog revision; do not imply the digest identifies signatures.
- Default composition expansion breaks old policy startup → explicit migration and failing test; preserve historical compatibility through email-only injection.

## Migration Plan

After approval, implement modules/tests, then serialize default composition/config
integration. Update all deployed selected policies with explicit entries. Rehearse
invalid old-policy startup and valid disabled-entry migration before deployment.
Catalog loads before serving; policy remains restart-bound. Expanded default digest
changes legitimately; original email-only policy digest remains tested with its old
registry. Preserve email behavior, HTTP schema/statuses and local echo adapter.

Rollback is deployment of baseline code together with baseline policy; new policy
cannot be used with old registrations. Do not silently disable controls on startup
errors. Finish required verification, fresh correctness/security PASS reviews and
worklog evidence before declaring complete or creating the single task-group commit.
Archive and push require later authorization.

Verification commands after implementation:

```sh
poetry check
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest tests/unit
poetry run pytest tests/integration
openspec validate add-deterministic-security-controls --strict
openspec validate --all --strict
openspec validate --archived --strict
git diff --check
```

Proposal-time verification was strict OpenSpec validation and whitespace/scope
checks only. Subsequent explicit apply approval, implementation verification and
independent-review results are recorded in tasks.md, evidence/ and docs/worklog.md;
proposal verification alone did not authorize implementation.
