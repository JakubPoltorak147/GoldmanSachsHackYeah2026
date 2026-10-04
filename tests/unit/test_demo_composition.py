import pytest
from fastapi.testclient import TestClient

from app.control_layer.demo import DemoSettings, load_demo_settings
from tests.fixtures.demo import demo_app


@pytest.mark.parametrize("value", ["1", "TRUE", "yes", "", None])
def test_invalid_flags_fail_closed(value):
    with pytest.raises(ValueError, match="invalid_demo_configuration"):
        load_demo_settings({"CONTROL_LAYER_DEMO_ENABLED": value})


def test_flags_default_off_and_strict():
    assert load_demo_settings({}) == DemoSettings()
    with pytest.raises(ValueError):
        DemoSettings(1, False)


def test_profiles_frozen_metadata_ordinary_policy_and_no_startup_calls(tmp_path):
    app, store, _, calls, evaluations, _ = demo_app(tmp_path)
    with TestClient(app):
        demo = app.state.demo
        assert set(demo.profiles) == {
            "deterministic-live",
            "semantic-live",
            "semantic-unavailable",
            "target-unavailable",
        }
        with pytest.raises(TypeError):
            demo.profiles["x"] = app.state.service
        assert demo.workspace.custom.policy_digest == app.state.service.policy.digest
        assert not next(
            c.enabled
            for c in demo.workspace.custom.controls
            if c.control_id == "semantic-security"
        )
        for service in demo.profiles.values():
            assert service.audit_sink.store is store
            assert service.audit_sink.upstream is app.state.service.audit_sink.upstream
        assert not calls and not evaluations and not store.list_events()
    store.close()


def test_disabled_profiles_and_missing_target_fail_closed(tmp_path):
    app, store, _, _, _, _ = demo_app(tmp_path, semantic=False)
    with TestClient(app):
        with pytest.raises(ValueError, match="invalid_request"):
            app.state.demo.resolve("prompt-injection")
        assert len(app.state.demo.profiles) == 2
    store.close()


def test_missing_target_invalid_profiles_and_private_metadata(tmp_path):
    from app.control_layer.demo import build_demo
    from app.control_layer.registry import ControlRegistry
    from app.control_layer.targets import (
        LocalEchoTarget,
        RegisteredTarget,
        TargetDefinition,
        TargetRegistry,
    )

    app, store, _, _, _, _ = demo_app(tmp_path)
    with TestClient(app):
        service = app.state.service
        controls = ControlRegistry(
            tuple(c.registration for c in service.policy.entries)
        )
        original = service.targets
        service.targets = TargetRegistry(
            original.registrations
            + (RegisteredTarget(TargetDefinition("internal-only"), LocalEchoTarget()),)
        )
        demo = build_demo(DemoSettings(True, True), service, controls)
        assert {t.target_id for t in demo.workspace.custom.targets} == {
            "local-echo",
            "local-ollama",
        }
        service.targets = TargetRegistry(())
        with pytest.raises(ValueError, match="invalid_demo_configuration"):
            build_demo(DemoSettings(True, True), service, controls)
        service.targets = original
        with pytest.raises(ValueError, match="invalid_demo_configuration"):
            build_demo(DemoSettings(True, True), service, ControlRegistry(()))
    store.close()
