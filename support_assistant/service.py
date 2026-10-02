from __future__ import annotations

import re

from .config import Settings
from .generation import generate_extractive, generate_with_inference
from .models import AskResponse, Citation
from .retrieval import TfidfRetriever


REFUSAL = "I don't have enough verified information to answer that."


ACCOUNT_OR_ACTION_PATTERNS = (
    r"\b(current location|where is my order|track my order|order\s*#?\s*\d+)\b",
    r"\b(what is|tell me|show me|recover)\s+(my\s+)?(account\s+)?(password|one-time code)\b",
    r"\b(place|submit|purchase|buy)\b.*\b(order|item)\b",
)

OUT_OF_SCOPE_PATTERNS = (
    r"\b(stock|share)\s+price\b",
    r"\b(football|basketball|baseball|championship)\b",
)


def must_refuse_before_retrieval(question: str) -> bool:
    """Reject requests the policy-only demo cannot safely perform or answer."""
    patterns = ACCOUNT_OR_ACTION_PATTERNS + OUT_OF_SCOPE_PATTERNS
    return any(re.search(pattern, question, flags=re.IGNORECASE) for pattern in patterns)


class SupportService:
    def __init__(self, retriever: TfidfRetriever, settings: Settings) -> None:
        self.retriever = retriever
        self.settings = settings

    def answer(self, question: str) -> AskResponse:
        if must_refuse_before_retrieval(question):
            return AskResponse(
                answer=REFUSAL,
                citations=[],
                refused=True,
                backend=self.settings.llm_backend,
            )
        documents = self.retriever.search(question, top_k=self.settings.top_k)
        if not documents or documents[0].score < self.settings.min_retrieval_score:
            return AskResponse(
                answer=REFUSAL,
                citations=[],
                refused=True,
                backend=self.settings.llm_backend,
            )

        if self.settings.llm_backend == "extractive":
            generated = generate_extractive(documents)
        elif self.settings.llm_backend == "inference":
            generated = generate_with_inference(
                question=question,
                documents=documents,
                model=self.settings.inference_model,
                base_url=self.settings.inference_base_url,
            )
        else:
            raise ValueError(f"Unsupported LLM_BACKEND: {self.settings.llm_backend}")

        citations = [
            Citation(
                document_id=doc.id,
                title=doc.title,
                source=doc.source,
                score=round(doc.score, 4),
            )
            for doc in documents
        ]
        return AskResponse(
            answer=generated.text,
            citations=citations,
            refused=generated.text.strip() == REFUSAL,
            backend=self.settings.llm_backend,
            model=generated.model,
            prompt_tokens=generated.prompt_tokens,
            completion_tokens=generated.completion_tokens,
        )