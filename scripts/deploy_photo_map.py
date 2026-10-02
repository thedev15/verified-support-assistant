"""Launch a short-lived public preview of the Photo Map Remix on CoreWeave Sandboxes."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from cwsandbox import (
    AuthStrategy,
    Endpoint,
    EndpointAuth,
    EndpointKind,
    Sandbox,
    Service,
    ServiceVisibility,
)


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = Path("/app")
STATE_PATH = ROOT / "evidence" / ".deployment.json"
LIFETIME_SECONDS = 1800
SOURCE_PATHS = ("index.html", "styles.css", "app.js")


def mounted_files() -> list[dict[str, object]]:
    return [
        {
            "mount_path": str(APP_ROOT / filename),
            "file_content": (ROOT / "photo_map" / filename).read_bytes(),
        }
        for filename in SOURCE_PATHS
    ]


def wait_for_ready(base_url: str, timeout_seconds: int = 180) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(base_url, timeout=10) as response:
                if response.status == 200 and b"Atlas de Recuerdos" in response.read():
                    return
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
        time.sleep(4)
    raise RuntimeError(f"Photo map did not become ready: {last_error}")


def main() -> None:
    sandbox = Sandbox.run(
        "python",
        "-m",
        "http.server",
        "8000",
        "--bind",
        "0.0.0.0",
        auth=AuthStrategy.WANDB,
        container_image="python:3.11-slim",
        placement_mode="serverless",
        max_lifetime_seconds=LIFETIME_SECONDS,
        resources={"cpu": "500m", "memory": "512Mi"},
        mounted_files=mounted_files(),
        working_dir=str(APP_ROOT),
        services=[
            Service(
                port=8000,
                name="web",
                visibility=ServiceVisibility.PUBLIC,
                endpoint=Endpoint(kind=EndpointKind.HTTPS, auth=EndpointAuth.OPEN),
            )
        ],
        tags=["verified-support-assistant", "photo-map-remix", "ui-evidence"],
    )
    sandbox.wait()
    if not sandbox.service_urls:
        raise RuntimeError("Sandbox started without a public service URL")
    _, _, base_url = sandbox.service_urls[0]
    wait_for_ready(base_url)
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({"sandbox_id": sandbox.sandbox_id, "url": base_url}, indent=2))
    print(json.dumps({"sandbox_id": sandbox.sandbox_id, "url": base_url}))


if __name__ == "__main__":
    main()