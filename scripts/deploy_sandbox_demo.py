"""Deploy or capture the support assistant in a bounded CoreWeave Sandbox."""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import tarfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zipfile import ZipFile

import wandb
from cwsandbox import AuthHeaders, AuthStrategy, ResourceOptions, Sandbox, Service


ROOT = Path(__file__).resolve().parents[1]


def sandbox_auth() -> AuthHeaders | AuthStrategy:
    api_key = os.environ.get("SANDBOX_WANDB_KEY")
    if api_key:
        return AuthHeaders(
            headers={
                "x-wandb-api-key": api_key,
                "x-wandb-sdk-version": wandb.__version__,
            },
            strategy="wandb_api_key",
        )
    return AuthStrategy.WANDB


def build_archive() -> bytes:
    files = [
        "pyproject.toml",
        "README.md",
        "data/knowledge_base.json",
        "data/eval_set.json",
        "docs/live-demo/README.md",
        "scripts/capture_live_demo.py",
    ]
    files.extend(
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "support_assistant").glob("*.py"))
    )
    files.append("support_assistant/static/index.html")
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode="w:gz") as archive:
        for relative_path in files:
            archive.add(ROOT / relative_path, arcname=relative_path)
    return payload.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lifetime-minutes", type=int, default=90)
    parser.add_argument("--private-capture", action="store_true")
    args = parser.parse_args()

    name = f"verified-support-live-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
    expires_at = datetime.now(UTC) + timedelta(minutes=args.lifetime_minutes)
    sandbox = Sandbox.run(
        "sleep",
        "infinity",
        container_image=(
            "mcr.microsoft.com/playwright/python:v1.55.0-noble"
            if args.private_capture
            else "python:3.11-slim"
        ),
        auth=sandbox_auth(),
        max_lifetime_seconds=args.lifetime_minutes * 60,
        tags=[name, "verified-support-live-evidence"],
        resources=ResourceOptions(requests={"cpu": "1", "memory": "2Gi"}),
        services=(
            []
            if args.private_capture
            else [Service(port=8000, name="support-ui", visibility="public")]
        ),
        environment_variables={"PYTHONUNBUFFERED": "1"},
    )
    result = {
        "sandbox_id": sandbox.sandbox_id,
        "name": name,
        "expires_at_utc": expires_at.isoformat(),
    }
    print(json.dumps({"created": result}), flush=True)

    try:
        sandbox.wait(timeout=360)
        sandbox.write_file("/workspace/source.tar.gz", build_archive()).result(timeout=120)
        browser_install = (
            "python -m pip install --disable-pip-version-check playwright==1.55.0 && "
            if args.private_capture
            else ""
        )
        install_command = (
            "mkdir -p /workspace/app && cd /workspace/app && "
            "tar -xzf /workspace/source.tar.gz && "
            "python -m pip install --disable-pip-version-check -e . && "
            f"{browser_install}true"
        )
        install = sandbox.exec(
            ["bash", "-lc", install_command], timeout_seconds=300
        ).result()
        if install.returncode != 0:
            raise RuntimeError(f"Sandbox install failed: {install.stderr}")

        start = sandbox.exec(
            [
                "bash",
                "-lc",
                "cd /workspace/app && setsid -f python -m uvicorn "
                "support_assistant.api:app --host 0.0.0.0 --port 8000 "
                ">/workspace/app/server.log 2>&1 </dev/null",
            ],
            timeout_seconds=30,
        ).result()
        if start.returncode != 0:
            raise RuntimeError(f"Sandbox server start failed: {start.stderr}")

        public_url = (
            None
            if args.private_capture
            else next(url for port, _, url in sandbox.service_urls if port == 8000)
        )
        health_command = (
            "python - <<'PY'\n"
            "import json, time, urllib.request\n"
            "for attempt in range(90):\n"
            "    try:\n"
            "        with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2) as response:\n"
            "            print(response.read().decode())\n"
            "            break\n"
            "    except Exception:\n"
            "        if attempt == 89: raise\n"
            "        time.sleep(1)\n"
            "PY"
        )
        health = sandbox.exec(
            ["bash", "-lc", health_command], timeout_seconds=120
        ).result()
        if health.returncode != 0:
            raise RuntimeError(f"Sandbox health check failed: {health.stderr}")

        if args.private_capture:
            capture = sandbox.exec(
                [
                    "bash",
                    "-lc",
                    "cd /workspace/app && python scripts/capture_live_demo.py "
                    "--base-url http://127.0.0.1:8000 "
                    "--capture-environment coreweave-sandbox-private",
                ],
                timeout_seconds=360,
            ).result()
            if capture.returncode != 0:
                raise RuntimeError(f"Sandbox browser capture failed: {capture.stderr}")
            archive_bytes = sandbox.read_file(
                "/workspace/app/docs/live-demo/verified-support-live-evidence.zip",
                timeout_seconds=120,
            ).result()
            output_dir = ROOT / "docs" / "live-demo"
            shutil.rmtree(output_dir / "screenshots", ignore_errors=True)
            with ZipFile(io.BytesIO(archive_bytes)) as archive:
                root = Path("verified-support-live-evidence")
                for member in archive.infolist():
                    relative = Path(member.filename).relative_to(root)
                    target = output_dir / relative
                    if member.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(archive.read(member))
            (output_dir / "verified-support-live-evidence.zip").write_bytes(archive_bytes)
            (output_dir / "sandbox-capture.json").write_text(
                json.dumps(
                    {
                        "sandbox_id": sandbox.sandbox_id,
                        "capture_environment": "coreweave-sandbox-private",
                        "captured_at_utc": datetime.now(UTC).isoformat(),
                        "expires_at_utc": expires_at.isoformat(),
                    },
                    indent=2,
                )
                + "\n"
            )
            result.update(
                {
                    "visibility": "private",
                    "evidence_archive": str(
                        output_dir / "verified-support-live-evidence.zip"
                    ),
                }
            )
        else:
            result.update(
                {"public_url": public_url, "health_url": f"{public_url}/health"}
            )
        print(json.dumps({"ready": result}, indent=2), flush=True)
    except Exception:
        sandbox.stop(missing_ok=True).result(timeout=120)
        raise


if __name__ == "__main__":
    main()