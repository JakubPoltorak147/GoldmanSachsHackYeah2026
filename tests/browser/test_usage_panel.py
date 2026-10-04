"""One operator journey: usage panel states; budget logic lives below the UI."""

import json

from playwright.sync_api import expect

from tests.browser.test_security_dashboard import dashboard_server  # noqa: F401

PATTERN = "**/v1/usage"


def usage_body(**overrides):
    body = {
        "enabled": True,
        "window_seconds": 60,
        "resets_in_seconds": 5,
        "requests": {"used": 10, "limit": 10},
        "estimated_tokens": {"used": 90, "limit": 100},
        "max_request_tokens": 50,
        "breaches": {"request_limit": 2, "token_limit": 0, "request_size": 1},
    }
    return json.dumps(body | overrides)


def fulfill(page, status, body):
    page.unroute(PATTERN)
    page.route(
        PATTERN,
        lambda route: route.fulfill(
            status=status, content_type="application/json", body=body
        ),
    )
    page.get_by_role("button", name="Refresh now").click()


def test_usage_panel_live_stale_disabled_and_limit_states(page, dashboard_server):  # noqa: F811
    origin, _, _, _ = dashboard_server
    page.goto(origin + "/dashboard")
    body = page.locator("#usage-body")
    expect(body).to_contain_text("of 120 requests")
    expect(page.locator("#usage-state")).to_contain_text("Resets in")
    expect(page.get_by_role("meter", name="Requests in window")).to_be_visible()
    expect(page.get_by_role("meter", name="Estimated tokens in window")).to_be_visible()
    # A failed read keeps the last real values and labels them stale.
    fulfill(page, 503, '{"error_code":"service_unavailable"}')
    expect(page.locator("#usage-state")).to_contain_text("Stale")
    expect(body).to_contain_text("of 120 requests")
    # An exhausted window is stated in text, not only by colour.
    fulfill(page, 200, usage_body())
    expect(body).to_contain_text("Limit reached · 0 requests remaining")
    expect(body).to_contain_text("Near limit · 10 tokens remaining")
    expect(body).to_contain_text("2 request · 0 token · 1 size")
    expect(page.locator("#usage-state")).to_contain_text("Resets in 5s")
    # A disabled control is reported as unmetered rather than as zero usage.
    fulfill(page, 200, '{"enabled": false}')
    expect(page.locator("#usage-state")).to_have_text("Disabled")
    expect(body).to_contain_text("not metered")
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
