from app.ai.rag.embeddings.factory import (
    create_embedding_provider,
)
from app.ai.rag.vectorstore.base import VectorStore
from app.ai.rag.vectorstore.pinecone import (
    PineconeVectorStore,
)


def create_vector_store() -> VectorStore:
    embedding_provider = create_embedding_provider()

    return PineconeVectorStore(
        embedding_provider=embedding_provider,
    )
