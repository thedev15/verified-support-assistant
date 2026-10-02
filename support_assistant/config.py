from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    knowledge_path: Path = Path(os.getenv("KNOWLEDGE_PATH", "data/knowledge_base.json"))
    top_k: int = int(os.getenv("TOP_K", "3"))
    min_retrieval_score: float = float(os.getenv("MIN_RETRIEVAL_SCORE", "0.12"))
    llm_backend: str = os.getenv("LLM_BACKEND", "extractive")
    inference_model: str = os.getenv(
        "INFERENCE_MODEL", "meta-llama/Llama-3.1-8B-Instruct"
    )
    inference_base_url: str = os.getenv(
        "INFERENCE_BASE_URL", "https://api.inference.wandb.ai/v1"
    )
    inference_max_tokens: int = int(os.getenv("INFERENCE_MAX_TOKENS", "220"))
    inference_temperature: float = float(os.getenv("INFERENCE_TEMPERATURE", "0"))
    enable_weave: bool = os.getenv("ENABLE_WEAVE", "false").lower() == "true"
    weave_project: str = os.getenv("WEAVE_PROJECT", "")


def get_settings() -> Settings:
    return Settings()