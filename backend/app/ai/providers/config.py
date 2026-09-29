from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr


class LLMConfig(BaseModel):
    provider: str = Field(
        default="mock",
        min_length=1,
    )

    model: str = Field(
        default="mock-model",
        min_length=1,
    )

    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
    )

    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
    )

    api_key: SecretStr | None = None

