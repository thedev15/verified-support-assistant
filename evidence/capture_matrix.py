"""Capture and validate the deterministic 40-case Photo Map Remix UI matrix."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence" / "screenshots"
BASE_URL = os.environ.get("EVIDENCE_APP_URL", "http://127.0.0.1:8000").rstrip("/")

STATES = [
    ("overview", {}),
    ("filter-viajes", {"filter": "viajes"}),
    ("filter-sabores", {"filter": "sabores"}),
    ("filter-celebraciones", {"filter": "celebraciones"}),
    ("search-tokio", {"q": "tokio"}),
    ("search-fiesta", {"q": "fiesta"}),
    *[
        (f"memory-{memory_id}", {"memory": memory_id})
        for memory_id in (
            "barcelona", "paris", "tokio", "oaxaca", "buenos-aires", "marrakech",
            "nueva-york", "lisboa", "bangkok", "sevilla", "rio", "patagonia",
            "kioto", "islandia",
        )
    ],
]

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900, "device_scale_factor": 1},
    "mobile": {"width": 390, "height": 844, "device_scale_factor": 1},
}


def safe_url(params: dict[str, str]) -> str:
    return BASE_URL if not params else f"{BASE_URL}/?{urlencode(params)}"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for old_file in OUTPUT.glob("*.png"):
        old_file.unlink()

    captures: list[dict[str, object]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for viewport_name, dimensions in VIEWPORTS.items():
            context = browser.new_context(
                viewport={"width": dimensions["width"], "height": dimensions["height"]},
                device_scale_factor=dimensions["device_scale_factor"],
                color_scheme="light",
                locale="es-ES",
                reduced_motion="reduce",
            )
            page = context.new_page()
            for index, (state_name, params) in enumerate(STATES, start=1):
                url = safe_url(params)
                page.goto(url, wait_until="networkidle", timeout=30_000)
                page.wait_for_function("document.body.dataset.ready === 'true'")
                page.locator(".app-shell").wait_for(state="visible")
                filename = f"{viewport_name}-{index:02d}-{state_name}.png"
                path = OUTPUT / filename
                page.screenshot(path=str(path), full_page=False)
                if path.stat().st_size < 10_000:
                    raise RuntimeError(f"Suspiciously small screenshot: {path}")
                captures.append(
                    {
                        "file": f"screenshots/{filename}",
                        "viewport": viewport_name,
                        "width": dimensions["width"],
                        "height": dimensions["height"],
                        "state": state_name,
                        "query": params,
                        "bytes": path.stat().st_size,
                    }
                )
            context.close()
        browser.close()

    if len(captures) != 40 or len(list(OUTPUT.glob("*.png"))) != 40:
        raise RuntimeError("Expected exactly 40 validated screenshots")
    if any(not re.match(r"^(desktop|mobile)-\d{2}-", Path(item["file"]).name) for item in captures):
        raise RuntimeError("Unexpected screenshot naming")

    manifest = {
        "app": "Atlas de Recuerdos — Photo Map Remix",
        "source_url": BASE_URL,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "capture_count": len(captures),
        "states_per_viewport": len(STATES),
        "captures": captures,
    }
    (ROOT / "evidence" / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"capture_count": 40, "output": str(OUTPUT)}))


if __name__ == "__main__":
    main()