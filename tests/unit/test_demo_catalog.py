import base64
import json
from dataclasses import FrozenInstanceError

import pytest

from app.control_layer.composition import default_controls
from app.control_layer.demo import SCENARIOS, DemoSettings
from app.control_layer.domain import Interaction


def test_synthetic_catalog_is_bounded_immutable_and_public_projection_is_safe():
    assert len(SCENARIOS) == len({s.id for s in SCENARIOS}) == 19
    assert {s.id for s in SCENARIOS} == {
        "benign",
        "email-pii",
        "api-secret",
        "private-key",
        "historical-signature",
        "prompt-injection",
        "indirect-override",
        "exfiltration-intent",
        "hybrid-controls",
        "evaluator-unavailable",
        "generation-unavailable",
        "github-pat",
        "github-oauth",
        "labelled-ssn",
        "pickle-os",
        "pickle-posix",
        "encoded-exec",
        "multiple-pii",
        "pii-and-secret",
    }
    controls = default_controls()
    covered = set()
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
            "expected_explanation",
            "runtime_requirements",
        }
        assert "content" not in public
        assert (
            scenario.expected_explanation and len(scenario.expected_explanation) < 500
        )
        assert len(set(scenario.runtime_requirements)) == len(
            scenario.runtime_requirements
        )
        assert set(scenario.runtime_requirements) <= {"generation", "semantic"}
        encoded = json.dumps(public)
        assert json.dumps(scenario.content)[1:-1] not in encoded
        findings = tuple(
            f
            for r in controls.registrations
            if r.definition.id != "semantic-security"
            for f in r.evaluator.evaluate(
                Interaction.create("local-ollama", scenario.content)
            )
        )
        codes = tuple(f.code for f in findings)
        covered.update(codes)
        for finding in findings:
            matched = scenario.content[finding.span.start : finding.span.end]
            assert json.dumps(matched)[1:-1] not in encoded
        assert all(
            code in codes
            for code in scenario.expected_codes
            if not code.startswith("semantic.")
        )
    assert covered == {
        f.code
        for r in controls.registrations
        if r.definition.id != "semantic-security"
        for f in r.definition.findings
    }
    private = next(s for s in SCENARIOS if s.id == "private-key")
    assert base64.b64decode(private.content.splitlines()[1]) == bytes(range(32))


def test_semantic_prerequisites_and_simulation_labels():
    for s in SCENARIOS:
        assert not s.public(DemoSettings()).enabled
        assert s.public(DemoSettings(True, False)).enabled == (
            not s.profile.startswith("semantic-")
        )
        assert s.simulation == s.id.endswith("unavailable")
        if s.simulation:
            assert s.runtime_requirements == ()
        elif s.profile == "semantic-live":
            assert s.runtime_requirements == ("semantic",)
        elif s.expected_action == "BLOCK":
            assert s.runtime_requirements == ()
        else:
            assert s.runtime_requirements == ("generation",)
