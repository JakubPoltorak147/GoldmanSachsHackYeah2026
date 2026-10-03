"""Bounded ASCII email-address detection, not general email/PII protection."""

import re

from app.control_layer.domain import Finding, Interaction, Span

EMAIL_CONTROL_ID = "email-address"
EMAIL_CODE = "pii.email"
PRODUCTION_CODES = {EMAIL_CONTROL_ID: frozenset({EMAIL_CODE})}
_ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
_LOCAL = re.compile(rf"{_ATOM}(?:\.{_ATOM})*", re.ASCII)
_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", re.ASCII)
_FINAL = re.compile(r"[A-Za-z]{2,63}", re.ASCII)
# Keep invalid address continuations inside candidates; never search a suffix.
_CANDIDATE = re.compile(r"[^\s<>() ,]+")
# Delimiters inside an unsupported quoted local part must never expose a suffix.
_QUOTED_LOCAL = re.compile(r'"(?:[^"\\]|\\.)*"@')


class EmailAddressControl:
    id = EMAIL_CONTROL_ID

    def evaluate(self, interaction: Interaction) -> tuple[Finding, ...]:
        findings = []
        quoted = tuple(_QUOTED_LOCAL.finditer(interaction.content))
        for match in _CANDIDATE.finditer(interaction.content):
            if any(match.start() < q.end() and q.start() < match.end() for q in quoted):
                continue
            candidate = match.group()
            if candidate.count("@") != 1:
                continue
            # One sentence-ending period is punctuation; multiple dots are invalid.
            if candidate.endswith(".") and not candidate.endswith(".."):
                candidate = candidate[:-1]
            local, domain = candidate.split("@")
            labels = domain.split(".")
            if (
                not 1 <= len(local) <= 64
                or _LOCAL.fullmatch(local) is None
                or len(domain) > 253
                or len(labels) < 2
                or _FINAL.fullmatch(labels[-1]) is None
                or any(
                    _LABEL.fullmatch(label) is None or label.lower().startswith("xn--")
                    for label in labels
                )
            ):
                continue
            findings.append(
                Finding(
                    self.id,
                    EMAIL_CODE,
                    Span(match.start(), match.start() + len(candidate)),
                )
            )
        return tuple(findings)
