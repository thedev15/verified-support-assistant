from __future__ import annotations

from pathlib import Path

import weave
from fastapi import FastAPI
from fastapi.responses import FileResponse

from .config import get_settings
from .knowledge import load_documents
from .models import AskRequest, AskResponse
from .retrieval import TfidfRetriever
from .service import SupportService


settings = get_settings()
documents = load_documents(settings.knowledge_path)
service = SupportService(TfidfRetriever(documents), settings)

if settings.enable_weave:
    if not settings.weave_project:
        raise RuntimeError("WEAVE_PROJECT is required when ENABLE_WEAVE=true")
    weave.init(settings.weave_project)

app = FastAPI(
    title="Verified Support Assistant",
    version="0.1.0",
    description="Citation-first support answers backed by a versioned policy corpus.",
)


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "documents": len(documents), "backend": settings.llm_backend}


@app.post("/api/ask", response_model=AskResponse)
@weave.op()
def ask(request: AskRequest) -> AskResponse:
    return service.answer(request.question)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")