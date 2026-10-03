from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Document, RetrievedDocument


def normalize_for_search(text: str) -> str:
    """Normalize a few operational-support paraphrases without an opaque model."""
    normalized = text.lower()
    replacements = {
        "one-day": "24 hours",
        "one day": "24 hours",
        "scanned": "scan",
        "scanning": "scan",
    }
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


class TfidfRetriever:
    """Small, inspectable retrieval baseline suitable for a portfolio demo."""

    def __init__(self, documents: list[Document]) -> None:
        self.documents = documents
        corpus = [f"{doc.title}. {doc.text}" for doc in documents]
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            preprocessor=normalize_for_search,
        )
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 3) -> list[RetrievedDocument]:
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).ravel()
        ranked_indices = scores.argsort()[::-1][:top_k]
        return [
            RetrievedDocument(**self.documents[index].model_dump(), score=float(scores[index]))
            for index in ranked_indices
            if scores[index] > 0
        ]
