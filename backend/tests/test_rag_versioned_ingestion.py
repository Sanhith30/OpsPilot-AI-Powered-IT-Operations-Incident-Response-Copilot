from pathlib import Path
from unittest.mock import MagicMock

import pytest
from app.ai.rag.ingestion.chunker import (
    KnowledgeChunker,
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
from app.ai.rag.vectorstore.base import VectorStore
from app.repositories.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)
from app.repositories.knowledge_document_version_repository import (
    KnowledgeDocumentVersionRepository,
)


@pytest.fixture
def mock_vector_store():
    store = MagicMock(spec=VectorStore)
    provider = MagicMock()
    provider.model_name = "gemini-embedding-2"
    provider.dimension = 1536
    store.embedding_provider = provider
    return store


@pytest.fixture
def ingestion_service(db_session, mock_vector_store):
    doc_repo = KnowledgeDocumentRepository(db_session)
    version_repo = KnowledgeDocumentVersionRepository(db_session)
    return KnowledgeIngestionService(
        loader=KnowledgeDocumentLoader(),
        normalizer=KnowledgeDocumentNormalizer(),
        chunker=KnowledgeChunker(chunk_size=500, chunk_overlap=50),
        vector_store=mock_vector_store,
        document_repository=doc_repo,
        version_repository=version_repo,
        db=db_session,
    )


def test_new_document_creates_version_1(
    tmp_path: Path,
    ingestion_service: KnowledgeIngestionService,
    db_session,
):
    file = tmp_path / "payment_runbook.md"
    file.write_text("# Payment Runbook\n\nInitial version 1 content.", encoding="utf-8")

    result = ingestion_service.ingest_file(file, source_type="RUNBOOK")

    assert result["status"] == "INGESTED"
    assert result["version_number"] == 1
    assert result["chunk_count"] >= 1

    doc_repo = KnowledgeDocumentRepository(db_session)
    version_repo = KnowledgeDocumentVersionRepository(db_session)

    doc = doc_repo.get_by_id(result["document_id"])
    assert doc is not None
    assert doc.current_version_id == result["version_id"]

    version = version_repo.get_by_id(result["version_id"])
    assert version is not None
    assert version.version_number == 1
    assert version.ingestion_status == "COMPLETED"


def test_same_document_same_content_returns_unchanged(
    tmp_path: Path,
    ingestion_service: KnowledgeIngestionService,
    mock_vector_store: MagicMock,
):
    file = tmp_path / "unchanged_runbook.md"
    file.write_text("# Unchanged Runbook\n\nContent does not change.", encoding="utf-8")

    first_result = ingestion_service.ingest_file(file, source_type="RUNBOOK")
    assert first_result["status"] == "INGESTED"
    assert mock_vector_store.add_chunks.call_count == 1

    # Ingest again with identical content
    second_result = ingestion_service.ingest_file(file, source_type="RUNBOOK")
    assert second_result["status"] == "UNCHANGED"
    assert second_result["version_id"] == first_result["version_id"]
    assert second_result["version_number"] == 1
    # Pinecone upsert should not be called again
    assert mock_vector_store.add_chunks.call_count == 1


def test_modified_content_creates_version_2(
    tmp_path: Path,
    ingestion_service: KnowledgeIngestionService,
):
    file = tmp_path / "evolving_runbook.md"
    file.write_text("# Evolving\n\nOriginal text.", encoding="utf-8")

    v1_result = ingestion_service.ingest_file(file, source_type="RUNBOOK")
    assert v1_result["version_number"] == 1

    file.write_text("# Evolving\n\nUpdated text for revision 2.", encoding="utf-8")
    v2_result = ingestion_service.ingest_file(file, source_type="RUNBOOK")

    assert v2_result["status"] == "INGESTED"
    assert v2_result["version_number"] == 2
    assert v2_result["version_id"] != v1_result["version_id"]


def test_version_2_gets_different_chunk_ids(
    tmp_path: Path,
    ingestion_service: KnowledgeIngestionService,
    mock_vector_store: MagicMock,
):
    file = tmp_path / "chunk_id_test.md"
    file.write_text("# Runbook\n\nContent v1.", encoding="utf-8")

    ingestion_service.ingest_file(file, source_type="RUNBOOK")
    v1_chunks = mock_vector_store.add_chunks.call_args_list[0][0][0]
    v1_ids = [c.chunk_id for c in v1_chunks]

    file.write_text("# Runbook\n\nContent v2 modified.", encoding="utf-8")
    ingestion_service.ingest_file(file, source_type="RUNBOOK")
    v2_chunks = mock_vector_store.add_chunks.call_args_list[1][0][0]
    v2_ids = [c.chunk_id for c in v2_chunks]

    assert all("-v1-" in cid for cid in v1_ids)
    assert all("-v2-" in cid for cid in v2_ids)
    assert set(v1_ids).isdisjoint(set(v2_ids))


def test_version_1_remains_in_postgresql(
    tmp_path: Path,
    ingestion_service: KnowledgeIngestionService,
    db_session,
):
    file = tmp_path / "retention_runbook.md"
    file.write_text("# Retention\n\nVersion 1 text.", encoding="utf-8")
    v1 = ingestion_service.ingest_file(file, source_type="RUNBOOK")

    file.write_text("# Retention\n\nVersion 2 revised text.", encoding="utf-8")
    v2 = ingestion_service.ingest_file(file, source_type="RUNBOOK")

    version_repo = KnowledgeDocumentVersionRepository(db_session)
    versions = version_repo.get_versions(v1["document_id"])

    assert len(versions) == 2
    version_numbers = [v.version_number for v in versions]
    assert version_numbers == [2, 1]

    v1_db = version_repo.get_by_id(v1["version_id"])
    assert v1_db is not None
    assert "Version 1 text" in v1_db.content


def test_current_version_id_points_to_version_2(
    tmp_path: Path,
    ingestion_service: KnowledgeIngestionService,
    db_session,
):
    file = tmp_path / "pointer_runbook.md"
    file.write_text("# Pointer\n\nInitial version.", encoding="utf-8")
    ingestion_service.ingest_file(file, source_type="RUNBOOK")

    file.write_text("# Pointer\n\nSecond version content.", encoding="utf-8")
    v2 = ingestion_service.ingest_file(file, source_type="RUNBOOK")

    doc_repo = KnowledgeDocumentRepository(db_session)
    doc = doc_repo.get_by_id(v2["document_id"])
    assert doc is not None
    assert doc.current_version_id == v2["version_id"]


def test_pinecone_receives_version_2_metadata(
    tmp_path: Path,
    ingestion_service: KnowledgeIngestionService,
    mock_vector_store: MagicMock,
):
    file = tmp_path / "metadata_runbook.md"
    file.write_text("# Metadata\n\nVersion 1.", encoding="utf-8")
    ingestion_service.ingest_file(file, source_type="RUNBOOK")

    file.write_text("# Metadata\n\nVersion 2 content.", encoding="utf-8")
    ingestion_service.ingest_file(file, source_type="RUNBOOK")

    # Second call to add_chunks is for v2
    v2_chunks = mock_vector_store.add_chunks.call_args_list[1][0][0]
    for chunk in v2_chunks:
        assert chunk.version_number == 2
        assert chunk.metadata["version_number"] == 2


def test_pinecone_failure_marks_version_failed(
    tmp_path: Path,
    ingestion_service: KnowledgeIngestionService,
    mock_vector_store: MagicMock,
    db_session,
):
    file = tmp_path / "fail_runbook.md"
    file.write_text("# Fail Runbook\n\nWill fail during Pinecone sync.", encoding="utf-8")

    mock_vector_store.add_chunks.side_effect = RuntimeError("Pinecone network timeout")

    with pytest.raises(RuntimeError, match="Pinecone network timeout"):
        ingestion_service.ingest_file(file, source_type="RUNBOOK")

    version_repo = KnowledgeDocumentVersionRepository(db_session)
    # The document was flushed, find its version
    doc_repo = KnowledgeDocumentRepository(db_session)
    doc = doc_repo.get_by_source(
        source_type="RUNBOOK",
        source_name="fail_runbook.md",
    )
    assert doc is not None

    latest_version = version_repo.get_latest(doc.document_id)
    assert latest_version is not None
    assert latest_version.ingestion_status == "FAILED"
    assert "Pinecone network timeout" in (latest_version.ingestion_error or "")


def test_pinecone_failure_keeps_previous_current_version(
    tmp_path: Path,
    ingestion_service: KnowledgeIngestionService,
    mock_vector_store: MagicMock,
    db_session,
):
    file = tmp_path / "stable_runbook.md"
    file.write_text("# Stable\n\nGood v1 content.", encoding="utf-8")
    v1 = ingestion_service.ingest_file(file, source_type="RUNBOOK")

    doc_repo = KnowledgeDocumentRepository(db_session)
    doc = doc_repo.get_by_id(v1["document_id"])
    assert doc.current_version_id == v1["version_id"]

    # Now make Pinecone fail on v2
    file.write_text("# Stable\n\nCorrupt v2 content.", encoding="utf-8")
    mock_vector_store.add_chunks.side_effect = RuntimeError("Pinecone unavailable")

    with pytest.raises(RuntimeError, match="Pinecone unavailable"):
        ingestion_service.ingest_file(file, source_type="RUNBOOK")

    # Refresh doc from db
    db_session.expire_all()
    doc = doc_repo.get_by_id(v1["document_id"])
    assert doc.current_version_id == v1["version_id"]

    version_repo = KnowledgeDocumentVersionRepository(db_session)
    versions = version_repo.get_versions(doc.document_id)
    assert len(versions) == 2
    v2_db = versions[0]  # latest number first
    assert v2_db.version_number == 2
    assert v2_db.ingestion_status == "FAILED"


def test_old_vector_cleanup_failure_leaves_new_version_completed(
    tmp_path: Path,
    ingestion_service: KnowledgeIngestionService,
    mock_vector_store: MagicMock,
    db_session,
):
    file = tmp_path / "cleanup_runbook.md"
    file.write_text("# Cleanup\n\nInitial version 1.", encoding="utf-8")
    ingestion_service.ingest_file(file, source_type="RUNBOOK")

    # Make old vector cleanup fail
    mock_vector_store.delete_document_version.side_effect = Exception("Pinecone delete failed")

    file.write_text("# Cleanup\n\nVersion 2 with cleanup failure.", encoding="utf-8")
    v2 = ingestion_service.ingest_file(file, source_type="RUNBOOK")

    assert v2["status"] == "INGESTED"
    assert v2["version_number"] == 2

    doc_repo = KnowledgeDocumentRepository(db_session)
    doc = doc_repo.get_by_id(v2["document_id"])
    assert doc.current_version_id == v2["version_id"]

    version_repo = KnowledgeDocumentVersionRepository(db_session)
    v2_db = version_repo.get_by_id(v2["version_id"])
    assert v2_db.ingestion_status == "COMPLETED"
