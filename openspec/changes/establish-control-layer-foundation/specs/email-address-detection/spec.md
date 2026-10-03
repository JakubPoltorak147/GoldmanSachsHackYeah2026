# Spec Delta

## Purpose

Email-address detection supplies deterministic, bounded findings about supported ASCII addresses so centralized policy can decide how to handle text containing them.

## ADDED Requirements

### Requirement: Supported email detection
The email control SHALL return one structured finding per complete supported ASCII email address in the original interaction text, including a trusted control ID, stable finding code, and source span, without copying the matched address into the finding.

#### Scenario: Supported address variants
- **WHEN** text contains a supported address with a plus tag, mixed case, or subdomain
- **THEN** the control returns a finding spanning the complete address in the original text

#### Scenario: Multiple addresses with punctuation
- **WHEN** text contains two supported addresses inside surrounding punctuation and sentence text
- **THEN** the control returns two findings whose spans exclude the surrounding punctuation

#### Scenario: Unicode before an ASCII address
- **WHEN** non-ASCII text appears before a supported ASCII address
- **THEN** the finding span still identifies the exact address in the original text

#### Scenario: No supported address
- **WHEN** text contains no supported ASCII email address
- **THEN** the control returns no findings

### Requirement: Whole-candidate matching
The email control MUST NOT report a valid-looking substring of a malformed, overlong, or unsupported address as though it were a complete supported address.

#### Scenario: Malformed local part
- **WHEN** a candidate contains consecutive dots in its local part
- **THEN** the control does not return a finding for a suffix of that candidate

#### Scenario: Overlong local part
- **WHEN** a candidate local part exceeds the supported length
- **THEN** the control does not return a finding for a shortened suffix

#### Scenario: Unsupported email form
- **WHEN** a candidate uses a quoted local part, Unicode address characters, an `xn--` internationalized domain label, a domain literal, HTML/percent/base64 encoded text, or obfuscation outside the documented grammar
- **THEN** the control does not claim that candidate as a supported address
