from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Document(BaseModel):
    id: str
    title: str
    source: str
    text: str


class RetrievedDocument(Document):
    score: float = Field(ge=0.0, le=1.0)


class AskRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(min_length=3, max_length=2_000)

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        if not any(character.isalnum() for character in value):
            raise ValueError("question must contain letters or numbers")
        return value


class Citation(BaseModel):
    document_id: str
    title: str
    source: str
    score: float


class AskResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: uuid4().hex)
    latency_ms: float = Field(default=0, ge=0)
    answer: str
    citations: list[Citation]
    refused: bool
    backend: str
    model: str | None = None
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
