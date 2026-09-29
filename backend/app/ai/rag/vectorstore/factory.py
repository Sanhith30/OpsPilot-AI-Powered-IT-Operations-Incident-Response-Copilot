from app.ai.rag.embeddings.factory import (
    create_embedding_provider,
)
from app.ai.rag.vectorstore.base import VectorStore
from app.ai.rag.vectorstore.mock import (
    MockVectorStore,
)
from app.ai.rag.vectorstore.pinecone import (
    PineconeVectorStore,
)
from app.core.config import settings


def create_vector_store(provider: str | None = None) -> VectorStore:
    selected_provider = (
        provider
        or getattr(settings, "vector_store_provider", None)
        or "pinecone"
    ).lower().strip()
    embedding_provider = create_embedding_provider()

    if selected_provider in ("mock", "test", "in_memory", "memory"):
        return MockVectorStore(
            embedding_provider=embedding_provider,
        )

    # In testing mode or when pinecone API key is absent, use mock store for deterministic CI testing
    if not settings.pinecone_api_key and settings.app_env in ("testing", "test"):
        return MockVectorStore(
            embedding_provider=embedding_provider,
        )

    return PineconeVectorStore(
        embedding_provider=embedding_provider,
    )

