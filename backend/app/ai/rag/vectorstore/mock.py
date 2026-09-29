from __future__ import annotations

import math
from typing import Any

from app.ai.rag.embeddings.base import EmbeddingProvider
from app.ai.rag.schemas import KnowledgeChunk, RetrievalResult
from app.ai.rag.vectorstore.base import VectorStore


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class MockVectorStore(VectorStore):
    """In-memory deterministic mock vector store for testing and CI."""

    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.chunks: dict[str, dict[str, Any]] = {}

    def add_chunks(
        self,
        chunks: list[KnowledgeChunk],
    ) -> None:
        if not chunks:
            return

        texts = [chunk.content for chunk in chunks]
        vectors = self.embedding_provider.embed_documents(texts)

        for chunk, vector in zip(chunks, vectors):
            metadata = {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "version_number": (
                    chunk.version_number
                    if chunk.version_number is not None
                    else 0
                ),
                **chunk.metadata,
            }
            self.chunks[chunk.chunk_id] = {
                "id": chunk.chunk_id,
                "values": vector,
                "metadata": metadata,
            }

    def delete_document(
        self,
        document_id: str,
    ) -> None:
        self.chunks = {
            cid: record
            for cid, record in self.chunks.items()
            if str(record["metadata"].get("document_id")) != str(document_id)
        }

    def delete_document_version(
        self,
        document_id: str,
        version_number: int,
    ) -> None:
        self.chunks = {
            cid: record
            for cid, record in self.chunks.items()
            if not (
                str(record["metadata"].get("document_id")) == str(document_id)
                and record["metadata"].get("version_number") == version_number
            )
        }

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        score_threshold: float | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError("Query text cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        if not self.chunks:
            return []

        query_vector = self.embedding_provider.embed_query(query)
        scored_results: list[RetrievalResult] = []

        for cid, record in self.chunks.items():
            metadata = record["metadata"]

            if metadata_filter:
                match = True
                for k, v in metadata_filter.items():
                    if metadata.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            score = _cosine_similarity(query_vector, record["values"])

            if score_threshold is not None and score < score_threshold:
                continue

            scored_results.append(
                RetrievalResult(
                    chunk_id=str(cid),
                    document_id=str(metadata.get("document_id", "")),
                    content=str(metadata.get("content", "")),
                    score=float(score),
                    metadata=dict(metadata),
                )
            )

        scored_results.sort(key=lambda r: r.score, reverse=True)
        return scored_results[:top_k]


TestVectorStore = MockVectorStore
