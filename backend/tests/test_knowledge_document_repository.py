import pytest
from sqlalchemy.exc import IntegrityError

from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_document_version import KnowledgeDocumentVersion
from app.repositories.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)
from app.repositories.knowledge_document_version_repository import (
    KnowledgeDocumentVersionRepository,
)


def test_create_and_get_document(db_session):
    doc_repo = KnowledgeDocumentRepository(db_session)

    doc = KnowledgeDocument(
        source_type="RUNBOOK",
        source_name="payment_timeouts.md",
        title="Payment API Timeouts",
        description="Handling payment db timeouts",
        status="ACTIVE",
    )
    doc_repo.add(doc)
    db_session.flush()

    assert doc.document_id is not None

    fetched = doc_repo.get_by_id(doc.document_id)
    assert fetched is not None
    assert fetched.title == "Payment API Timeouts"
    assert fetched.source_type == "RUNBOOK"
    assert fetched.source_name == "payment_timeouts.md"


def test_get_document_by_source(db_session):
    doc_repo = KnowledgeDocumentRepository(db_session)

    doc = KnowledgeDocument(
        source_type="RUNBOOK",
        source_name="auth_service.md",
        title="Auth Service Runbook",
        status="ACTIVE",
    )
    doc_repo.add(doc)
    db_session.flush()

    fetched = doc_repo.get_by_source(
        source_type="RUNBOOK",
        source_name="auth_service.md",
    )
    assert fetched is not None
    assert fetched.document_id == doc.document_id

    missing = doc_repo.get_by_source(
        source_type="RUNBOOK",
        source_name="nonexistent.md",
    )
    assert missing is None


def test_get_all_active_documents(db_session):
    doc_repo = KnowledgeDocumentRepository(db_session)

    active_doc = KnowledgeDocument(
        source_type="KB",
        source_name="active_guide.md",
        title="Active Guide",
        status="ACTIVE",
    )
    archived_doc = KnowledgeDocument(
        source_type="KB",
        source_name="archived_guide.md",
        title="Archived Guide",
        status="ARCHIVED",
    )
    doc_repo.add(active_doc)
    doc_repo.add(archived_doc)
    db_session.flush()

    active_docs = doc_repo.get_all_active()
    active_sources = [d.source_name for d in active_docs]
    assert "active_guide.md" in active_sources
    assert "archived_guide.md" not in active_sources


def test_duplicate_source_rejection(db_session):
    doc_repo = KnowledgeDocumentRepository(db_session)

    doc1 = KnowledgeDocument(
        source_type="RUNBOOK",
        source_name="duplicate_test.md",
        title="First Copy",
        status="ACTIVE",
    )
    doc_repo.add(doc1)
    db_session.flush()

    doc2 = KnowledgeDocument(
        source_type="RUNBOOK",
        source_name="duplicate_test.md",
        title="Second Copy",
        status="ACTIVE",
    )
    doc_repo.add(doc2)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_create_and_get_versions_ordering(db_session):
    doc_repo = KnowledgeDocumentRepository(db_session)
    version_repo = KnowledgeDocumentVersionRepository(db_session)

    doc = KnowledgeDocument(
        source_type="RUNBOOK",
        source_name="versioned_runbook.md",
        title="Versioned Runbook",
        status="ACTIVE",
    )
    doc_repo.add(doc)
    db_session.flush()

    v1 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=1,
        content_hash="hash-1",
        content="Content v1",
        chunk_count=2,
        embedding_model="gemini-embedding-2",
        embedding_dimensions=1536,
        ingestion_status="COMPLETED",
    )
    v2 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=2,
        content_hash="hash-2",
        content="Content v2",
        chunk_count=3,
        embedding_model="gemini-embedding-2",
        embedding_dimensions=1536,
        ingestion_status="COMPLETED",
    )
    v3 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=3,
        content_hash="hash-3",
        content="Content v3",
        chunk_count=4,
        embedding_model="gemini-embedding-2",
        embedding_dimensions=1536,
        ingestion_status="COMPLETED",
    )
    version_repo.add(v1)
    version_repo.add(v2)
    version_repo.add(v3)
    db_session.flush()

    # Link current version
    doc.current_version_id = v3.version_id
    db_session.flush()

    versions = version_repo.get_versions(doc.document_id)
    version_numbers = [v.version_number for v in versions]
    assert version_numbers == [3, 2, 1]

    latest = version_repo.get_latest(doc.document_id)
    assert latest is not None
    assert latest.version_number == 3
    assert latest.content_hash == "hash-3"

    by_id = version_repo.get_by_id(v2.version_id)
    assert by_id is not None
    assert by_id.version_number == 2


def test_duplicate_version_number_rejection(db_session):
    doc_repo = KnowledgeDocumentRepository(db_session)
    version_repo = KnowledgeDocumentVersionRepository(db_session)

    doc = KnowledgeDocument(
        source_type="RUNBOOK",
        source_name="version_dup.md",
        title="Version Dup",
        status="ACTIVE",
    )
    doc_repo.add(doc)
    db_session.flush()

    v1 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=1,
        content_hash="hash-1",
        content="Content v1",
    )
    v2 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=1,
        content_hash="hash-2",
        content="Content v2",
    )
    version_repo.add(v1)
    db_session.flush()

    version_repo.add(v2)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_duplicate_content_hash_rejection(db_session):
    doc_repo = KnowledgeDocumentRepository(db_session)
    version_repo = KnowledgeDocumentVersionRepository(db_session)

    doc = KnowledgeDocument(
        source_type="RUNBOOK",
        source_name="hash_dup.md",
        title="Hash Dup",
        status="ACTIVE",
    )
    doc_repo.add(doc)
    db_session.flush()

    v1 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=1,
        content_hash="same-hash",
        content="Content v1",
    )
    v2 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=2,
        content_hash="same-hash",
        content="Content v2",
    )
    version_repo.add(v1)
    db_session.flush()

    version_repo.add(v2)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_get_current_version_and_access_record(db_session):
    doc_repo = KnowledgeDocumentRepository(db_session)
    version_repo = KnowledgeDocumentVersionRepository(db_session)

    doc = KnowledgeDocument(
        source_type="RUNBOOK",
        source_name="access_record_test.md",
        title="Access Record Test",
        status="ACTIVE",
        owner_team_id=5,
    )
    doc_repo.add(doc)
    db_session.flush()

    assert doc_repo.get_current_version(doc.document_id) is None

    v1 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=1,
        content_hash="hash-1",
        content="Version 1",
    )
    version_repo.add(v1)
    db_session.flush()

    doc.current_version_id = v1.version_id
    db_session.flush()

    current_ver = doc_repo.get_current_version(doc.document_id)
    assert current_ver is not None
    assert current_ver.version_id == v1.version_id
    assert current_ver.version_number == 1

    access_record = doc_repo.get_access_record(
        source_type="RUNBOOK",
        source_name="access_record_test.md",
    )
    assert access_record is not None
    fetched_doc, fetched_ver = access_record
    assert fetched_doc.document_id == doc.document_id
    assert fetched_doc.owner_team_id == 5
    assert fetched_ver.version_id == v1.version_id

    missing = doc_repo.get_access_record(
        source_type="RUNBOOK",
        source_name="nonexistent.md",
    )
    assert missing is None

