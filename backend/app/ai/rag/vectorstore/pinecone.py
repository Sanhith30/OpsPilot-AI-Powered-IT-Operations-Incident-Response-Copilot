from typing import Any

from pinecone import Pinecone

from app.ai.rag.embeddings.base import EmbeddingProvider
from app.ai.rag.schemas import (
    KnowledgeChunk,
    RetrievalResult,
)
from app.ai.rag.vectorstore.base import VectorStore
from app.core.config import settings


class PineconeVectorStore(VectorStore):

    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        if not settings.pinecone_api_key:
            raise ValueError(
                "PINECONE_API_KEY is required"
            )

        self.embedding_provider = embedding_provider
        self.client = Pinecone(
            api_key=settings.pinecone_api_key,
        )
        self.index = self.client.Index(
            settings.pinecone_index_name,
        )

    def add_chunks(
        self,
        chunks: list[KnowledgeChunk],
    ) -> None:
        if not chunks:
            return

        texts = [
            chunk.content for chunk in chunks
        ]
        vectors = self.embedding_provider.embed_documents(
            texts
        )

        records = []
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
            records.append(
                {
                    "id": chunk.chunk_id,
                    "values": vector,
                    "metadata": metadata,
                }
            )

        self.index.upsert(
            vectors=records,
            namespace=settings.pinecone_namespace,
        )

    def delete_document(
        self,
        document_id: str,
    ) -> None:
        self.index.delete(
            filter={
                "document_id": document_id,
            },
            namespace=settings.pinecone_namespace,
        )

    def delete_document_version(
        self,
        document_id: str,
        version_number: int,
    ) -> None:
        self.index.delete(
            filter={
                "document_id": document_id,
                "version_number": version_number,
            },
            namespace=settings.pinecone_namespace,
        )

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        score_threshold: float | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError(
                "Query text cannot be empty"
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be positive"
            )

        query_vector = self.embedding_provider.embed_query(
            query
        )

        response = self.index.query(
            namespace=settings.pinecone_namespace,
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=metadata_filter,
        )

        results: list[RetrievalResult] = []

        for match in response.matches:
            score = float(match.score or 0.0)

            if (
                score_threshold is not None
                and score < score_threshold
            ):
                continue

            metadata = dict(match.metadata or {})

            results.append(
                RetrievalResult(
                    chunk_id=str(match.id),
                    document_id=str(
                        metadata.get("document_id", "")
                    ),
                    content=str(
                        metadata.get("content", "")
                    ),
                    score=score,
                    metadata=metadata,
                )
            )

        return results
