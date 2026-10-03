"""Classic ghp_/gho_ 36-character suffix shapes only; no checksum/authentication.

Whole Unicode alphanumeric/underscore/hyphen runs prevent truncated detection.
Other provider families, changed lengths and encoded forms are unsupported.
"""

import re

from app.control_layer.domain import Finding, Interaction, Span

GITHUB_CONTROL_ID = "github-token"
GITHUB_PAT_CODE = "secret.github_pat"
GITHUB_OAUTH_CODE = "secret.github_oauth"
_CANDIDATE = re.compile(r"[\w-]+", re.UNICODE)
_TOKEN = re.compile(r"(ghp_|gho_)[A-Za-z0-9]{36}", re.ASCII)


class GitHubTokenControl:
    id = GITHUB_CONTROL_ID

    def evaluate(self, interaction: Interaction) -> tuple[Finding, ...]:
        findings = []
        for candidate in _CANDIDATE.finditer(interaction.content):
            match = _TOKEN.fullmatch(candidate.group())
            if match:
                code = GITHUB_PAT_CODE if match[1] == "ghp_" else GITHUB_OAUTH_CODE
                findings.append(Finding(self.id, code, Span(*candidate.span())))
        return tuple(findings)
