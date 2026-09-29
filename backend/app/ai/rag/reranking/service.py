from __future__ import annotations

import logging
from app.ai.rag.reranking.base import Reranker
from app.ai.rag.schemas import RetrievalResult
from app.observability.tracing import get_tracer

tracer = get_tracer("opspilot.rag.reranking")
logger = logging.getLogger(__name__)


class RerankingService:
    """Service orchestrating candidate reranking with observability."""

    def __init__(self, reranker: Reranker) -> None:
        self.reranker = reranker

    def rerank(
        self,
        *,
        query: str,
        candidates: list[RetrievalResult],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not candidates or top_k <= 0:
            return []

        with tracer.start_as_current_span("rag.rerank") as span:
            span.set_attribute("opspilot.rag.rerank.candidate_count", len(candidates))
            span.set_attribute("opspilot.rag.rerank.top_k", top_k)

            results = self.reranker.rerank(
                query=query,
                candidates=candidates,
                top_k=top_k,
            )

            span.set_attribute("opspilot.rag.rerank.output_count", len(results))
            return results
