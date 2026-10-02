from __future__ import annotations

import json
from pathlib import Path

from .models import Document


def load_documents(path: Path) -> list[Document]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    documents = [Document.model_validate(item) for item in payload["documents"]]
    if not documents:
        raise ValueError("Knowledge base must contain at least one document")
    ids = [document.id for document in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("Knowledge-base document IDs must be unique")
    return documents