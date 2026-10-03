# Operations and deployment

Verified Support Assistant ships as one same-origin service: FastAPI serves the
JSON/SSE API and the compiled React application. The default extractive backend
is deterministic, stateless, and makes no paid model calls.

## Release build

```bash
npm --prefix web ci
npm --prefix web run build
python -m build --wheel
python -m zipfile -l dist/verified_support_assistant-0.3.0-py3-none-any.whl
```

The wheel listing must include `support_assistant/static/index.html` and hashed
files below `support_assistant/static/assets/`. A release that omits nested
assets will return the SPA shell but fail in the browser.

## Local production process

```bash
python -m pip install dist/verified_support_assistant-0.3.0-py3-none-any.whl
LLM_BACKEND=extractive python -m uvicorn support_assistant.api:app \
  --host 0.0.0.0 --port 8000
curl --fail http://127.0.0.1:8000/health
```

Use a process manager or orchestrator to restart failed processes. Terminate TLS
at a trusted ingress, forward `X-Forwarded-*` headers only from that ingress,
and add authentication, rate limiting, audit retention, and abuse controls
before connecting real customer data or account actions.

## Container

```bash
docker build -t verified-support-assistant:0.3.0 .
docker run --rm -p 8000:8000 \
  -e LLM_BACKEND=extractive \
  verified-support-assistant:0.3.0
```

The Dockerfile compiles the frontend in a Node stage, installs the Python app
in a slim runtime stage, runs as a non-root user, and checks `/health`.

## CoreWeave Sandbox verification

Install optional tooling and request a time-bounded public endpoint:

```bash
python -m pip install -e ".[dev,sandbox]" build
python scripts/deploy_sandbox_demo.py --lifetime-minutes 120
```

The launcher builds the current React bundle and wheel, creates a 1 CPU / 2 GiB
Sandbox, uploads only the release bundle and verification scripts, starts
Uvicorn, checks `/health`, and writes `docs/live-demo/deployment.json` with the
HTTPS URL and hard expiry.

Public visibility depends on runner capability. If placement returns
`FAILED_PRECONDITION: requested service visibility is not supported`, run the
same artifact privately and execute Chromium inside the Sandbox:

```bash
python scripts/deploy_sandbox_demo.py \
  --lifetime-minutes 120 \
  --private-capture
```

This produces 40 screenshots, complete response JSON, accessibility and layout
checks, hashes, a CRC-tested ZIP, and `sandbox-capture.json`. It verifies the
release runtime but intentionally does not claim a public URL.

## Readiness and rollback

Before promoting a release:

1. `make check` and `npm --prefix web run build` pass from a clean checkout.
2. The wheel contains `static/assets` and installs in an empty environment.
3. `/health`, `/api/meta`, `/assistant`, and one `/api/ask` request succeed.
4. The 40-case browser manifest has `verification_pass: true`.
5. The evidence ZIP passes `python -m zipfile -t`.

Rollback by redeploying the previous immutable wheel or image tag. Do not copy
an older static directory over a newer backend: API and frontend contracts are
versioned and validated as one release.

## Secrets and optional services

- Never bake `WANDB_API_KEY` or provider credentials into the image or wheel.
- `LLM_BACKEND=inference` requires explicit W&B entity/project attribution and
  consumes credits; start with the bounded evaluation harness.
- `ENABLE_WEAVE=true` requires an explicit `WEAVE_PROJECT`.
- The synthetic demo has no authentication or persistence. It is not approved
  for real customer records without the controls listed above.