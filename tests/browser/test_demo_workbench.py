"""Three essential operator journeys; security decisions tested below the UI."""

import json
import socket
import threading
from time import monotonic

import pytest
import uvicorn
from playwright.sync_api import expect

from tests.fixtures.demo import demo_app


@pytest.fixture
def demo_server(tmp_path):
    app, store, state, calls, evaluations, stream = demo_app(tmp_path)
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="critical",
            access_log=False,
            proxy_headers=False,
        )
    )
    thread = threading.Thread(
        target=server.run, kwargs={"sockets": [sock]}, daemon=True
    )
    thread.start()
    deadline = monotonic() + 10
    while not server.started:
        assert thread.is_alive() and monotonic() < deadline
        threading.Event().wait(0.01)
    try:
        yield f"http://127.0.0.1:{port}", app, store, state, calls, evaluations, stream
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
        store.close()


def enter(page, origin):
    page.goto(origin + "/dashboard")
    page.locator("#nav-interactions").click()
    expect(page.locator("#workspace-availability")).to_contain_text(
        "Configured controls"
    )


def scenario(page, identifier):
    page.locator(f'[data-scenario="{identifier}"]').click()
    page.get_by_role("button", name="Run scenario", exact=True).click()
    expect(page.locator("#run-status")).not_to_contain_text("Running")
    expect(page.locator("#run-pipeline")).to_contain_text("Immediate outcome")


def test_scenarios_actual_results_audit_overview_keyboard_and_mobile(page, demo_server):
    origin, _, _, _, calls, _, _ = demo_server
    enter(page, origin)
    scenario(page, "benign")
    expect(page.locator("#run-status")).to_have_text("Decision: ALLOW")
    expect(page.locator("#run-result")).to_contain_text("Uninspected model response")
    assert page.evaluate("window.compromised === undefined")
    audit = page.get_by_role("button", name="Inspect matching audit event")
    audit.click()
    expect(page.locator("#detail-content")).not_to_contain_text("DEMO_OUTPUT")
    page.keyboard.press("Escape")
    expect(audit).to_be_focused()
    scenario(page, "email-pii")
    expect(page.locator("#run-status")).to_have_text("Decision: REDACT")
    assert calls[-1] == "Write a short greeting for [REDACTED]."
    scenario(page, "api-secret")
    expect(page.locator("#run-status")).to_have_text("Decision: BLOCK")
    expect(page.locator("#run-result")).not_to_contain_text("DEMO_OUTPUT")
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.screenshot(path="/tmp/workbench-desktop.png", full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    page.screenshot(path="/tmp/workbench-mobile.png", full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.locator("#nav-overview").click()
    expect(page.locator("#metric-total")).to_have_text("3")
    expect(page.locator("#event-rows tr")).to_have_count(3)


def test_semantic_failures_mismatch_missing_evidence_and_no_retry(page, demo_server):
    origin, _, _, state, _, _, _ = demo_server
    enter(page, origin)
    scenario(page, "prompt-injection")
    expect(page.locator("#run-status")).to_have_text("Decision: BLOCK")
    expect(page.locator("#run-pipeline")).to_contain_text("semantic.prompt_injection")
    scenario(page, "evaluator-unavailable")
    expect(page.locator("#run-status")).to_contain_text("evaluation_failed")
    expect(page.locator("#run-pipeline")).to_contain_text("Not reached")
    expect(page.locator("#run-pipeline")).to_contain_text("Not invoked")
    scenario(page, "generation-unavailable")
    expect(page.locator("#run-status")).to_contain_text("target_failed")
    expect(page.locator("#run-pipeline")).to_contain_text("ALLOW")
    expect(page.locator("#run-pipeline")).to_contain_text("Failed")
    page.route(
        "**/v1/reporting/events/*",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"error_code":"reporting_unavailable"}',
        ),
    )
    scenario(page, "benign")
    expect(page.locator("#run-pipeline")).to_contain_text(
        "Reporting evidence unavailable"
    )
    expect(page.locator("#run-result")).to_contain_text("Uninspected model response")
    page.unroute("**/v1/reporting/events/*")
    # Actual classification may disagree; expectation never establishes policy.
    state["semantic_fail"] = True
    scenario(page, "prompt-injection")
    expect(page.locator("#run-result")).to_contain_text("Expected / observed mismatch")
    state["semantic_fail"] = False
    posts = []
    page.route(
        "**/v1/interactions",
        lambda route: (posts.append(route.request), route.abort())[1],
    )
    scenario_button = page.locator('[data-scenario="benign"]')
    scenario_button.click()
    page.get_by_role("button", name="Run scenario", exact=True).click()
    expect(page.locator("#run-status")).to_contain_text("Outcome unknown")
    assert len(posts) == 1


def test_custom_controls_scalar_privacy_navigation_lock_and_metadata_failure(
    page, demo_server
):
    origin, _, _, _, _, _, stream = demo_server
    enter(page, origin)
    expect(page.locator("#custom-target")).to_have_value("local-echo")
    expect(page.locator("#custom-controls")).to_contain_text(
        "semantic-securityDisabled"
    )
    page.locator("#custom-content").fill("🦊" * 16384)
    expect(page.locator("#input-count")).to_have_text("16,384 / 16,384 characters")
    expect(page.locator("#run-custom")).to_be_enabled()
    page.locator("#custom-content").fill("🦊" * 16385)
    expect(page.locator("#run-custom")).to_be_disabled()
    canary = (
        "CUSTOM_PRIVATE<script>window.compromised=true</script> alex@example.invalid"
    )
    page.locator('[data-scenario="api-secret"]').click()
    page.locator("#custom-content").fill(canary)
    page.locator("#run-custom").click()
    expect(page.locator("#run-status")).to_have_text("Decision: REDACT")
    expect(page.locator("#run-result")).to_contain_text(
        "Approved input returned by Local echo"
    )
    expect(page.locator("#run-result")).to_contain_text("[REDACTED]")
    expect(page.locator("#scenario-selection")).to_be_empty()
    assert page.evaluate("window.compromised === undefined")
    assert page.evaluate("JSON.stringify([localStorage,sessionStorage])") == "[{},{}]"
    assert "CUSTOM_PRIVATE" not in stream.getvalue() and canary not in page.url
    page.locator("#custom-target").select_option("local-ollama")
    page.locator("#run-custom").click()
    expect(page.locator("#run-result")).to_contain_text("Uninspected model response")
    page.locator("#nav-overview").click()
    page.locator("#nav-interactions").click()
    expect(page.locator("#custom-content")).to_have_value("")
    expect(page.locator("#run-result")).to_be_empty()
    same_view = []
    page.route("**/v1/interactions", lambda route: same_view.append(route))
    page.locator("#custom-content").fill("Same-view synthetic request")
    page.locator("#run-custom").click()
    expect(page.locator("#run-custom")).to_be_disabled()
    page.locator("#nav-interactions").click()
    same_view[0].fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(
            {"action": "ALLOW", "result": {"content": "SAME_VIEW_RESPONSE"}}
        ),
    )
    page.unroute("**/v1/interactions")
    expect(page.locator("#run-status")).to_have_text("Decision: ALLOW")
    expect(page.locator("#run-result")).to_contain_text("SAME_VIEW_RESPONSE")
    page.locator("#nav-interactions").click()
    expect(page.locator("#run-status")).to_have_text("Decision: ALLOW")
    expect(page.locator("#run-result")).to_contain_text("SAME_VIEW_RESPONSE")
    held = []
    page.route("**/v1/interactions", lambda route: held.append(route))
    page.locator("#custom-content").fill("Pending synthetic request")
    page.locator("#run-custom").click()
    expect(page.locator("#run-custom")).to_be_disabled()
    expect(page.locator('[data-scenario="benign"]')).to_be_disabled()
    page.locator("#nav-overview").click()
    page.locator("#nav-interactions").click()
    expect(page.locator("#run-custom")).to_be_disabled()
    expect(page.locator('[data-scenario="benign"]')).to_be_disabled()
    assert len(held) == 1
    held[0].fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(
            {"action": "ALLOW", "result": {"content": "ABANDONED_PRIVATE_OUTPUT"}}
        ),
    )
    page.unroute("**/v1/interactions")
    expect(page.locator('[data-scenario="benign"]')).to_be_enabled()
    expect(page.locator("#run-result")).to_be_empty()
    expect(page.locator("#run-status")).to_contain_text("after navigation")
    page.route(
        "**/v1/demo/workspace", lambda route: route.fulfill(status=503, body="{}")
    )
    page.locator("#reload-workspace").click()
    expect(page.locator("#workspace-availability")).to_contain_text("unavailable")
    page.locator("#custom-content").fill("hello")
    expect(page.locator("#run-custom")).to_be_disabled()
    expect(page.locator("#custom-controls")).to_be_empty()
