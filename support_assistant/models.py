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


class RuntimeLinks(BaseModel):
    assistant: str
    policies: str
    evaluations: str
    about: str
    openapi: str


class RuntimeMetadata(BaseModel):
    name: str
    version: str
    backend: str
    document_count: int = Field(ge=0)
    evaluation_count: int = Field(ge=0)
    capabilities: list[str]
    links: RuntimeLinks


class PolicySummary(BaseModel):
    document_id: str
    title: str
    source: str
    excerpt: str


class PolicyDetail(PolicySummary):
    text: str


class EvaluationMetrics(BaseModel):
    examples: int = Field(ge=0)
    retrieval_accuracy: float = Field(ge=0, le=1)
    refusal_accuracy: float = Field(ge=0, le=1)
    keyword_coverage: float = Field(ge=0, le=1)


class EvaluationCase(BaseModel):
    case: int = Field(ge=1)
    question: str
    expected_answerable: bool
    observed_refused: bool
    expected_document_id: str | None
    observed_citation_ids: list[str]
    retrieval_correct: bool
    refusal_correct: bool
    keyword_coverage: float = Field(ge=0, le=1)
    answer: str
    passed: bool


class EvaluationReport(BaseModel):
    dataset_version: str
    metrics: EvaluationMetrics
    passed_cases: int = Field(ge=0)
    failed_cases: int = Field(ge=0)
    cases: list[EvaluationCase]
