"""Closed semantic scores become fixed findings; policy alone enforces them."""

import json
import math
from collections.abc import Callable
from dataclasses import dataclass

from app.control_layer.domain import EvaluationError, Finding, Interaction

SEMANTIC_ID = "semantic-security"
FIELDS = ("prompt_injection", "instruction_override", "exfiltration_intent")
CODES = tuple("semantic." + field for field in FIELDS)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError()
        result[key] = value
    return result


def invalid_constant(_value):
    raise ValueError()


def strict_json(text):
    if type(text) is not str or any(0xD800 <= ord(c) <= 0xDFFF for c in text):
        raise ValueError()
    return json.loads(
        text, object_pairs_hook=unique_object, parse_constant=invalid_constant
    )


def validate_scores(scores):
    try:
        if type(scores) is not dict or set(scores) != set(FIELDS):
            raise ValueError()
        for value in scores.values():
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not 0 <= value <= 1
            ):
                raise ValueError()
        return {field: scores[field] for field in FIELDS}
    except Exception:
        raise EvaluationError() from None


def parse_scores(text):
    try:
        return validate_scores(strict_json(text))
    except Exception:
        raise EvaluationError() from None


@dataclass(frozen=True)
class SemanticSecurityControl:
    runtime: Callable[[str], dict]
    threshold: float | None = None
    id = SEMANTIC_ID

    def __post_init__(self):
        if not callable(self.runtime) or (
            self.threshold is not None
            and (
                type(self.threshold) not in (int, float)
                or not math.isfinite(self.threshold)
                or not 0 < self.threshold <= 1
            )
        ):
            raise ValueError("invalid_semantic_configuration")

    def evaluate(self, interaction: Interaction) -> tuple[Finding, ...]:
        try:
            if self.threshold is None:
                raise ValueError()
            scores = validate_scores(self.runtime(interaction.content))
            return tuple(
                Finding(SEMANTIC_ID, code)
                for field, code in zip(FIELDS, CODES, strict=True)
                if scores[field] >= self.threshold
            )
        except Exception:
            raise EvaluationError() from None
