"""Keep default application reporting file-backed and isolated per test."""

import pytest


@pytest.fixture(autouse=True)
def reporting_location(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CONTROL_LAYER_REPORTING_DB", str(tmp_path / "reporting.sqlite3")
    )
