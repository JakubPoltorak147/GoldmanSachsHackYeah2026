"""Shared isolated Chromium fixtures for operator journeys."""

import pytest


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    # Keep these isolated UI journeys viable in constrained CI containers.
    return {
        **browser_type_launch_args,
        "args": [
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--no-zygote",
            "--single-process",
        ],
    }


@pytest.fixture
def page(browser_type, browser_type_launch_args, tmp_path):
    # A persistent context closes the whole low-process browser on teardown.
    context = browser_type.launch_persistent_context(
        str(tmp_path / "browser"), **browser_type_launch_args
    )
    try:
        yield context.pages[0]
    finally:
        context.close()
