"""Whole Authorization-shaped text lines only; no transport/credential validation."""

import re

from app.control_layer.domain import Finding, Interaction, Span

BEARER_CONTROL_ID = "bearer-credential"
BEARER_CODE = "secret.bearer"
_HEADER = re.compile(
    r"[ \t]*Authorization[ \t]*:[ \t]*Bearer +([A-Za-z0-9._~+/-]+=*)[ \t]*",
    re.ASCII | re.IGNORECASE,
)


class BearerCredentialControl:
    id = BEARER_CONTROL_ID

    def evaluate(self, interaction: Interaction) -> tuple[Finding, ...]:
        findings = []
        offset = 0
        lines = interaction.content.split("\n")
        for index, line in enumerate(lines):
            physical = (
                line[:-1] if index < len(lines) - 1 and line.endswith("\r") else line
            )
            match = _HEADER.fullmatch(physical)
            if match and len(match[1]) <= 4096:
                start, end = match.span(1)
                findings.append(
                    Finding(self.id, BEARER_CODE, Span(offset + start, offset + end))
                )
            offset += len(line) + 1
        return tuple(findings)
