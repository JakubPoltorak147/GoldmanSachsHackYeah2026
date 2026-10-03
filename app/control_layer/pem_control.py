"""Complete bounded private-key-shaped PEM blocks; no crypto/ASN.1 validation.

Malformed/nested/truncated envelopes and legacy metadata headers are unsupported.
Recognized unsupported END labels terminate candidates for deterministic recovery.
"""

import base64
import binascii
import re

from app.control_layer.domain import Finding, Interaction, Span

PEM_CONTROL_ID = "pem-private-key"
PEM_CODE = "secret.pem_private_key"
_LABELS = frozenset(
    {
        "PRIVATE KEY",
        "RSA PRIVATE KEY",
        "EC PRIVATE KEY",
        "OPENSSH PRIVATE KEY",
        "ENCRYPTED PRIVATE KEY",
    }
)
_MARKER = re.compile(r"-----(BEGIN|END) ([A-Z][A-Z0-9]*(?: [A-Z0-9]+)*)-----", re.ASCII)
_BODY = re.compile(r"[A-Za-z0-9+/=]{1,64}", re.ASCII)


def _marker(line: str) -> tuple[str, str] | None:
    match = _MARKER.fullmatch(line)
    return (match[1], match[2]) if match and len(match[2]) <= 64 else None


def _valid_body(lines: list[str]) -> bool:
    if not lines or any(_BODY.fullmatch(line) is None for line in lines):
        return False
    if any("=" in line for line in lines[:-1]):
        return False
    encoded = "".join(lines)
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        return False
    return len(decoded) >= 32 and base64.b64encode(decoded).decode("ascii") == encoded


class PemPrivateKeyControl:
    id = PEM_CONTROL_ID

    def evaluate(self, interaction: Interaction) -> tuple[Finding, ...]:
        findings = []
        offset = 0
        candidate = None
        body = []
        nested = False
        lines = interaction.content.split("\n")
        for index, raw_line in enumerate(lines):
            line = (
                raw_line[:-1]
                if index < len(lines) - 1 and raw_line.endswith("\r")
                else raw_line
            )
            marker = _marker(line)
            if candidate is None:
                if marker and marker[0] == "BEGIN" and marker[1] in _LABELS:
                    candidate = (offset, marker[1])
                    body = []
                    nested = False
            elif marker and marker[0] == "END":
                if not nested and marker[1] == candidate[1] and _valid_body(body):
                    findings.append(
                        Finding(
                            self.id, PEM_CODE, Span(candidate[0], offset + len(line))
                        )
                    )
                candidate = None
            else:
                if marker and marker[0] == "BEGIN":
                    nested = True
                body.append(line)
            offset += len(raw_line) + 1
        return tuple(findings)
