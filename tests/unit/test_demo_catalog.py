import base64
from dataclasses import FrozenInstanceError

import pytest

from app.control_layer.composition import default_controls
from app.control_layer.demo import SCENARIOS, DemoSettings
from app.control_layer.domain import Interaction


def test_synthetic_catalog_is_bounded_immutable_and_public_projection_is_safe():
    assert len(SCENARIOS) == len({s.id for s in SCENARIOS}) == 11
    controls = default_controls()
    for scenario in SCENARIOS:
        assert 0 < len(scenario.content) <= 16384
        assert not any(0xD800 <= ord(c) <= 0xDFFF for c in scenario.content)
        with pytest.raises(FrozenInstanceError):
            scenario.content = "changed"
        public = scenario.public(DemoSettings(True, True)).model_dump()
        assert set(public) == {
            "id",
            "title",
            "description",
            "category",
            "expected_action",
            "expected_error",
            "expected_codes",
            "profile",
            "enabled",
            "prerequisite",
            "simulation",
        }
        assert "content" not in public
        codes = tuple(
            f.code
            for r in controls.registrations
            if r.definition.id != "semantic-security"
            for f in r.evaluator.evaluate(
                Interaction.create("local-ollama", scenario.content)
            )
        )
        assert all(
            code in codes
            for code in scenario.expected_codes
            if not code.startswith("semantic.")
        )
    private = next(s for s in SCENARIOS if s.id == "private-key")
    assert base64.b64decode(private.content.splitlines()[1]) == bytes(range(32))


def test_semantic_prerequisites_and_simulation_labels():
    for s in SCENARIOS:
        assert not s.public(DemoSettings()).enabled
        assert s.public(DemoSettings(True, False)).enabled == (
            not s.profile.startswith("semantic-")
        )
        assert s.simulation == s.id.endswith("unavailable")
