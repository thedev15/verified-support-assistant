from __future__ import annotations

from html import escape
from pathlib import Path

import weave
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

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
        <title>{identifier} · {title}</title><style>
        body{{margin:0;background:#08111f;color:#eaf0ff;font:16px/1.7 system-ui,sans-serif}}
        main{{max-width:760px;margin:7vh auto;padding:36px;border:1px solid #9bb0db2b;
        border-radius:20px;background:#101b2e}}a{{color:#70e0bd}}small{{color:#7f90ad}}
        h1{{line-height:1.15}}p{{white-space:pre-wrap;color:#c8d2e5}}
        </style></head><body><main><small>VERSIONED SUPPORT POLICY · {identifier}</small>
        <h1>{title}</h1><p>{body}</p><a href="/">← Back to Verified Support</a>
        </main></body></html>"""
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")
