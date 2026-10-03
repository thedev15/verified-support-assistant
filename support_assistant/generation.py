from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI

from .models import RetrievedDocument

SYSTEM_PROMPT = """You are a careful e-commerce support assistant.
Answer only from the supplied policy excerpts. Do not use outside knowledge.
If the excerpts do not establish the answer, say exactly:
I don't have enough verified information to answer that.
Keep the answer concise and cite supporting excerpts with [DOC_ID].
Never claim to have accessed an order, account, payment, or shipment.
"""


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model: str | None = None
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


def build_context(documents: list[RetrievedDocument]) -> str:
    return "\n\n".join(
        f"[{doc.id}] {doc.title}\nSource: {doc.source}\n{doc.text}" for doc in documents
    )


def generate_extractive(documents: list[RetrievedDocument]) -> GenerationResult:
    primary = documents[0]
    return GenerationResult(text=f"{primary.text} [{primary.id}]")


def generate_with_inference(
    question: str,
    documents: list[RetrievedDocument],
    model: str,
    base_url: str,
    max_tokens: int,
    temperature: float,
) -> GenerationResult:
    api_key = os.environ.get("WANDB_API_KEY")
    if not api_key:
        raise RuntimeError("WANDB_API_KEY is required for the inference backend")

    entity = os.environ.get("WANDB_ENTITY")
    project = os.environ.get("WANDB_PROJECT")
    client_args: dict[str, object] = {
        "base_url": base_url,
        "api_key": api_key,
        "max_retries": 0,
        "timeout": 60.0,
    }
    if entity and project:
        client_args["project"] = f"{entity}/{project}"
    client = OpenAI(**client_args)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Verified excerpts:\n{build_context(documents)}\n\nQuestion: {question}",
            },
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    usage = response.usage
    return GenerationResult(
        text=response.choices[0].message.content or "",
        model=response.model,
        finish_reason=response.choices[0].finish_reason,
        prompt_tokens=usage.prompt_tokens if usage else None,
        completion_tokens=usage.completion_tokens if usage else None,
    )
