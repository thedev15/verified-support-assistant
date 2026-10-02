from __future__ import annotations

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str
    title: str
    source: str
    text: str


class RetrievedDocument(Document):
    score: float = Field(ge=0.0, le=1.0)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)


class Citation(BaseModel):
    document_id: str
    title: str
    source: str
    score: float


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    refused: bool
    backend: str
    model: str | None = None
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None