from __future__ import annotations

from app.ai.providers.base import LLMProvider
from app.ai.providers.config import LLMConfig
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.mock import MockLLMProvider


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    if config.provider == "mock":
        return MockLLMProvider()

    if config.provider == "gemini":
        return GeminiProvider(config)

    raise ValueError(
        f"Unsupported LLM provider: {config.provider}"
    )
