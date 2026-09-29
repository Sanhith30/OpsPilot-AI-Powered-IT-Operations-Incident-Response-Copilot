from __future__ import annotations

from app.ai.rag.reranking.base import Reranker
from app.ai.rag.reranking.lexical import DeterministicLexicalReranker
from app.ai.rag.reranking.schemas import RerankingWeights
from app.ai.rag.reranking.service import RerankingService


def create_reranker(
    reranker_type: str = "lexical",
    weights: RerankingWeights | None = None,
) -> Reranker:
    """Factory creating configured Reranker instance."""
    if reranker_type in {"lexical", "deterministic_lexical"}:
        return DeterministicLexicalReranker(weights=weights)
    raise ValueError(f"Unknown reranker type: {reranker_type}")


def create_reranking_service(
    reranker_type: str = "lexical",
    weights: RerankingWeights | None = None,
) -> RerankingService:
    """Factory creating configured RerankingService instance."""
    reranker = create_reranker(reranker_type=reranker_type, weights=weights)
    return RerankingService(reranker=reranker)
