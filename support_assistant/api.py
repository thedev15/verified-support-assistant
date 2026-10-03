from __future__ import annotations

import json
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from time import perf_counter

import weave
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import get_settings
from .evaluate import evaluate_detailed
from .knowledge import load_documents
from .models import (
    AskRequest,
    AskResponse,
    EvaluationReport,
    PolicyDetail,
    PolicySummary,
    RuntimeLinks,
    RuntimeMetadata,
)
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
        {
            "name": "assistant",
            "description": "Question answering with structured citations and streaming progress.",
        },
        {"name": "discovery", "description": "Runtime metadata and policy discovery."},
        {"name": "evaluation", "description": "Inspectable deterministic quality results."},
        {"name": "operations", "description": "Health and readiness information."},
    ],
)
if (STATIC_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    content_security_policy = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"
        if request.url.path in {"/docs", "/redoc"}
        else "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "font-src 'self' data:; "
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


def answer_question(question: str) -> AskResponse:
    started = perf_counter()
    response = service.answer(question)
    return response.model_copy(update={"latency_ms": round((perf_counter() - started) * 1000, 2)})


@app.post("/api/ask", response_model=AskResponse, tags=["assistant"])
@weave.op()
def ask(request: AskRequest) -> AskResponse:
    return answer_question(request.question)


def stream_answer(question: str) -> Iterator[str]:
    stages = (
        {"step": "validating", "message": "Checking request scope"},
        {"step": "retrieving", "message": "Ranking versioned policies"},
    )
    for stage in stages:
        yield f"event: stage\ndata: {json.dumps(stage)}\n\n"
    response = answer_question(question)
    yield f"event: result\ndata: {response.model_dump_json()}\n\n"


@app.post(
    "/api/ask/stream",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
    tags=["assistant"],
)
def ask_stream(request: AskRequest) -> StreamingResponse:
    return StreamingResponse(
        stream_answer(request.question),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-store"},
    )


@lru_cache(maxsize=1)
def current_evaluation() -> EvaluationReport:
    return evaluate_detailed(settings.evaluation_path, service)


@app.get("/api/meta", response_model=RuntimeMetadata, tags=["discovery"])
def metadata() -> RuntimeMetadata:
    evaluation = current_evaluation()
    return RuntimeMetadata(
        name="Verified Support Assistant",
        version=__version__,
        backend=settings.llm_backend,
        document_count=len(documents),
        evaluation_count=evaluation.metrics.examples,
        capabilities=[
            "citation-first answers",
            "streaming verification progress",
            "policy discovery",
            "safe refusal",
            "interactive evaluation results",
            "local conversation history",
            "optional Forge Inference",
            "optional Weave tracing",
        ],
        links=RuntimeLinks(
            assistant="/assistant",
            policies="/policies",
            evaluations="/evaluations",
            about="/about",
            openapi="/docs",
        ),
    )


def policy_summary(document) -> PolicySummary:
    excerpt = document.text[:180].strip()
    if len(document.text) > len(excerpt):
        excerpt += "…"
    return PolicySummary(
        document_id=document.id,
        title=document.title,
        source=document.source,
        excerpt=excerpt,
    )


@app.get("/api/policies", response_model=list[PolicySummary], tags=["discovery"])
def policy_catalog() -> list[PolicySummary]:
    return [policy_summary(document) for document in documents]


@app.get("/api/policies/{document_id}", response_model=PolicyDetail, tags=["discovery"])
def policy_detail(document_id: str) -> PolicyDetail:
    document = next((item for item in documents if item.id == document_id), None)
    if document is None:
        raise HTTPException(status_code=404, detail="Policy document not found")
    summary = policy_summary(document)
    return PolicyDetail(**summary.model_dump(), text=document.text)


@app.get("/api/evaluations/latest", response_model=EvaluationReport, tags=["evaluation"])
def latest_evaluation() -> EvaluationReport:
    return current_evaluation()


def frontend() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/", include_in_schema=False)
@app.get("/assistant", include_in_schema=False)
@app.get("/policies", include_in_schema=False)
@app.get("/policies/{document_id}", include_in_schema=False)
@app.get("/evaluations", include_in_schema=False)
@app.get("/about", include_in_schema=False)
def react_application(document_id: str | None = None) -> FileResponse:
    return frontend()
