from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.ai.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        metadata: dict[str, Any] | None = None,
        response_schema: type[BaseModel] | None = None,
    ) -> str:
        return (
            "Mock investigation response. "
            "No external language model was called."
        )
