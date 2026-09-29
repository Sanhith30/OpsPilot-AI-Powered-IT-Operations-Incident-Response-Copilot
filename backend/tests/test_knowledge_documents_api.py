from unittest.mock import MagicMock

import pytest

from app.ai.rag.ingestion.chunker import KnowledgeChunker
from app.ai.rag.ingestion.loader import KnowledgeDocumentLoader
from app.ai.rag.ingestion.normalizer import KnowledgeDocumentNormalizer
from app.ai.rag.ingestion.service import KnowledgeIngestionService
from app.ai.rag.vectorstore.base import VectorStore
from app.api.dependencies import get_knowledge_ingestion_service
from app.core.security import create_access_token
from app.main import app
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)
from app.repositories.knowledge_document_version_repository import (
    KnowledgeDocumentVersionRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService


def auth_headers(user_id: int):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


@pytest.fixture
def mock_vector_store():
    store = MagicMock(spec=VectorStore)
    provider = MagicMock()
    provider.model_name = "gemini-embedding-2"
    provider.dimension = 1536
    store.embedding_provider = provider
    store.add_chunks.return_value = None
    store.delete_document_version.return_value = None
    return store


@pytest.fixture(autouse=True)
def override_ingestion(db_session, mock_vector_store):
    def _get_ingestion():
        return KnowledgeIngestionService(
            loader=KnowledgeDocumentLoader(),
            normalizer=KnowledgeDocumentNormalizer(),
            chunker=KnowledgeChunker(chunk_size=500, chunk_overlap=50),
            vector_store=mock_vector_store,
            document_repository=KnowledgeDocumentRepository(db_session),
            version_repository=KnowledgeDocumentVersionRepository(db_session),
            db=db_session,
        )

    app.dependency_overrides[get_knowledge_ingestion_service] = _get_ingestion
    yield
    app.dependency_overrides.pop(get_knowledge_ingestion_service, None)


# 1. Create document
def test_create_knowledge_document(client):
    payload = {
        "source_type": "RUNBOOK",
        "source_name": "payment-api-troubleshooting.md",
        "title": "Payment API Troubleshooting Runbook",
        "description": "Standard procedures for payment API timeouts",
        "owner_team_id": 1,
    }

    # User 4 has ROLE_MANAGE
    response = client.post(
        "/api/v1/knowledge/documents",
        json=payload,
        headers=auth_headers(4),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] > 0
    assert data["source_type"] == "RUNBOOK"
    assert data["source_name"] == "payment-api-troubleshooting.md"
    assert data["title"] == "Payment API Troubleshooting Runbook"
    assert data["status"] == "ACTIVE"
    assert data["current_version_id"] is None


# 2. Get document
def test_get_knowledge_document(client):
    # Create a document
    create_resp = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "get-test-doc.md",
            "title": "Get Test Document",
            "description": "Testing document retrieval",
        },
        headers=auth_headers(4),
    )
    assert create_resp.status_code == 200
    doc_id = create_resp.json()["document_id"]

    # User 1 has RUNBOOK_SEARCH
    response = client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers=auth_headers(1),
    )
    assert response.status_code == 200
    assert response.json()["document_id"] == doc_id
    assert response.json()["source_name"] == "get-test-doc.md"

    # Non-existent doc
    not_found = client.get(
        "/api/v1/knowledge/documents/999999",
        headers=auth_headers(1),
    )
    assert not_found.status_code == 404


# 3. List documents
def test_list_knowledge_documents(client):
    # Ensure at least one document exists
    client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "list-test-doc.md",
            "title": "List Test Document",
        },
        headers=auth_headers(4),
    )

    response = client.get(
        "/api/v1/knowledge/documents",
        headers=auth_headers(1),
    )
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    assert len(docs) >= 1
    assert any(d["source_name"] == "list-test-doc.md" for d in docs)


# 4. Get versions
def test_get_knowledge_document_versions(client):
    create_resp = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "versions-test-doc.md",
            "title": "Versions Test",
        },
        headers=auth_headers(4),
    )
    doc_id = create_resp.json()["document_id"]

    # Before ingestion, versions is empty
    resp_empty = client.get(
        f"/api/v1/knowledge/documents/{doc_id}/versions",
        headers=auth_headers(1),
    )
    assert resp_empty.status_code == 200
    assert resp_empty.json() == []

    # Ingest version 1
    ingest_resp = client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": "# Section 1\n\nRunbook instructions here."},
        headers=auth_headers(4),
    )
    assert ingest_resp.status_code == 200

    # Now versions has 1 item
    resp_v1 = client.get(
        f"/api/v1/knowledge/documents/{doc_id}/versions",
        headers=auth_headers(1),
    )
    assert resp_v1.status_code == 200
    versions = resp_v1.json()
    assert len(versions) == 1
    assert versions[0]["version_number"] == 1
    assert versions[0]["ingestion_status"] == "COMPLETED"
    assert versions[0]["chunk_count"] > 0


# 5. Ingest version 1
def test_ingest_knowledge_document_version_1(client):
    create_resp = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "ingest-v1-doc.md",
            "title": "Ingest V1 Doc",
        },
        headers=auth_headers(4),
    )
    doc_id = create_resp.json()["document_id"]

    ingest_resp = client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": "# Ingest Test\n\nInitial content for version 1."},
        headers=auth_headers(4),
    )
    assert ingest_resp.status_code == 200
    ingest_data = ingest_resp.json()
    assert ingest_data["status"] in {"COMPLETED", "INGESTED"}
    assert ingest_data["version_number"] == 1
    assert ingest_data["chunk_count"] > 0

    # Verify current_version_id was promoted
    doc_resp = client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers=auth_headers(1),
    )
    assert doc_resp.status_code == 200
    assert doc_resp.json()["current_version_id"] == ingest_data["version_id"]


# 6. Ingest modified content -> version 2
def test_ingest_modified_content_creates_version_2(client):
    create_resp = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "version-progression.md",
            "title": "Version Progression Doc",
        },
        headers=auth_headers(4),
    )
    doc_id = create_resp.json()["document_id"]

    # Ingest version 1
    resp_v1 = client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": "First version text."},
        headers=auth_headers(4),
    )
    assert resp_v1.status_code == 200
    v1_id = resp_v1.json()["version_id"]

    # Ingest version 2 with modified content
    resp_v2 = client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": "Second version text with updated instructions."},
        headers=auth_headers(4),
    )
    assert resp_v2.status_code == 200
    v2_data = resp_v2.json()
    assert v2_data["status"] in {"COMPLETED", "INGESTED"}
    assert v2_data["version_number"] == 2
    assert v2_data["version_id"] != v1_id

    # Verify current_version_id points to v2
    doc_resp = client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers=auth_headers(1),
    )
    assert doc_resp.json()["current_version_id"] == v2_data["version_id"]


# 7. Same content -> no unnecessary new version (UNCHANGED)
def test_same_content_returns_unchanged(client):
    create_resp = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "idempotent-doc.md",
            "title": "Idempotent Ingestion Doc",
        },
        headers=auth_headers(4),
    )
    doc_id = create_resp.json()["document_id"]

    content = "Stable content that will not change."
    resp1 = client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": content},
        headers=auth_headers(4),
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] in {"COMPLETED", "INGESTED"}
    v1_id = resp1.json()["version_id"]

    # Ingest same content again
    resp2 = client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": content},
        headers=auth_headers(4),
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "UNCHANGED"
    assert data2["version_id"] == v1_id
    assert data2["version_number"] == 1

    # Verify no new version created in DB
    versions_resp = client.get(
        f"/api/v1/knowledge/documents/{doc_id}/versions",
        headers=auth_headers(1),
    )
    assert len(versions_resp.json()) == 1


# 8. Archive document
def test_archive_knowledge_document(client):
    create_resp = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "archive-test-doc.md",
            "title": "Archive Test Doc",
        },
        headers=auth_headers(4),
    )
    doc_id = create_resp.json()["document_id"]

    # Ingest initial version
    client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": "Content to archive later."},
        headers=auth_headers(4),
    )

    # Archive
    archive_resp = client.post(
        f"/api/v1/knowledge/documents/{doc_id}/archive",
        headers=auth_headers(4),
    )
    assert archive_resp.status_code == 200
    assert archive_resp.json()["status"] == "ARCHIVED"

    # Ingestion into archived document is blocked
    ingest_blocked = client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": "Attempting to update archived doc."},
        headers=auth_headers(4),
    )
    assert ingest_blocked.status_code == 422


# 9. Unauthorized management request blocked
def test_unauthorized_management_request_blocked(client):
    # Unauthenticated requests blocked
    resp_no_auth = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "noauth.md",
            "title": "No Auth",
        },
    )
    assert resp_no_auth.status_code in {401, 403}

    # User 1 has RUNBOOK_SEARCH but NOT ROLE_MANAGE
    resp_u1_create = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "u1.md",
            "title": "User 1 Attempt",
        },
        headers=auth_headers(1),
    )
    assert resp_u1_create.status_code == 403

    # Ingest attempt by User 1
    resp_u1_ingest = client.post(
        "/api/v1/knowledge/documents/1/ingest",
        json={"content": "Illegal ingest"},
        headers=auth_headers(1),
    )
    assert resp_u1_ingest.status_code == 403

    # Archive attempt by User 1
    resp_u1_archive = client.post(
        "/api/v1/knowledge/documents/1/archive",
        headers=auth_headers(1),
    )
    assert resp_u1_archive.status_code == 403


# 10. Audit entry created
def test_audit_entry_created(client, db_session):
    create_resp = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "audited-doc.md",
            "title": "Audited Doc",
        },
        headers=auth_headers(4),
    )
    doc_id = create_resp.json()["document_id"]

    client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": "Audited content."},
        headers=auth_headers(4),
    )

    client.post(
        f"/api/v1/knowledge/documents/{doc_id}/archive",
        headers=auth_headers(4),
    )

    audit_service = AuditLogService(
        db=db_session,
        repository=AuditLogRepository(db_session),
        user_repository=UserRepository(db_session),
    )
    logs = audit_service.get_by_resource(
        resource_type="KNOWLEDGE_DOCUMENT",
        resource_id=doc_id,
    )
    actions = [log.action for log in logs]
    assert "KNOWLEDGE_DOCUMENT_CREATED" in actions
    assert "KNOWLEDGE_DOCUMENT_INGESTED" in actions
    assert "KNOWLEDGE_DOCUMENT_ARCHIVED" in actions

    # Verify safe metadata (no document body content stored)
    ingest_log = next(
        l for l in logs if l.action == "KNOWLEDGE_DOCUMENT_INGESTED"
    )
    assert ingest_log.details is not None
    assert "content" not in ingest_log.details
    assert ingest_log.details["document_id"] == doc_id
    assert ingest_log.details["version_number"] == 1
    assert ingest_log.actor_user_id == 4


# 11. Failed ingestion preserves previous current version
def test_failed_ingestion_preserves_previous_current_version(
    client, mock_vector_store
):
    create_resp = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "failure-resilience.md",
            "title": "Failure Resilience Doc",
        },
        headers=auth_headers(4),
    )
    doc_id = create_resp.json()["document_id"]

    # Ingest version 1 successfully
    resp_v1 = client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": "Version 1 stable content."},
        headers=auth_headers(4),
    )
    assert resp_v1.status_code == 200
    v1_id = resp_v1.json()["version_id"]

    # Now make vector store raise error during version 2
    mock_vector_store.add_chunks.side_effect = RuntimeError(
        "Pinecone vector write failure"
    )

    # Ingest version 2 -> fails
    with pytest.raises(RuntimeError):
        client.post(
            f"/api/v1/knowledge/documents/{doc_id}/ingest",
            json={"content": "Version 2 broken content."},
            headers=auth_headers(4),
        )

    # Restore mock
    mock_vector_store.add_chunks.side_effect = None

    # Check document current_version_id is STILL Version 1!
    doc_resp = client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers=auth_headers(1),
    )
    assert doc_resp.status_code == 200
    assert doc_resp.json()["current_version_id"] == v1_id

    # Check versions: version 2 is recorded as FAILED
    versions_resp = client.get(
        f"/api/v1/knowledge/documents/{doc_id}/versions",
        headers=auth_headers(1),
    )
    versions = versions_resp.json()
    assert len(versions) == 2
    v2 = next(v for v in versions if v["version_number"] == 2)
    assert v2["ingestion_status"] == "FAILED"
    assert "Pinecone vector write failure" in v2["ingestion_error"]


# 12. Historical versions remain accessible
def test_historical_versions_remain_accessible(client):
    create_resp = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source_type": "RUNBOOK",
            "source_name": "historical-access.md",
            "title": "Historical Access Doc",
        },
        headers=auth_headers(4),
    )
    doc_id = create_resp.json()["document_id"]

    # Ingest v1
    client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": "Historical content v1."},
        headers=auth_headers(4),
    )

    # Ingest v2
    client.post(
        f"/api/v1/knowledge/documents/{doc_id}/ingest",
        json={"content": "Historical content v2."},
        headers=auth_headers(4),
    )

    # Archive document
    client.post(
        f"/api/v1/knowledge/documents/{doc_id}/archive",
        headers=auth_headers(4),
    )

    # Historical versions are still accessible via API
    versions_resp = client.get(
        f"/api/v1/knowledge/documents/{doc_id}/versions",
        headers=auth_headers(1),
    )
    assert versions_resp.status_code == 200
    versions = versions_resp.json()
    assert len(versions) == 2
    version_numbers = [v["version_number"] for v in versions]
    assert 1 in version_numbers
    assert 2 in version_numbers


# Additional test: verify root route /knowledge/documents also works
def test_root_route_support(client):
    response = client.get(
        "/knowledge/documents",
        headers=auth_headers(1),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
