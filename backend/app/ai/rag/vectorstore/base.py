from abc import ABC, abstractmethod
from typing import Any

from app.ai.rag.schemas import (
    KnowledgeChunk,
    RetrievalResult,
)


class VectorStore(ABC):

    @abstractmethod
    def add_chunks(
        self,
        chunks: list[KnowledgeChunk],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_document(
        self,
        document_id: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_document_version(
        self,
        document_id: str,
        version_number: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        score_threshold: float | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        raise NotImplementedError
