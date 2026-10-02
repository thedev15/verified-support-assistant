from __future__ import annotations

import re

from .config import Settings
from .generation import generate_extractive, generate_with_inference
from .models import AskResponse, Citation
from .retrieval import TfidfRetriever


REFUSAL = "I don't have enough verified information to answer that."
CITATION_PATTERN = re.compile(r"\[([A-Z][A-Z0-9_-]+)\]")


ACCOUNT_OR_ACTION_PATTERNS = (
    r"\b(current location|where is my order|track my order|order\s*#?\s*\d+)\b",
    r"\b(what is|tell me|show me|recover)\s+(my\s+)?(account\s+)?(password|one-time code)\b",
    r"\b(place|submit|purchase|buy)\b.*\b(order|item)\b",
    r"\b(buy|purchase|submit|place|cancel)\b.*\b(for me|my account|order\s*#?\s*\d+)\b",
    r"\b(full card number|card security code|another customer'?s|other customer'?s)\b",
)

OUT_OF_SCOPE_PATTERNS = (
    r"\b(stock|share)\s+price\b",
    r"\b(football|basketball|baseball|championship)\b",
    r"\b(weather|political candidate|medical device|medical condition|malware)\b",
)

PROMPT_INJECTION_PATTERNS = (
    r"\b(ignore|override|bypass)\b.*\b(instructions|policies|rules|system|prompt)\b",
    r"\b(system prompt|developer message|jailbreak)\b",
)


def must_refuse_before_retrieval(question: str) -> bool:
    """Reject requests the policy-only demo cannot safely perform or answer."""
    patterns = ACCOUNT_OR_ACTION_PATTERNS + OUT_OF_SCOPE_PATTERNS + PROMPT_INJECTION_PATTERNS
    return any(re.search(pattern, question, flags=re.IGNORECASE) for pattern in patterns)


def normalize_generated_text(text: str, document_ids: list[str]) -> str:
    """Guarantee a usable answer or a safe refusal at the API boundary."""
    cleaned = text.strip()
    if not cleaned or cleaned == REFUSAL:
        return REFUSAL
    cited_ids = set(CITATION_PATTERN.findall(cleaned))
    if not cited_ids.intersection(document_ids):
        cleaned = f"{cleaned} [{document_ids[0]}]"
    return cleaned


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
                max_tokens=self.settings.inference_max_tokens,
                temperature=self.settings.inference_temperature,
            )
        else:
            raise ValueError(f"Unsupported LLM_BACKEND: {self.settings.llm_backend}")

        answer = normalize_generated_text(generated.text, [doc.id for doc in documents])
        refused = answer == REFUSAL
        citations = [
            Citation(
                document_id=doc.id,
                title=doc.title,
                source=doc.source,
                score=round(doc.score, 4),
            )
            for doc in documents
        ] if not refused else []
        return AskResponse(
            answer=answer,
            citations=citations,
            refused=refused,
            backend=self.settings.llm_backend,
            model=generated.model,
            finish_reason=generated.finish_reason,
            prompt_tokens=generated.prompt_tokens,
            completion_tokens=generated.completion_tokens,
        )