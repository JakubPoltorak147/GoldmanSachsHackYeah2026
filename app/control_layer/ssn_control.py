"""Explicitly labelled hyphenated US SSN shapes only, not identity verification.

ASCII syntax and impossible-group checks; no unlabelled/compact/Unicode discovery.
"""

import re

from app.control_layer.domain import Finding, Interaction, Span

SSN_CONTROL_ID = "us-ssn"
SSN_CODE = "pii.us_ssn"
# Unicode-aware left boundary, with ASCII case folding only for the label.
# Rejecting a longer label must leave the inner standalone SSN searchable.
_LABEL = re.compile(r"(?<!\w)(?ai:US SSN|SSN)[ \t]*:[ \t]*")
_VALUE = re.compile(r"([0-9]{3})-([0-9]{2})-([0-9]{4})", re.ASCII)


class UsSsnControl:
    id = SSN_CONTROL_ID

    def evaluate(self, interaction: Interaction) -> tuple[Finding, ...]:
        text = interaction.content
        findings = []
        for label in _LABEL.finditer(text):
            end = label.end()
            while end < len(text) and (text[end].isalnum() or text[end] in "_-"):
                end += 1
            match = _VALUE.fullmatch(text[label.end() : end])
            if (
                match
                and 1 <= int(match[1]) <= 899
                and int(match[1]) != 666
                and int(match[2])
                and int(match[3])
            ):
                findings.append(Finding(self.id, SSN_CODE, Span(label.end(), end)))
        return tuple(findings)
