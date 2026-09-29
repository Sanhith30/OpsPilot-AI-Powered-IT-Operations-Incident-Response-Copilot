from __future__ import annotations

from abc import ABC, abstractmethod
from app.ai.rag.schemas import RetrievalResult


class Reranker(ABC):
    """Abstract base class for RAG retrieval candidate rerankers."""

    @abstractmethod
    def rerank(
        self,
        *,
        query: str,
        candidates: list[RetrievalResult],
        top_k: int,
    ) -> list[RetrievalResult]:
        """
        Rerank candidate chunks based on relevance to query.
        Returns up to top_k reranked candidates with updated scores and provenance metadata.
        """
        ...
