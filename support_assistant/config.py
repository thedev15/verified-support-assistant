from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    knowledge_path: Path = Path(
        os.getenv("KNOWLEDGE_PATH", str(PROJECT_ROOT / "data" / "knowledge_base.json"))
    )
    evaluation_path: Path = Path(
        os.getenv("EVALUATION_PATH", str(PROJECT_ROOT / "data" / "eval_set.json"))
    )
    top_k: int = int(os.getenv("TOP_K", "3"))
    min_retrieval_score: float = float(os.getenv("MIN_RETRIEVAL_SCORE", "0.12"))
    llm_backend: str = os.getenv("LLM_BACKEND", "extractive")
    inference_model: str = os.getenv("INFERENCE_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    inference_base_url: str = os.getenv("INFERENCE_BASE_URL", "https://api.inference.wandb.ai/v1")
    inference_max_tokens: int = int(os.getenv("INFERENCE_MAX_TOKENS", "220"))
    inference_temperature: float = float(os.getenv("INFERENCE_TEMPERATURE", "0"))
    enable_weave: bool = os.getenv("ENABLE_WEAVE", "false").lower() == "true"
    weave_project: str = os.getenv("WEAVE_PROJECT", "")

    def __post_init__(self) -> None:
        if self.llm_backend not in {"extractive", "inference"}:
            raise ValueError("LLM_BACKEND must be 'extractive' or 'inference'")
        if self.top_k < 1:
            raise ValueError("TOP_K must be at least 1")
        if not 0 <= self.min_retrieval_score <= 1:
            raise ValueError("MIN_RETRIEVAL_SCORE must be between 0 and 1")
        if self.inference_max_tokens < 1:
            raise ValueError("INFERENCE_MAX_TOKENS must be at least 1")
        if not 0 <= self.inference_temperature <= 2:
            raise ValueError("INFERENCE_TEMPERATURE must be between 0 and 2")
        if self.enable_weave and not self.weave_project:
            raise ValueError("WEAVE_PROJECT is required when ENABLE_WEAVE=true")


def get_settings() -> Settings:
    return Settings()
