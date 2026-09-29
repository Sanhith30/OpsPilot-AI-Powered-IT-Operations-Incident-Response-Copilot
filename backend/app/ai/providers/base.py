from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        metadata: dict[str, Any] | None = None,
        response_schema: type[BaseModel] | None = None,
    ) -> str:
        """
        Generate a response from the configured language model.
        """
        raise NotImplementedError
