from app.ai.rag.embeddings.factory import create_embedding_provider
from app.ai.rag.schemas import KnowledgeChunk, RetrievalResult
from app.ai.rag.vectorstore.base import VectorStore
from app.ai.rag.vectorstore.pinecone import PineconeVectorStore
from app.core.config import settings


class InMemoryVectorStore(VectorStore):
    def __init__(self, embedding_provider):
        self.embedding_provider = embedding_provider
        self.chunks: list[KnowledgeChunk] = []

    def add_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        self.chunks.extend(chunks)

    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.5) -> list[RetrievalResult]:
        results = []
        for i, chunk in enumerate(self.chunks[:top_k]):
            results.append(RetrievalResult(chunk=chunk, score=0.85, rank=i + 1))
        return results

    def delete(self, filter: dict) -> None:
        pass


def create_vector_store() -> VectorStore:
    embedding_provider = create_embedding_provider()

    if settings.pinecone_api_key:
        try:
            return PineconeVectorStore(
                embedding_provider=embedding_provider,
            )
        except Exception:
            pass

    return InMemoryVectorStore(embedding_provider=embedding_provider)
