"""Exercise the production UI in Chromium and capture release evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "evidence" / "browser"
AXE_PATH = ROOT / "web" / "node_modules" / "axe-core" / "axe.min.js"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def assert_no_horizontal_overflow(page: Page) -> None:
    dimensions = page.evaluate(
        "() => ({width: document.documentElement.scrollWidth, viewport: window.innerWidth})"
    )
    assert dimensions["width"] <= dimensions["viewport"], dimensions


def audit_accessibility(page: Page, route: str, findings: dict[str, object]) -> None:
    page.evaluate(AXE_PATH.read_text(encoding="utf-8"))
    violations = page.evaluate(
        """async () => (await axe.run(document, {
          runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']}
        })).violations.map(({id, impact, help, nodes}) => ({
          id, impact, help,
          targets: nodes.map((node) => node.target.join(' '))
        }))"""
    )
    findings["accessibility"][route] = violations
    assert not violations, json.dumps({"route": route, "violations": violations}, indent=2)


def main() -> None:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    findings: dict[str, object] = {
        "base_url": base_url,
        "console_errors": [],
        "page_errors": [],
        "failed_responses": [],
        "accessibility": {},
        "checks": [],
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_context(
            viewport={"width": 1440, "height": 1100},
            color_scheme="dark",
            reduced_motion="reduce",
        )
        page = desktop.new_page()
        page.on(
            "console",
            lambda message: (
                findings["console_errors"].append(message.text) if message.type == "error" else None
            ),
        )
        page.on("pageerror", lambda error: findings["page_errors"].append(str(error)))
        page.on(
            "response",
            lambda response: (
                findings["failed_responses"].append(
                    {"status": response.status, "url": response.url}
                )
                if response.status >= 400
                else None
            ),
        )

        page.goto(f"{base_url}/assistant", wait_until="networkidle")
        page.get_by_text("12 policies · 40 evals", exact=False).wait_for()
        page.locator("#question").fill("How long does a card refund take?")
        page.locator("#ask").click()
        page.locator('#response[data-complete="true"]').wait_for()
        page.get_by_text("✓ Verified answer").wait_for()
        page.get_by_text("REF-001", exact=False).last.wait_for()
        assert page.locator(".history-list li").count() == 1
        assert_no_horizontal_overflow(page)
        audit_accessibility(page, "/assistant", findings)
        page.screenshot(path=args.output_dir / "assistant-desktop.png", full_page=True)
        findings["checks"].append("desktop assistant stream, citation, and history")

        page.get_by_role("link", name="Open versioned policy").click()
        page.get_by_role("heading", name="Refund processing times").wait_for()
        assert "5 to 10 business days" in page.locator(".policy-copy").inner_text()
        audit_accessibility(page, "/policies/REF-001", findings)
        findings["checks"].append("citation deep-link and policy detail")

        page.goto(f"{base_url}/policies", wait_until="networkidle")
        page.get_by_placeholder("Search refunds, shipping, security…").fill("security")
        assert "1 results" in page.locator(".result-count").inner_text()
        audit_accessibility(page, "/policies", findings)
        page.screenshot(path=args.output_dir / "policies-search.png", full_page=True)
        findings["checks"].append("policy catalog search")

        page.goto(f"{base_url}/evaluations", wait_until="networkidle")
        page.get_by_role("heading", name="Evaluation dashboard").wait_for()
        assert page.locator(".metric-card").count() == 4
        page.get_by_role("button", name="Refusal", exact=True).click()
        assert "Showing 15 of 40 cases" in page.locator(".evaluation-count").inner_text()
        page.locator(".case-row").first.locator("summary").click()
        audit_accessibility(page, "/evaluations", findings)
        page.screenshot(path=args.output_dir / "evaluations-desktop.png", full_page=True)
        findings["checks"].append("evaluation metrics, filtering, and case detail")

        page.goto(f"{base_url}/about", wait_until="networkidle")
        page.get_by_role(
            "heading", name="Support answers with an inspectable evidence trail."
        ).wait_for()
        assert page.locator(".process-card").count() == 4
        audit_accessibility(page, "/about", findings)
        findings["checks"].append("architecture and limitations page")

        mobile = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
            color_scheme="light",
            reduced_motion="reduce",
        )
        mobile_page = mobile.new_page()
        for route in ("/assistant", "/policies", "/evaluations", "/about"):
            mobile_page.goto(f"{base_url}{route}", wait_until="networkidle")
            assert_no_horizontal_overflow(mobile_page)
        mobile_page.goto(f"{base_url}/assistant", wait_until="networkidle")
        mobile_page.screenshot(path=args.output_dir / "assistant-mobile.png", full_page=True)
        findings["checks"].append("390px responsive layout across every product route")

        mobile.close()
        desktop.close()
        browser.close()

    assert not findings["console_errors"], findings["console_errors"]
    assert not findings["page_errors"], findings["page_errors"]
    assert not findings["failed_responses"], findings["failed_responses"]
    findings["status"] = "pass"
    result_path = args.output_dir / "browser-verification.json"
    result_path.write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    main()
