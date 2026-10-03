"""Bounded trusted local literal catalog; no regex, execution, network or reload.

Catalog metadata is startup configuration, never derived from submitted content.
Known indicators can match benign documentation and do not establish maliciousness.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from app.control_layer.domain import Finding, Interaction, PolicyError, Span
from app.control_layer.registry import machine_id

ATTACK_CONTROL_ID = "known-attack-signatures"
MAX_CATALOG_BYTES = 64 * 1024
DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "attack-signatures.json"
)


@dataclass(frozen=True)
class AttackSignature:
    id: str
    code: str
    literal: str

    def __post_init__(self):
        if (
            not machine_id(self.id)
            or not machine_id(self.code, code=True)
            or not self.code.startswith("attack.")
            or type(self.literal) is not str
            or not 8 <= len(self.literal) <= 256
            or any(0xD800 <= ord(c) <= 0xDFFF for c in self.literal)
        ):
            raise PolicyError()


@dataclass(frozen=True)
class AttackCatalog:
    catalog_id: str
    signatures: tuple[AttackSignature, ...]

    def __post_init__(self):
        signatures = tuple(self.signatures)
        if (
            not machine_id(self.catalog_id)
            or not 1 <= len(signatures) <= 32
            or any(type(s) is not AttackSignature for s in signatures)
            or len({s.id for s in signatures}) != len(signatures)
            or len({s.literal for s in signatures}) != len(signatures)
        ):
            raise PolicyError()
        object.__setattr__(self, "signatures", signatures)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PolicyError()
        result[key] = value
    return result


def _invalid_constant(value):
    raise PolicyError()


def load_attack_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> AttackCatalog:
    """Read at most the bounded file size plus one byte, sanitize every failure."""
    try:
        with Path(path).open("rb") as stream:
            data = stream.read(MAX_CATALOG_BYTES + 1)
        if len(data) > MAX_CATALOG_BYTES:
            raise PolicyError()
        root = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_invalid_constant,
        )
        if type(root) is not dict or set(root) != {
            "version",
            "catalog_id",
            "signatures",
        }:
            raise PolicyError()
        if type(root["version"]) is not int or root["version"] != 1:
            raise PolicyError()
        if type(root["signatures"]) is not list:
            raise PolicyError()
        signatures = []
        for entry in root["signatures"]:
            if type(entry) is not dict or set(entry) != {"id", "code", "literal"}:
                raise PolicyError()
            signatures.append(
                AttackSignature(entry["id"], entry["code"], entry["literal"])
            )
        return AttackCatalog(root["catalog_id"], tuple(signatures))
    except Exception:
        raise PolicyError() from None


@dataclass(frozen=True)
class KnownAttackSignaturesControl:
    catalog: AttackCatalog
    id = ATTACK_CONTROL_ID

    def __post_init__(self):
        if type(self.catalog) is not AttackCatalog:
            raise PolicyError()

    @property
    def finding_codes(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(s.code for s in self.catalog.signatures))

    def evaluate(self, interaction: Interaction) -> tuple[Finding, ...]:
        occurrences = set()
        for signature in self.catalog.signatures:
            offset = 0
            while (start := interaction.content.find(signature.literal, offset)) >= 0:
                occurrences.add((start, start + len(signature.literal), signature.code))
                offset = start + 1
        return tuple(
            Finding(self.id, code, Span(start, end))
            for start, end, code in sorted(occurrences)
        )
