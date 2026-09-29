from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from app.ai.rag.schemas import RetrievalResult


class RerankingWeights(BaseModel):
    vector_weight: float = Field(default=1.0, ge=0.0, le=1.0)
    lexical_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    title_weight: float = Field(default=0.10, ge=0.0, le=1.0)


class RerankScoreBreakdown(BaseModel):
    vector_score: float
    lexical_score: float
    title_score: float
    final_score: float


class RerankRequest(BaseModel):
    query: str
    candidates: list[RetrievalResult]
    top_k: int = 5
