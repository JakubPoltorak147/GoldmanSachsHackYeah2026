# known-attack-signatures Specification

## Purpose

A small trusted startup catalog supplies deterministic known-dangerous text indicators for central mitigation, with explicit coverage limits and no general malicious-code or prompt-injection claim.

## Requirements

### Requirement: Trusted bounded startup catalog
Attack signatures SHALL load once from a trusted local versioned JSON catalog before policy binding. User interaction content MUST NOT supply catalog identities, metadata or definitions. Catalog loading MUST be bounded, strict and fail closed without fallback or raw configuration diagnostics. No remote fetching or runtime reload SHALL occur.

#### Scenario: Exact catalog shape
- **WHEN** a catalog has exactly version integer 1, a bounded machine `catalog_id`, and 1–32 signature objects with exactly `id`, `code`, and `literal`
- **THEN** valid startup freezes the catalog, registers its unique codes under `known-attack-signatures`, and reuses those bindings for requests

#### Scenario: Resource and metadata bounds
- **WHEN** the UTF-8 file is at most 64 KiB, IDs/codes satisfy existing registered metadata syntax, codes start with `attack.`, and literals have 8–256 Unicode scalar characters
- **THEN** those bounds permit catalog validation, subject to all other strict checks

#### Scenario: Invalid catalog
- **WHEN** loading encounters an unreadable/malformed/oversized file, duplicate JSON keys, NaN/Infinity, unknown fields, wrong types, unsupported version, invalid identifiers, duplicate IDs/literals, lone surrogates or out-of-range count/length
- **THEN** startup fails with a fixed sanitized configuration error even if policy would disable the control

#### Scenario: Quote variants sharing a code
- **WHEN** distinct valid signature IDs and literals intentionally share a code within the catalog
- **THEN** that code has one finding definition under the attack control and cannot collide with another control's code

#### Scenario: Snapshot and policy consistency
- **WHEN** the source file changes after startup or an updated catalog adds a code missing from enabled policy mappings
- **THEN** existing requests keep the frozen snapshot, while a new startup rejects the incomplete policy without implicit mapping defaults

### Requirement: Initial known-dangerous signature coverage
The initial catalog SHALL contain five exact case-sensitive literals with four owned codes: pickle os/posix system globals, single/double-quote Python os.system import calls, and Python exec/base64 decoding. These SHALL be identified as indicators, not proof of executable malicious behavior or coverage of all historical exploits.

#### Scenario: Pickle global indicators
- **WHEN** original text contains `cos\nsystem\n` or `cposix\nsystem\n` with actual LF characters
- **THEN** IDs `pickle-os-system`/`pickle-posix-system` produce respectively `attack.pickle_os_system`/`attack.pickle_posix_system`

#### Scenario: Python os execution indicators
- **WHEN** original text contains `__import__('os').system(` or `__import__("os").system(`
- **THEN** IDs `python-os-system-single`/`python-os-system-double` produce `attack.python_os_system`

#### Scenario: Encoded-code execution indicator
- **WHEN** original text contains `exec(base64.b64decode(`
- **THEN** ID `python-exec-base64` produces `attack.python_exec_base64`

#### Scenario: Exact matching limits
- **WHEN** text instead contains aliases, inserted whitespace/comments, Unicode lookalikes, CRLF instead of the literal LF, textual backslash-n, binary pickle protocols, other globals, encoded forms, supply-chain metadata or jailbreak instructions without a declared literal
- **THEN** the catalog does not claim those unsupported cases were detected

### Requirement: Literal findings and non-redactable capability
Every literal occurrence SHALL produce an original-content span with no copied content. Matching SHALL be exact anywhere, including quoted examples, preserve overlapping occurrences, deduplicate only identical code/start/end triples, and order findings by start/end/code. Attack definitions MUST require spans but declare REDACT unsupported; only central policy SHALL select ALLOW/BLOCK.

#### Scenario: Multiple and overlapping occurrences
- **WHEN** repeated initial literals or overlapping trusted catalog-fixture literals occur in an interaction
- **THEN** all distinct code/start/end occurrences are returned in stable order without match-length skipping

#### Scenario: Documentation matches
- **WHEN** a known literal appears in benign documentation or a quoted string
- **THEN** it still produces the declared indicator and policy determines whether to allow or block it

#### Scenario: Invalid redaction policy
- **WHEN** any attack-code mapping selects REDACT, even with the attack control disabled
- **THEN** existing startup policy validation rejects the unsupported action capability

#### Scenario: Matched content cannot mint codes
- **WHEN** user text includes fabricated signature IDs or finding codes
- **THEN** only actual declared literal matches can produce registered findings, and evaluator output with undeclared/foreign codes fails closed

### Requirement: Local historical-pattern verification
Tests MUST cover every initial literal/code, positive/negative/malformed cases, boundary/embedded/multiline behavior, repeated/overlapping matches, documented bypasses, strict catalog bounds, immutable snapshots and cross-control ownership collisions. Tests MUST NOT execute submitted code, unpickle payloads or require network/AI services.

#### Scenario: Mitigation demonstration
- **WHEN** an interaction containing a known attack literal and a redactable email is tested under default policy
- **THEN** central BLOCK overrides REDACT, a safe decision is audited, and zero target invocations occur

#### Scenario: Extensible local catalog
- **WHEN** a test substitutes a trusted conforming local catalog with a new literal/code and corresponding policy
- **THEN** matching and enforcement work without a policy-engine change, while incomplete or colliding metadata is rejected
