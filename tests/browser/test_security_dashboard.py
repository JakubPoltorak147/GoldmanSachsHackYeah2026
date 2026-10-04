"""Two operator journeys only; security assertions live below the browser."""

import socket
import threading
from dataclasses import replace
from time import monotonic
from uuid import UUID, uuid4

import pytest
import uvicorn
from playwright.sync_api import expect

from app.control_layer.reporting import InvocationStatus
from tests.fixtures.dashboard import dashboard_app, seed_dashboard


@pytest.fixture
def dashboard_server(tmp_path):
    app, store, state, _, _ = dashboard_app(tmp_path)
    ids = seed_dashboard(app, store, state)
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            log_level="critical",
            access_log=False,
            host="127.0.0.1",
            port=port,
        )
    )
    thread = threading.Thread(
        target=server.run, kwargs={"sockets": [sock]}, daemon=True
    )
    thread.start()
    deadline = monotonic() + 10
    while not server.started:
        assert thread.is_alive() and monotonic() < deadline, "test server failed"
        threading.Event().wait(0.01)
    try:
        yield f"http://127.0.0.1:{port}", app, store, ids
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
        store.close()


def test_overview_filters_safe_detail_keyboard_and_mobile(page, dashboard_server):
    origin, _, store, ids = dashboard_server
    page.goto(origin + "/dashboard")
    expect(page.locator("#metric-total")).to_have_text("7")
    expect(page.locator("#metric-allow")).to_have_text("3")
    expect(page.locator("#metric-redact")).to_have_text("1")
    expect(page.locator("#metric-block")).to_have_text("2")
    expect(page.locator("#metric-operational")).to_have_text("1")
    expect(page.locator("#status-unknown")).to_have_text("1")
    expect(page.locator("#findings-semantic")).to_have_text("1")
    expect(page.locator("#finding-rankings")).to_contain_text("2")
    page.screenshot(path="/tmp/security-dashboard-desktop.png", full_page=True)
    selected = page.locator(f'[data-interaction="{ids["unknown"]}"]')
    selected.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog")).to_be_visible()
    expect(page.locator("#detail-content")).to_contain_text(
        "does not prove the target was invoked"
    )
    expect(page.locator("#detail-content")).to_contain_text("generation:v1")
    expect(page.locator("#detail-content")).to_contain_text("qwen2.5:3b")
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).not_to_be_visible()
    expect(selected).to_be_focused()
    page.locator("#action").select_option("BLOCK")
    expect(page.locator("#metric-total")).to_have_text("2")
    expect(page.locator("#event-rows tr")).to_have_count(2)
    page.locator(f'[data-interaction="{ids["semantic"]}"]').click()
    expect(page.locator("#detail-content")).to_contain_text(
        "semantic.instruction_override"
    )
    expect(page.locator("#detail-content")).not_to_contain_text("PRIVATE_")
    page.get_by_role("button", name="Close event detail").click()
    page.locator("#action").select_option("ALLOW")
    page.locator("#invocation").select_option("not_invoked")
    expect(page.locator("#metric-total")).to_have_text("0")
    expect(page.locator("#event-empty")).to_be_visible()
    expect(page.locator("#timing-stats")).to_contain_text("0 recorded samples")
    page.get_by_role("button", name="Reset filters").click()
    expect(page.locator("#metric-total")).to_have_text("7")
    page.set_viewport_size({"width": 390, "height": 844})
    expect(
        page.get_by_role("heading", name="Security overview", exact=True)
    ).to_be_visible()
    page.screenshot(
        path="/tmp/security-dashboard-mobile-before-detail.png", full_page=True
    )
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    selected.click()
    expect(page.get_by_role("dialog")).to_be_visible()
    page.screenshot(path="/tmp/security-dashboard-mobile-detail.png", full_page=False)
    page.keyboard.press("Escape")
    page.screenshot(path="/tmp/security-dashboard-mobile.png", full_page=True)
    assert page.evaluate("window.compromised === undefined")
    # Discover a custom target that exists only outside the live first page.
    original = store.list_events()[0].event
    store._append_event(
        replace(original, interaction_id=uuid4(), target_id="historical-target")
    )
    for _ in range(50):
        store._append_event(replace(original, interaction_id=uuid4()))
    page.get_by_role("button", name="Refresh now").click()
    expect(page.locator("#metric-total")).to_have_text("58")
    expect(page.locator("#event-rows tr")).to_have_count(50)
    page.get_by_role("button", name="Older events", exact=True).click()
    expect(page.locator("#event-rows")).to_contain_text("historical-target")
    expect(page.locator('#target option[value="historical-target"]')).to_have_count(1)
    page.locator("#target").select_option("historical-target")
    expect(page.locator("#metric-total")).to_have_text("1")
    expect(page.locator("#event-rows tr")).to_have_count(1)


def test_polling_completion_failure_recovery_and_filter_race(page, dashboard_server):
    origin, app, _, ids = dashboard_server
    # Initial failed reads do not turn unavailable history into fabricated zeros.
    pattern = "**/v1/reporting/summary?*"
    page.route(
        pattern,
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"error_code":"reporting_unavailable"}',
        ),
    )
    page.goto(origin + "/dashboard")
    expect(page.locator("#availability")).to_contain_text("Reporting unavailable")
    expect(page.locator("#metric-total")).to_have_text("—")
    page.unroute(pattern)
    page.get_by_role("button", name="Refresh now").click()
    expect(page.locator("#metric-total")).to_have_text("7")
    selected = page.locator(f'[data-interaction="{ids["unknown"]}"]')
    selected.click()
    expect(page.locator("#detail-content")).to_contain_text("Unknown")
    # Completion changes an existing row, without a new event sequence.
    app.state.service.audit_sink.complete(
        UUID(ids["unknown"]), InvocationStatus.SUCCEEDED, 4.0, 9.0
    )
    expect(page.locator("#detail-content")).to_contain_text("Succeeded", timeout=8000)
    expect(page.locator("#status-unknown")).to_have_text("0")
    expect(page.locator("#status-succeeded")).to_have_text("3")
    expect(page.locator("#event-rows tr")).to_have_count(7)
    page.route(
        pattern,
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"error_code":"reporting_unavailable"}',
        ),
    )
    expect(page.locator("#availability")).to_contain_text("stale", timeout=8000)
    expect(page.locator("#metric-total")).to_have_text("7")
    expect(page.get_by_role("dialog")).to_be_visible()
    page.unroute(pattern)
    expect(page.locator("#availability")).to_contain_text("Live evidence", timeout=8000)
    page.keyboard.press("Escape")
    # Hold the old generation's summary; a new filter invalidates it.
    held = []

    def hold(route):
        held.append(route)

    page.route(pattern, hold)
    page.get_by_role("button", name="Refresh now").click()
    page.wait_for_function("document.querySelector('#refresh').disabled")
    page.locator("#action").select_option("BLOCK")
    page.unroute(pattern)
    for route in held:
        try:
            route.continue_()
        except Exception:
            # The old generation is intentionally aborted by a filter change.
            pass
    expect(page.locator("#metric-total")).to_have_text("2", timeout=8000)
    expect(page.locator("#event-rows tr")).to_have_count(2)
    expect(page.locator("#filter-chips")).to_contain_text("BLOCK")
    page.wait_for_timeout(3500)
    expect(page.locator("#metric-total")).to_have_text("2")
