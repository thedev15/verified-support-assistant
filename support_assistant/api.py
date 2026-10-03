from __future__ import annotations

from html import escape
from pathlib import Path
from time import perf_counter

import weave
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import get_settings
from .knowledge import load_documents
from .models import AskRequest, AskResponse
from .retrieval import TfidfRetriever
from .service import SupportService

settings = get_settings()
documents = load_documents(settings.knowledge_path)
service = SupportService(TfidfRetriever(documents), settings)

if settings.enable_weave:
    weave.init(settings.weave_project)

STATIC_DIR = Path(__file__).parent / "static"
app = FastAPI(
    title="Verified Support Assistant",
    version=__version__,
    description=(
        "Citation-first support answers backed by a versioned policy corpus, "
        "with explicit safe refusal when evidence or authority is missing."
    ),
    contact={"name": "Verified Support Assistant maintainers"},
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "assistant", "description": "Question answering with structured citations."},
        {"name": "discovery", "description": "Runtime metadata and policy discovery."},
        {"name": "operations", "description": "Health and readiness information."},
    ],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    content_security_policy = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data:; "
        "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"
        if request.url.path in {"/docs", "/redoc"}
        else "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    )
    response.headers.setdefault("Content-Security-Policy", content_security_policy)
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.get("/health", tags=["operations"])
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "version": __version__,
        "documents": len(documents),
        "backend": settings.llm_backend,
    }


@app.post("/api/ask", response_model=AskResponse, tags=["assistant"])
@weave.op()
def ask(request: AskRequest) -> AskResponse:
    started = perf_counter()
    response = service.answer(request.question)
    return response.model_copy(update={"latency_ms": round((perf_counter() - started) * 1000, 2)})


@app.get("/api/meta", tags=["discovery"])
def metadata() -> dict[str, object]:
    return {
        "name": "Verified Support Assistant",
        "version": __version__,
        "backend": settings.llm_backend,
        "document_count": len(documents),
        "capabilities": [
            "citation-first answers",
            "policy discovery",
            "safe refusal",
            "optional Forge Inference",
            "optional Weave tracing",
        ],
        "links": {"about": "/about", "policies": "/policies", "openapi": "/docs"},
    }


@app.get("/api/policies", tags=["discovery"])
def policy_catalog() -> list[dict[str, str]]:
    return [
        {"document_id": document.id, "title": document.title, "source": document.source}
        for document in documents
    ]


@app.get("/policies", response_class=HTMLResponse, include_in_schema=False)
def policies() -> HTMLResponse:
    links = "".join(
        f'<li><a href="{escape(document.source)}"><strong>{escape(document.id)}</strong>'
        f"<span>{escape(document.title)}</span></a></li>"
        for document in documents
    )
    return HTMLResponse(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="theme-color" content="#08111f"><title>Policy library · Verified Support</title>'
        '<link rel="stylesheet" href="/static/app.css"></head><body>'
        '<a class="skip-link" href="#content">Skip to content</a>'
        '<main id="content" class="document-page"><a class="back-link" href="/">← Assistant</a>'
        '<p class="eyebrow">Versioned evidence</p><h1>Policy library</h1>'
        '<p class="lede">These synthetic documents are the complete evidence boundary for the demo.</p>'
        f'<ul class="policy-list">{links}</ul><footer class="page-footer">'
        '<a href="/about">About the project</a><a href="/docs">API docs</a>'
        "</footer></main></body></html>"
    )


@app.get("/policies/{document_id}", response_class=HTMLResponse, include_in_schema=False)
def policy(document_id: str) -> HTMLResponse:
    document = next((item for item in documents if item.id == document_id), None)
    if document is None:
        raise HTTPException(status_code=404, detail="Policy document not found")
    title = escape(document.title)
    body = escape(document.text)
    identifier = escape(document.id)
    return HTMLResponse(
        f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <meta name="theme-color" content="#08111f"><title>{identifier} · {title}</title>
        <link rel="stylesheet" href="/static/app.css"></head><body>
        <a class="skip-link" href="#content">Skip to content</a>
        <main id="content" class="document-page policy-document">
        <a class="back-link" href="/policies">← Policy library</a>
        <p class="eyebrow">Versioned support policy · {identifier}</p>
        <h1>{title}</h1><p class="policy-copy">{body}</p>
        <footer class="page-footer"><a href="/">Ask the assistant</a>
        <a href="/about">How verification works</a></footer></main></body></html>"""
    )


@app.get("/about", include_in_schema=False)
def about() -> FileResponse:
    return FileResponse(STATIC_DIR / "about.html")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
