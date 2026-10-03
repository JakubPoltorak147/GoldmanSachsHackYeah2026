# Labelled SSN Detection Delta

## Purpose

Conservative deterministic detection identifies explicitly labelled US Social Security number shapes for centrally governed sensitive-data protection, without claiming identity or issuance verification.

## ADDED Requirements

### Requirement: Contextual US SSN grammar
The `us-ssn` control SHALL detect ASCII-case-insensitive labels `SSN` or `US SSN` followed by `[ \t]*:[ \t]*` and a whole ASCII `DDD-DD-DDDD` candidate. The label MUST start at content start or after a non-Unicode-alphanumeric, non-underscore character. Area MUST be 001–899 except 666, group 01–99, and serial 0001–9999.

#### Scenario: Exact supported label and value
- **WHEN** content includes `SSN: 123-45-6789` or `us ssn:\t321-54-6789` with an actual tab and supported left boundary
- **THEN** the control returns `pii.us_ssn` spanning only the complete 11-character number in original text

#### Scenario: Whole value boundary
- **WHEN** the maximal run of Unicode alphanumeric characters plus `_` and `-` after a supported label is exactly a supported number
- **THEN** the number matches immediately after the permitted separators, with trailing delimiters and preceding label/separators excluded from its span

#### Scenario: Candidate continuations
- **WHEN** the number touches an extra digit, Unicode alphanumeric, underscore or hyphen continuation
- **THEN** the whole run is rejected without reporting a shortened number

#### Scenario: Invalid numeric groups
- **WHEN** area is 000, 666 or 900–999, group is 00, serial is 0000, or any digit is non-ASCII
- **THEN** the candidate produces no finding

#### Scenario: Missing or unsupported context
- **WHEN** a number is unlabelled, compact, uses another label or punctuation separator, has a quote/newline before the value, or a label touches an alphanumeric/underscore prefix
- **THEN** the control does not claim a supported SSN detection

### Requirement: Span-capable sensitive-data findings
The US SSN control SHALL own only `pii.us_ssn`, require original-character spans under every action, and support central ALLOW, REDACT and BLOCK. It MUST emit no value, identity claim or action, MUST preserve input without normalization, and SHALL report all supported occurrences in ascending start/end/code order.

#### Scenario: Central redaction leaves context
- **WHEN** policy maps `pii.us_ssn` to REDACT
- **THEN** only selected number spans are masked with `[REDACTED]`, leaving the label and separators intact

#### Scenario: Shape is not verified identity
- **WHEN** a fictitious or documented example has supported syntax and context
- **THEN** it produces a shape finding without a claim that the number is issued to a person

### Requirement: Sensitive-data adversarial verification
Local tests MUST cover both labels/case, numeric group boundaries, missing context, malformed and overlong values, near misses, Unicode digits/offsets, repeated and embedded candidates, punctuation, multiline rejection and malformed-neighbor recovery. Existing email grammar and redaction tests MUST remain unchanged in meaning.

#### Scenario: Positive and negative numeric corpus
- **WHEN** the SSN suite runs
- **THEN** tests exercise accepted boundary groups and impossible groups, full candidate rejection, unsupported obfuscations, and exact original spans without external identity services

#### Scenario: Email compatibility
- **WHEN** existing email fixtures and new email-plus-SSN inputs are evaluated
- **THEN** existing email findings and span semantics remain compatible and both controls independently contribute to central policy
