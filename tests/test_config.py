from pathlib import Path

import pytest

from support_assistant.config import Settings


def test_default_settings_are_safe_and_local() -> None:
    settings = Settings(knowledge_path=Path("data/knowledge_base.json"))
    assert settings.llm_backend == "extractive"
    assert settings.enable_weave is False
    assert settings.top_k == 3


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("llm_backend", "unknown", "LLM_BACKEND"),
        ("top_k", 0, "TOP_K"),
        ("min_retrieval_score", 1.1, "MIN_RETRIEVAL_SCORE"),
        ("inference_max_tokens", 0, "INFERENCE_MAX_TOKENS"),
        ("inference_temperature", 2.1, "INFERENCE_TEMPERATURE"),
    ],
)
def test_invalid_settings_fail_fast(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        Settings(**{field: value})


def test_weave_requires_explicit_project() -> None:
    with pytest.raises(ValueError, match="WEAVE_PROJECT"):
        Settings(enable_weave=True, weave_project="")
