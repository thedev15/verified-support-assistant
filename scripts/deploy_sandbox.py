"""Launch a one-hour public preview of the extractive assistant on CoreWeave Sandboxes."""

from __future__ import annotations

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
SANDBOX_ROOT = Path("/app")
LIFETIME_SECONDS = 3600
SOURCE_PATHS = (
    Path("pyproject.toml"),
    Path("README.md"),
    Path("data/knowledge_base.json"),
    Path("support_assistant/__init__.py"),
    Path("support_assistant/api.py"),
    Path("support_assistant/config.py"),
    Path("support_assistant/generation.py"),
    Path("support_assistant/knowledge.py"),
    Path("support_assistant/models.py"),
    Path("support_assistant/retrieval.py"),
    Path("support_assistant/service.py"),
    Path("support_assistant/static/index.html"),
)


def mounted_files() -> list[dict[str, object]]:
    return [
        {
            "mount_path": str(SANDBOX_ROOT / relative_path),
            "file_content": (ROOT / relative_path).read_bytes(),
        }
        for relative_path in SOURCE_PATHS
    ]


def wait_for_health(base_url: str, timeout_seconds: int = 180) -> None:
    deadline = time.monotonic() + timeout_seconds
    health_url = f"{base_url.rstrip('/')}/health"
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=10) as response:
                if response.status == 200:
                    print(f"Health check passed: {health_url}")
                    return
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
        time.sleep(5)
    raise RuntimeError(f"Service did not become healthy: {last_error}")


def main() -> None:
    sandbox = Sandbox.run(
        "/bin/sh",
        "-lc",
        (
            "python -m pip install --disable-pip-version-check --no-cache-dir . "
            "&& exec python -m uvicorn support_assistant.api:app "
            "--host 0.0.0.0 --port 8000"
        ),
        auth=AuthStrategy.WANDB,
        container_image="python:3.11-slim",
        placement_mode="serverless",
        max_lifetime_seconds=LIFETIME_SECONDS,
        resources={"cpu": "1", "memory": "2Gi"},
        mounted_files=mounted_files(),
        working_dir=str(SANDBOX_ROOT),
        environment_variables={
            "LLM_BACKEND": "extractive",
            "ENABLE_WEAVE": "false",
            "PYTHONUNBUFFERED": "1",
        },
        services=[
            Service(
                port=8000,
                name="web",
                visibility=ServiceVisibility.PUBLIC,
                endpoint=Endpoint(kind=EndpointKind.HTTPS, auth=EndpointAuth.OPEN),
            )
        ],
        tags=["verified-support-assistant", "portfolio-preview"],
    )
    sandbox.wait()
    if not sandbox.service_urls:
        raise RuntimeError("Sandbox started without a public service URL")

    _, _, base_url = sandbox.service_urls[0]
    print(f"Sandbox ID: {sandbox.sandbox_id}")
    print(f"Preview URL (expires within one hour): {base_url}")
    wait_for_health(base_url)


if __name__ == "__main__":
    main()