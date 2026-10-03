# Credential Exposure Detection Delta

## Purpose

Independent deterministic credential controls identify precisely bounded supported secret shapes and original-content spans without owning enforcement or disclosing detected values.

## ADDED Requirements

### Requirement: Independent credential findings
Credential detection SHALL use independent `bearer-credential`, `pem-private-key`, and `github-token` controls owning respectively `secret.bearer`, `secret.pem_private_key`, and `secret.github_pat`/`secret.github_oauth`. Each finding MUST require an original-character span and support central ALLOW, REDACT, or BLOCK. Findings MUST contain no matched value or enforcement decision.

#### Scenario: Independent policy ownership
- **WHEN** the three controls find supported credentials in the same interaction
- **THEN** each returns only its own declared codes and exact source spans, and central policy independently resolves each code

#### Scenario: Repeated credentials
- **WHEN** supported credentials occur multiple times
- **THEN** each occurrence produces a finding in ascending start/end/code order without copying values

### Requirement: Whole-line bearer grammar
The bearer control SHALL match whole Authorization header-shaped lines using ASCII case-insensitive keywords. TOKEN SHALL contain one or more ASCII letters/digits or `._~+/-`, followed only by optional `=` padding, with total length 1–4096. Matching MUST NOT inspect transport headers or shorten malformed candidates.

#### Scenario: Exact supported framing
- **WHEN** a physical line is `[ \t]*Authorization[ \t]*:[ \t]*Bearer +TOKEN[ \t]*`, where ` +` means one or more ASCII spaces
- **THEN** the control emits `secret.bearer` spanning only TOKEN, including trailing padding

#### Scenario: Physical line boundaries
- **WHEN** supported lines use LF, CRLF, or end of content with no final newline
- **THEN** each matches independently, preserving original offsets and excluding CRLF from the token span; a bare CR at EOF remains invalid

#### Scenario: Boundary token lengths
- **WHEN** tokens have length 1, 4096, or 4097
- **THEN** the first two supported whole lines match and the third produces no shortened finding

#### Scenario: Malformed or unsupported framing
- **WHEN** content has a standalone Bearer value, inline header within other text/JSON, Proxy-Authorization, a tab instead of spaces after Bearer, empty token, quotes, internal whitespace or `=`, bare CR, comma or trailing non-whitespace text
- **THEN** that line produces no bearer finding while separate supported lines remain detectable

### Requirement: Complete bounded PEM envelopes
The PEM control SHALL detect complete unindented private-key envelopes with matching labels and canonical standard-base64 bodies decoding to at least 32 bytes. The span MUST include BEGIN through END and exclude the newline after END. Detection MUST NOT execute, cryptographically validate, or deserialize the decoded bytes.

#### Scenario: Supported envelope labels
- **WHEN** whole-line boundaries are exactly `-----BEGIN LABEL-----` and `-----END LABEL-----`, using matching PRIVATE KEY, RSA PRIVATE KEY, EC PRIVATE KEY, OPENSSH PRIVATE KEY, or ENCRYPTED PRIVATE KEY labels
- **THEN** a supported body produces one `secret.pem_private_key` finding for the full envelope

#### Scenario: Exact body grammar
- **WHEN** one or more body lines each have 1–64 ASCII standard-base64 characters, padding only at the end of the final body line, and concatenation strictly decodes/re-encodes identically to at least 32 bytes
- **THEN** the envelope matches with exact original offsets under LF, CRLF or mixed line endings, including END at EOF

#### Scenario: Invalid bodies and labels
- **WHEN** an envelope contains indentation, trailing boundary whitespace, blank body lines, metadata headers, invalid alphabet/padding, noncanonical base64, fewer than 32 decoded bytes, a body line over 64 characters or mismatched labels
- **THEN** the whole candidate produces no finding

#### Scenario: Exact framing marker recognition
- **WHEN** a whole line has five ASCII hyphens, uppercase BEGIN or END, one ASCII space, a case-sensitive 1–64-character label matching `[A-Z][A-Z0-9]*(?: [A-Z0-9]+)*`, and five closing hyphens
- **THEN** it is a recognized framing marker, including unsupported labels for termination/nesting checks, but only supported BEGIN labels start detection candidates

#### Scenario: Malformed framing and bare carriage return
- **WHEN** dash count, marker case or label syntax is wrong, or a bare CR appears without an immediately following LF
- **THEN** it is not stripped or treated as a valid marker; malformed text inside a candidate fails body validation and cannot shorten the candidate

#### Scenario: Nested and truncated candidates
- **WHEN** a BEGIN is followed by another BEGIN before the first subsequent END boundary of any label
- **THEN** that entire candidate is rejected without harvesting a nested block, scanning resumes after that END, and separate later complete candidates remain detectable

#### Scenario: Unsupported end marker recovery
- **WHEN** a supported BEGIN and body are followed by a recognized END PUBLIC KEY marker and then a separate supported complete envelope
- **THEN** the mismatched first candidate is rejected at that END and the later complete envelope is detected

#### Scenario: Missing terminator
- **WHEN** a candidate BEGIN has no subsequent END boundary
- **THEN** it extends to EOF and is unsupported without a partial-envelope finding

#### Scenario: Public and binary material
- **WHEN** input contains certificates, public-key envelopes, DER/binary data or other unsupported envelope labels
- **THEN** the control does not report them as supported private-key envelopes

### Requirement: Bounded GitHub token shapes
The GitHub control SHALL match whole maximal runs of Unicode alphanumeric characters plus `_` and `-` only when the run is exactly case-sensitive `ghp_` or `gho_` followed by 36 ASCII alphanumeric characters. Detection SHALL identify shape only, without checksum, entropy or provider authentication checks.

#### Scenario: Prefix ownership and delimiters
- **WHEN** supported tokens occur at content edges or are delimited by whitespace, quotes, commas, parentheses or periods
- **THEN** `ghp_` produces `secret.github_pat`, `gho_` produces `secret.github_oauth`, and each span covers the full 40-character token

#### Scenario: Whole candidate near misses
- **WHEN** a token has 35 or 37 suffix characters, an uppercase prefix, a Unicode alphanumeric suffix, or a touching alphanumeric/underscore/hyphen prefix or suffix
- **THEN** it produces no shortened-token finding

#### Scenario: Unsupported provider shapes
- **WHEN** text contains fine-grained `github_pat_`, `ghu_`, `ghs_`, `ghr_`, old unprefixed hex credentials or other provider/changed-length tokens
- **THEN** this control does not claim detection of those unsupported shapes

### Requirement: Credential adversarial verification
Automated local tests MUST cover each credential code's positive, negative/near-miss, malformed, minimum/maximum, embedded and repeated cases, original offsets with Unicode prefixes, and supported multiline behavior. Tests MUST cover overlapping bearer/GitHub evidence, adjacency where grammar permits, and unsupported encoding/obfuscation without executing payloads or using external services.

#### Scenario: Exact span assertions
- **WHEN** fixtures include punctuation, Unicode before candidates, multiple matches and malformed neighbors
- **THEN** tests assert both expected findings and exact original slices/spans without allowing shortened malformed candidates

#### Scenario: Supported and unsupported corpus
- **WHEN** detector suites run locally
- **THEN** allowed negatives, detected positives, documented unsupported forms and reasonable bypass attempts are all exercised deterministically without network, LLM or paid services
