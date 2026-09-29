from unittest.mock import MagicMock, patch

import pytest
from app.ai.rag.embeddings.base import EmbeddingProvider
from app.ai.rag.embeddings.factory import create_embedding_provider
from app.ai.rag.embeddings.gemini import GeminiEmbeddingProvider
from app.ai.rag.schemas import (
    KnowledgeChunk,
    KnowledgeDocument,
    RetrievalResult,
)
from app.ai.rag.vectorstore.base import VectorStore
from app.ai.rag.vectorstore.factory import create_vector_store
from app.ai.rag.vectorstore.pinecone import PineconeVectorStore


class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 1536):
        self._dim = dimension

    @property
    def model_name(self) -> str:
        return "mock-embedding"

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * self._dim for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * self._dim


def test_rag_schemas():
    doc = KnowledgeDocument(
        document_id="doc-1",
        source_type="RUNBOOK",
        source_name="postgres_troubleshooting.md",
        title="PostgreSQL Runbook",
        content="Check connections and locks",
        metadata={"category": "database"},
    )
    assert doc.document_id == "doc-1"
    assert doc.metadata["category"] == "database"

    chunk = KnowledgeChunk(
        chunk_id="doc-1-chunk-0",
        document_id="doc-1",
        content="Check connections",
        chunk_index=0,
        metadata={"tags": ["db"]},
    )
    assert chunk.chunk_id == "doc-1-chunk-0"
    assert chunk.chunk_index == 0

    res = RetrievalResult(
        chunk_id="doc-1-chunk-0",
        document_id="doc-1",
        content="Check connections",
        score=0.92,
        metadata={"tags": ["db"]},
    )
    assert res.score == 0.92


def test_gemini_embedding_provider_validation():
    with pytest.raises(ValueError, match="Gemini API key is required"):
        GeminiEmbeddingProvider(api_key="", model="gemini-embedding-2", dimension=1536)

    with pytest.raises(ValueError, match="Embedding dimension must be positive"):
        GeminiEmbeddingProvider(api_key="test-key", model="gemini-embedding-2", dimension=0)


def test_gemini_embedding_provider_embed_empty():
    provider = GeminiEmbeddingProvider(api_key="test-key", model="gemini-embedding-2", dimension=1536)
    assert provider.embed_documents([]) == []

    with pytest.raises(ValueError, match="Query text cannot be empty"):
        provider.embed_query("   ")


def test_gemini_embedding_provider_embed_documents():
    provider = GeminiEmbeddingProvider(api_key="test-key", model="gemini-embedding-2", dimension=3)
    mock_resp = MagicMock()
    mock_item1 = MagicMock()
    mock_item1.values = [0.1, 0.2, 0.3]
    mock_item2 = MagicMock()
    mock_item2.values = [0.4, 0.5, 0.6]
    mock_resp.embeddings = [mock_item1, mock_item2]

    provider._client.models.embed_content = MagicMock(return_value=mock_resp)

    vectors = provider.embed_documents(["doc1", "doc2"])
    assert len(vectors) == 2
    assert vectors[0] == [0.1, 0.2, 0.3]
    assert vectors[1] == [0.4, 0.5, 0.6]


def test_gemini_embedding_provider_embed_query():
    provider = GeminiEmbeddingProvider(api_key="test-key", model="gemini-embedding-2", dimension=3)
    mock_resp = MagicMock()
    mock_item = MagicMock()
    mock_item.values = [0.7, 0.8, 0.9]
    mock_resp.embeddings = [mock_item]

    provider._client.models.embed_content = MagicMock(return_value=mock_resp)

    vector = provider.embed_query("search query")
    assert vector == [0.7, 0.8, 0.9]


@patch("app.ai.rag.vectorstore.pinecone.Pinecone")
def test_pinecone_vector_store_operations(mock_pinecone_class, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.pinecone_api_key", "test-pinecone-key")
    monkeypatch.setattr("app.core.config.settings.pinecone_index_name", "opspilot-knowledge")
    monkeypatch.setattr("app.core.config.settings.pinecone_namespace", "opspilot")

    mock_client = MagicMock()
    mock_index = MagicMock()
    mock_client.Index.return_value = mock_index
    mock_pinecone_class.return_value = mock_client

    provider = MockEmbeddingProvider(dimension=4)
    store = PineconeVectorStore(embedding_provider=provider)

    chunks = [
        KnowledgeChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            content="Sample text",
            chunk_index=0,
            metadata={"source": "runbook"},
        )
    ]
    store.add_chunks(chunks)
    assert mock_index.upsert.called

    store.delete_document("doc-1")
    assert mock_index.delete.called

    # Test search with score threshold
    mock_match_high = MagicMock(
        id="chunk-1",
        score=0.88,
        metadata={"document_id": "doc-1", "content": "Sample text"},
    )
    mock_match_low = MagicMock(
        id="chunk-2",
        score=0.20,
        metadata={"document_id": "doc-2", "content": "Low score text"},
    )
    mock_query_resp = MagicMock()
    mock_query_resp.matches = [mock_match_high, mock_match_low]
    mock_index.query.return_value = mock_query_resp

    results = store.search("troubleshooting", top_k=5, score_threshold=0.35)
    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"
    assert results[0].score == 0.88


def test_factories(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.embedding_provider", "gemini")
    monkeypatch.setattr("app.core.config.settings.gemini_api_key", "test-gemini-key")
    monkeypatch.setattr("app.core.config.settings.embedding_dimensions", 1536)

    provider = create_embedding_provider()
    assert isinstance(provider, GeminiEmbeddingProvider)
    assert provider.dimension == 1536

    with patch("app.ai.rag.vectorstore.pinecone.Pinecone"):
        monkeypatch.setattr("app.core.config.settings.pinecone_api_key", "test-pinecone-key")
        store = create_vector_store()
        assert isinstance(store, VectorStore)

    monkeypatch.setattr("app.core.config.settings.embedding_provider", "mock")
    monkeypatch.setattr("app.core.config.settings.embedding_dimensions", 768)
    mock_provider = create_embedding_provider()
    from app.ai.rag.embeddings.mock import MockEmbeddingProvider
    assert isinstance(mock_provider, MockEmbeddingProvider)
    assert mock_provider.dimension == 768
    vec = mock_provider.embed_query("test query")
    assert len(vec) == 768
