from pathlib import Path
from unittest.mock import MagicMock

import pytest
from app.ai.rag.ingestion.chunker import (
    KnowledgeChunker,
)
from app.ai.rag.ingestion.ids import (
    create_chunk_id,
    create_content_hash,
    create_document_id,
)
from app.ai.rag.ingestion.loader import (
    KnowledgeDocumentLoader,
)
from app.ai.rag.ingestion.normalizer import (
    KnowledgeDocumentNormalizer,
)
from app.ai.rag.ingestion.service import (
    KnowledgeIngestionService,
)
from app.ai.rag.schemas import KnowledgeDocument
from app.ai.rag.vectorstore.base import VectorStore


def test_document_loader(tmp_path: Path):
    file = tmp_path / "runbook.md"
    file.write_text(
        "# Payment API\n\nDatabase timeout runbook.",
        encoding="utf-8",
    )
    document = KnowledgeDocumentLoader().load_file(
        file
    )
    assert document.source_name == "runbook.md"
    assert "Payment API" in document.content


def test_document_loader_rejects_unsupported_type(
    tmp_path: Path,
):
    file = tmp_path / "runbook.pdf"
    file.write_bytes(b"test")
    with pytest.raises(ValueError):
        KnowledgeDocumentLoader().load_file(
            file
        )


def test_normalizer():
    document = {
        "document_id": "test",
        "source_type": "FILE",
        "source_name": "test.md",
        "title": "Test",
        "content": "hello \n\n\n\nworld ",
        "metadata": {},
    }
    result = KnowledgeDocumentNormalizer().normalize(
        KnowledgeDocument(**document)
    )
    assert result.content == "hello\n\nworld"


def test_chunking():
    document = KnowledgeDocument(
        document_id="doc-1",
        source_type="FILE",
        source_name="test.md",
        title="Test",
        content=("Payment API database timeout. " * 200),
        metadata={},
    )
    chunks = KnowledgeChunker(
        chunk_size=500,
        chunk_overlap=50,
    ).chunk(document, version_number=1)
    assert len(chunks) > 1
    assert all(
        chunk.document_id == "doc-1"
        for chunk in chunks
    )
    assert all(
        chunk.version_number == 1
        for chunk in chunks
    )
    assert [
        chunk.chunk_index for chunk in chunks
    ] == list(range(len(chunks)))


def test_document_id_is_deterministic():
    first = create_document_id(
        source_type="FILE",
        source_name="runbook.md",
    )
    second = create_document_id(
        source_type="FILE",
        source_name="runbook.md",
    )
    assert first == second


def test_content_hash_is_deterministic():
    first = create_content_hash("hello world")
    second = create_content_hash("hello world")
    assert first == second
    assert first != create_content_hash("hello world 2")


def test_chunk_id_is_deterministic():
    first = create_chunk_id(
        document_id="abc",
        version_number=1,
        chunk_index=0,
        content="hello",
    )
    second = create_chunk_id(
        document_id="abc",
        version_number=1,
        chunk_index=0,
        content="hello",
    )
    assert first == second
    assert "-v1-" in first


def test_ingestion_service_prepare_file(tmp_path: Path):
    file = tmp_path / "test-runbook.md"
    file.write_text("# Test Title\n\nRunbook content here.", encoding="utf-8")

    mock_store = MagicMock(spec=VectorStore)
    mock_doc_repo = MagicMock()
    mock_version_repo = MagicMock()
    mock_db = MagicMock()

    service = KnowledgeIngestionService(
        loader=KnowledgeDocumentLoader(),
        normalizer=KnowledgeDocumentNormalizer(),
        chunker=KnowledgeChunker(chunk_size=200, chunk_overlap=20),
        vector_store=mock_store,
        document_repository=mock_doc_repo,
        version_repository=mock_version_repo,
        db=mock_db,
    )

    doc = service.prepare_file(file)
    assert doc.source_name == "test-runbook.md"
    assert doc.document_id is not None
    assert doc.content_hash is not None
    assert "Runbook content here." in doc.content
