from __future__ import annotations

import re
from typing import Any

from app.ai.rag.reranking.base import Reranker
from app.ai.rag.reranking.schemas import RerankingWeights
from app.ai.rag.schemas import RetrievalResult

DEFAULT_STOP_WORDS = {
    "a",
    "an",
    "the",
    "in",
    "on",
    "at",
    "to",
    "for",
    "with",
    "by",
    "of",
    "from",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "it",
    "this",
    "that",
    "these",
    "those",
    "how",
    "what",
    "where",
    "when",
    "why",
    "which",
    "who",
    "and",
    "or",
    "but",
    "not",
    "can",
    "could",
    "do",
    "does",
    "did",
    "md",
}

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


def tokenize(text: str) -> list[str]:
    """Tokenize string into lowercase alphanumeric tokens."""
    return TOKEN_PATTERN.findall(text.lower())


def extract_meaningful_tokens(
    text: str,
    stop_words: set[str] = DEFAULT_STOP_WORDS,
) -> set[str]:
    """Extract unique lowercase tokens excluding stop words."""
    tokens = tokenize(text)
    meaningful = {t for t in tokens if t not in stop_words and len(t) > 1}
    return meaningful if meaningful else set(tokens)


class DeterministicLexicalReranker(Reranker):
    """
    Deterministic reranker combining:
    - Vector similarity score
    - Query-term overlap against chunk text
    - Title / source-name match
    """

    def __init__(
        self,
        weights: RerankingWeights | None = None,
        stop_words: set[str] | None = None,
    ) -> None:
        self.weights = weights or RerankingWeights()
        self.stop_words = stop_words if stop_words is not None else DEFAULT_STOP_WORDS

    def _calculate_lexical_score(
        self,
        query_terms: set[str],
        content: str,
    ) -> float:
        if not query_terms:
            return 0.0

        content_lower = content.lower()
        content_tokens = set(tokenize(content_lower))

        overlap = len(query_terms & content_tokens) / len(query_terms)

        # Occurrence density
        freq_count = sum(content_lower.count(term) for term in query_terms)
        norm_freq = min(freq_count / (len(query_terms) * 2), 1.0)

        return round(0.7 * overlap + 0.3 * norm_freq, 4)

    def _calculate_title_score(
        self,
        query_terms: set[str],
        metadata: dict[str, Any],
        document_id: str,
    ) -> float:
        if not query_terms:
            return 0.0

        title_parts: list[str] = []
        if metadata.get("source_name"):
            title_parts.append(str(metadata["source_name"]))
        if metadata.get("title"):
            title_parts.append(str(metadata["title"]))
        if document_id:
            title_parts.append(document_id)

        title_text = " ".join(title_parts)
        title_tokens = set(tokenize(title_text))

        if not title_tokens:
            return 0.0

        overlap = len(query_terms & title_tokens) / len(query_terms)
        return round(overlap, 4)

    def rerank(
        self,
        *,
        query: str,
        candidates: list[RetrievalResult],
        top_k: int,
    ) -> list[RetrievalResult]:
        if not candidates or top_k <= 0:
            return []

        query_terms = extract_meaningful_tokens(query, self.stop_words)

        reranked_list: list[RetrievalResult] = []

        for candidate in candidates:
            vector_score = float(candidate.score)
            lexical_score = self._calculate_lexical_score(
                query_terms, candidate.content
            )
            title_score = self._calculate_title_score(
                query_terms, candidate.metadata, candidate.document_id
            )

            final_score = (
                self.weights.vector_weight * vector_score
                + self.weights.lexical_weight * lexical_score
                + self.weights.title_weight * title_score
            )
            final_score = min(max(round(final_score, 4), 0.0), 1.0)

            updated_metadata = dict(candidate.metadata)
            updated_metadata["original_vector_score"] = round(vector_score, 4)
            updated_metadata["lexical_score"] = lexical_score
            updated_metadata["title_match_score"] = title_score
            updated_metadata["rerank_score"] = final_score
            updated_metadata["reranker"] = "deterministic_lexical"

            reranked_candidate = RetrievalResult(
                chunk_id=candidate.chunk_id,
                document_id=candidate.document_id,
                content=candidate.content,
                score=final_score,
                metadata=updated_metadata,
            )
            reranked_list.append(reranked_candidate)

        # Sort descending by final rerank score, breaking ties with original vector score
        reranked_list.sort(
            key=lambda r: (
                r.score,
                r.metadata.get("original_vector_score", 0.0),
            ),
            reverse=True,
        )

        return reranked_list[:top_k]
