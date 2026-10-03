# Local development guide

This guide covers the tools, setup, commands, and troubleshooting needed to run
Verified Support Assistant (VSA) on a developer workstation. The default
extractive backend is deterministic and makes no paid model calls.

## Required tools

| Tool | Supported version | Purpose |
|---|---|---|
| Git | current maintained release | Clone and contribute |
| Python | 3.11 or newer | Application and tests |
| `venv` and `pip` | bundled with Python | Isolated dependencies |

Recommended but optional:

- **GNU Make** for short commands such as `make check` and `make run`.
- **Docker** for a production-style, non-root container run.
- **Chromium via Playwright** only when regenerating browser evidence.
- **CoreWeave Sandbox SDK** only when reproducing the bounded Sandbox capture.

Node.js, npm, a database, and a frontend build system are not required. The
browser application uses standards-based HTML, CSS, and JavaScript served by
FastAPI.

## 1. Clone and create an environment

macOS or Linux:

```bash
git clone https://github.com/thedev15/verified-support-assistant.git
cd verified-support-assistant
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
git clone https://github.com/thedev15/verified-support-assistant.git
Set-Location verified-support-assistant
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If `make` is available, `make setup` performs the editable installation.

## 2. Configure the app

No configuration is required for the safe local default. Optionally copy the
documented values:

```bash
cp .env.example .env
```

The application intentionally does **not** auto-load `.env`; production and
test behavior should not depend on an unobserved local file. To load it in a
POSIX shell:

```bash
set -a
source .env
set +a
```

Do not commit `.env` or real credentials. The most important settings are:

| Variable | Default | Meaning |
|---|---|---|
| `LLM_BACKEND` | `extractive` | `extractive` or `inference` |
| `KNOWLEDGE_PATH` | `data/knowledge_base.json` | Versioned policy corpus |
| `TOP_K` | `3` | Retrieved candidates |
| `MIN_RETRIEVAL_SCORE` | `0.12` | Minimum answer threshold |
| `ENABLE_WEAVE` | `false` | Enable optional tracing |
| `WEAVE_PROJECT` | empty | Required when tracing is enabled |

Invalid values fail at startup rather than silently changing behavior.

## 3. Run the quality gates

```bash
make check
```

Equivalent commands without Make:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m support_assistant.evaluate
```

The deterministic evaluation must retain 100% retrieval accuracy, refusal
accuracy, and required-keyword coverage on the versioned 40-case benchmark.

## 4. Start the application

```bash
make run
```

Or directly:

```bash
python -m uvicorn support_assistant.api:app --reload --host 127.0.0.1 --port 8000
```

Open:

- Application: <http://127.0.0.1:8000>
- About: <http://127.0.0.1:8000/about>
- Policy library: <http://127.0.0.1:8000/policies>
- OpenAPI: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/health>

Binding to `127.0.0.1` keeps the development server local. Use `make
run-public` only on a trusted network and only when another device must connect.

## Docker

```bash
make docker-build
make docker-run
```

The image runs as a non-root user and includes a health check. Verify it with:

```bash
curl --fail http://127.0.0.1:8000/health
```

## Browser evidence

Install Chromium once:

```bash
make browser
```

With VSA running in another terminal:

```bash
make capture
```

The capture submits all 40 questions through the visible form and fails unless
the rendered results, cited documents, safe refusals, screenshot uniqueness,
and ZIP integrity pass. It rewrites `docs/live-demo/`; review those generated
files before committing them.

## Optional CoreWeave Sandbox capture

```bash
python -m pip install -e ".[dev,sandbox]"
python scripts/deploy_sandbox_demo.py --lifetime-minutes 90 --private-capture
```

This requires W&B-authenticated Sandbox access. The script provisions bounded
CPU/memory, runs Chromium inside the Sandbox, copies the verified evidence ZIP
back, and records capture provenance. It stops failed Sandboxes automatically;
stop successful temporary Sandboxes after retrieval to avoid unnecessary use.

## Optional Forge Inference and Weave

Inference consumes credits. Set `LLM_BACKEND=inference`, supply an approved W&B
credential and explicit entity/project, then run a bounded evaluation before
interactive use. For tracing, set `ENABLE_WEAVE=true` and an explicit
`WEAVE_PROJECT`. Do not trace customer data without an approved data policy.

## Troubleshooting

- **`ModuleNotFoundError`** — activate `.venv` and rerun `python -m pip install
  -e ".[dev]"`.
- **Knowledge file not found** — run from the repository root or set an
  absolute `KNOWLEDGE_PATH`.
- **Port 8000 already used** — run `make run PORT=8080`.
- **Browser capture cannot launch** — run `python -m playwright install
  chromium`; Linux may require Playwright's documented system dependencies.
- **Inference authentication fails** — verify W&B login, entity/project access,
  and the exact catalog model ID; never paste credentials into source files.
- **Tracing fails at startup** — set `WEAVE_PROJECT=entity/project` or disable
  tracing with `ENABLE_WEAVE=false`.