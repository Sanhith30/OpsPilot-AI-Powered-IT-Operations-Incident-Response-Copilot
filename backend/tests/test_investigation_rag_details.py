from app.core.security import create_access_token
from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_document_version import KnowledgeDocumentVersion
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.evidence_repository import (
    EvidenceRepository,
    InvestigationEvidenceRepository,
)
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.repositories.knowledge_document_version_repository import (
    KnowledgeDocumentVersionRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService
from app.services.investigation_service import InvestigationService


class _FakeRAGGraph:
    def __init__(
        self,
        rag_citations=None,
        rag_query="Why is Payment API database timing out?",
        evidence=None,
        findings=None,
    ):
        self.rag_citations = rag_citations or []
        self.rag_query = rag_query
        self.evidence = evidence or []
        self.findings = findings or []

    class _Wrapper:
        def __init__(self, outer):
            self.outer = outer

        def invoke(self, state):
            return {
                "status": "COMPLETED",
                "current_stage": "completed",
                "final_summary": "RAG investigation details test run completed.",
                "tool_results": [
                    {
                        "tool_name": "search_knowledge",
                        "status": "SUCCESS",
                        "data": {"results": []},
                    }
                ],
                "evidence": self.outer.evidence,
                "findings": self.outer.findings,
                "rag_query": self.outer.rag_query,
                "rag_context": "The following knowledge-base material was retrieved...",
                "rag_citations": self.outer.rag_citations,
                "risk_prediction": None,
            }

    @property
    def graph(self):
        return self._Wrapper(self)


def _auth_headers(user_id: int = 1):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _build_service(db_session) -> InvestigationService:
    inv_repo = InvestigationRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    user_repo = UserRepository(db_session)
    audit_repo = AuditLogRepository(db_session)
    audit_service = AuditLogService(db_session, audit_repo, user_repo)
    return InvestigationService(db_session, inv_repo, inc_repo, audit_service)


def test_investigation_details_populated_with_rag_evidence(client, db_session):
    """
    Test 1: Investigation with RAG evidence -> knowledge_evidence is populated in API response.
    """
    service = _build_service(db_session)

    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-pay-101",
            "document_id": "doc-payment-timeouts",
            "source_type": "FILE",
            "source_name": "payment-api-database-timeouts.md",
            "title": "Payment API Database Timeouts Runbook",
            "version_number": 1,
            "score": 0.885,
            "content": "Check database connection pool timeouts and max connections.",
        }
    ]

    graph = _FakeRAGGraph(rag_citations=rag_citations)
    inv = service.run_investigation(
        incident_id=1,
        question="Why is Payment API timing out?",
        actor_user_id=1,
        graph=graph,
    )

    response = client.get(
        f"/api/v1/investigations/{inv.investigation_id}/details",
        headers=_auth_headers(1),
    )
    assert response.status_code == 200
    data = response.json()

    assert "knowledge_evidence" in data
    assert len(data["knowledge_evidence"]) == 1
    kb = data["knowledge_evidence"][0]
    assert kb["citation_id"] == "KB-1"
    assert kb["chunk_id"] == "chunk-pay-101"
    assert kb["document_id"] == "doc-payment-timeouts"
    assert kb["source_name"] == "payment-api-database-timeouts.md"
    assert kb["source_type"] == "FILE"
    assert kb["version_number"] == 1
    assert abs(kb["score"] - 0.885) < 1e-4
    assert kb["title"] == "Payment API Database Timeouts Runbook"
    assert kb["content"] == "Check database connection pool timeouts and max connections."


def test_investigation_details_without_rag_evidence(client, db_session):
    """
    Test 2: Investigation without RAG -> knowledge_evidence is an empty list.
    """
    service = _build_service(db_session)

    operational_evidence = [
        {
            "source_type": "deployment",
            "source_id": "55",
            "title": "Deploy 55",
            "content": "Deployment info",
            "metadata": {},
        }
    ]

    graph = _FakeRAGGraph(rag_citations=[], evidence=operational_evidence)
    inv = service.run_investigation(
        incident_id=1,
        question="What deployment occurred?",
        actor_user_id=1,
        graph=graph,
    )

    response = client.get(
        f"/api/v1/investigations/{inv.investigation_id}/details",
        headers=_auth_headers(1),
    )
    assert response.status_code == 200
    data = response.json()

    assert "knowledge_evidence" in data
    assert data["knowledge_evidence"] == []


def test_investigation_details_metadata_preserved(client, db_session):
    """
    Test 3: Metadata preserved: citation_id, document_id, version, score, source_name.
    """
    service = _build_service(db_session)

    rag_citations = [
        {
            "citation_id": "KB-2",
            "chunk_id": "chunk-meta-202",
            "document_id": "doc-gateway-504",
            "source_type": "FILE",
            "source_name": "gateway-troubleshooting.md",
            "title": "Gateway 504 Troubleshoot Guide",
            "version_number": 4,
            "score": 0.923,
            "content": "Verify reverse proxy keep-alive timeouts.",
        }
    ]

    graph = _FakeRAGGraph(rag_citations=rag_citations)
    inv = service.run_investigation(
        incident_id=1,
        question="How to troubleshoot 504?",
        actor_user_id=1,
        graph=graph,
    )

    response = client.get(
        f"/api/v1/investigations/{inv.investigation_id}/details",
        headers=_auth_headers(1),
    )
    assert response.status_code == 200
    kb = response.json()["knowledge_evidence"][0]

    assert kb["citation_id"] == "KB-2"
    assert kb["document_id"] == "doc-gateway-504"
    assert kb["version_number"] == 4
    assert abs(kb["score"] - 0.923) < 1e-4
    assert kb["source_name"] == "gateway-troubleshooting.md"


def test_investigation_details_finding_reference_preserved(client, db_session):
    """
    Test 4: Finding reference preserved -> KB-1 remains attached to the correct finding,
    and evidence_links point to the persisted evidence ID.
    """
    service = _build_service(db_session)

    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-f-001",
            "document_id": "doc-pool-exhaustion",
            "source_type": "FILE",
            "source_name": "pool.md",
            "title": "Pool Guide",
            "version_number": 1,
            "score": 0.87,
            "content": "Connection pool was exhausted.",
        }
    ]
    findings = [
        {
            "finding": "The runbook suggests connection pool exhaustion caused the timeout.",
            "confidence": "HIGH",
            "evidence_refs": [{"source_type": "KNOWLEDGE_BASE", "source_id": "KB-1"}],
        }
    ]

    graph = _FakeRAGGraph(rag_citations=rag_citations, findings=findings)
    inv = service.run_investigation(
        incident_id=1,
        question="What caused the timeout?",
        actor_user_id=1,
        graph=graph,
    )

    response = client.get(
        f"/api/v1/investigations/{inv.investigation_id}/details",
        headers=_auth_headers(1),
    )
    assert response.status_code == 200
    data = response.json()

    kb = data["knowledge_evidence"][0]
    expected_evidence_id = kb["evidence_id"]

    assert len(data["findings"]) == 1
    f = data["findings"][0]
    assert len(f["evidence_links"]) == 1
    assert f["evidence_links"][0]["evidence_id"] == expected_evidence_id
    assert f["evidence_links"][0]["citation_id"] == "KB-1"


def test_investigation_details_multiple_findings_share_evidence(client, db_session):
    """
    Test 5: Multiple findings referencing the same citation share the same evidence_id,
    with only one knowledge_evidence entry returned.
    """
    service = _build_service(db_session)

    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-shared-200",
            "document_id": "doc-shared-runbook",
            "source_type": "FILE",
            "source_name": "shared.md",
            "title": "Shared Runbook",
            "version_number": 1,
            "score": 0.82,
            "content": "Shared runbook recommendation.",
        }
    ]
    findings = [
        {
            "finding": "First finding citing KB-1.",
            "confidence": "HIGH",
            "evidence_refs": [{"source_type": "KNOWLEDGE_BASE", "source_id": "KB-1"}],
        },
        {
            "finding": "Second finding citing KB-1.",
            "confidence": "MEDIUM",
            "evidence_refs": [{"source_type": "KNOWLEDGE_BASE", "source_id": "KB-1"}],
        },
    ]

    graph = _FakeRAGGraph(rag_citations=rag_citations, findings=findings)
    inv = service.run_investigation(
        incident_id=1,
        question="What are the findings?",
        actor_user_id=1,
        graph=graph,
    )

    response = client.get(
        f"/api/v1/investigations/{inv.investigation_id}/details",
        headers=_auth_headers(1),
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data["knowledge_evidence"]) == 1
    shared_evidence_id = data["knowledge_evidence"][0]["evidence_id"]

    assert len(data["findings"]) == 2
    f1_ev_id = data["findings"][0]["evidence_links"][0]["evidence_id"]
    f2_ev_id = data["findings"][1]["evidence_links"][0]["evidence_id"]
    assert f1_ev_id == shared_evidence_id
    assert f2_ev_id == shared_evidence_id


def test_investigation_details_historical_version_preserved(client, db_session):
    """
    Test 6: Historical version: version 1 remains visible in investigation details
    even after version 2 becomes current in the database.
    """
    service = _build_service(db_session)
    doc_repo = KnowledgeDocumentRepository(db_session)
    version_repo = KnowledgeDocumentVersionRepository(db_session)

    # 1. Create document with version 1 in DB
    doc = KnowledgeDocument(
        source_type="RUNBOOK",
        source_name="history_doc.md",
        title="History Doc",
        status="ACTIVE",
    )
    doc_repo.add(doc)
    db_session.flush()

    v1 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=1,
        content_hash="hash-hist-v1",
        content="Version 1 original content.",
        chunk_count=1,
    )
    version_repo.add(v1)
    db_session.flush()
    doc.current_version_id = v1.version_id
    db_session.flush()

    # 2. Investigation executed using version 1
    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-hist-001",
            "document_id": str(doc.document_id),
            "source_type": "RUNBOOK",
            "source_name": "history_doc.md",
            "title": "History Doc",
            "version_number": 1,
            "score": 0.86,
            "content": "Version 1 original content.",
        }
    ]
    graph = _FakeRAGGraph(rag_citations=rag_citations)
    inv = service.run_investigation(
        incident_id=1,
        question="What does history doc say?",
        actor_user_id=1,
        graph=graph,
    )
    inv_id = inv.investigation_id

    # 3. Later, version 2 is ingested and becomes current
    v2 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=2,
        content_hash="hash-hist-v2",
        content="Version 2 updated content.",
        chunk_count=2,
    )
    version_repo.add(v2)
    db_session.flush()
    doc.current_version_id = v2.version_id
    db_session.flush()

    # 4. Fetch investigation details from API -> version_number MUST still be 1
    response = client.get(
        f"/api/v1/investigations/{inv_id}/details",
        headers=_auth_headers(1),
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data["knowledge_evidence"]) == 1
    kb = data["knowledge_evidence"][0]
    assert kb["version_number"] == 1
    assert kb["content"] == "Version 1 original content."


def test_investigation_details_unauthorized_blocked(client):
    """
    Test 7: Unauthorized request without valid JWT token is blocked with 401 or 403.
    """
    response = client.get("/api/v1/investigations/1/details")
    assert response.status_code in {401, 403}


def test_evidence_repository_get_knowledge_base_by_investigation(db_session):
    """
    Test repository method: get_knowledge_base_by_investigation directly.
    """
    service = _build_service(db_session)
    evidence_repo = EvidenceRepository(db_session)

    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-repo-1",
            "document_id": "doc-repo-1",
            "source_type": "FILE",
            "source_name": "repo1.md",
            "title": "Repo Doc 1",
            "version_number": 1,
            "score": 0.81,
            "content": "Repo content 1",
        }
    ]
    graph = _FakeRAGGraph(rag_citations=rag_citations)
    inv = service.run_investigation(
        incident_id=1,
        question="Repo test",
        actor_user_id=1,
        graph=graph,
    )

    kb_evidence = evidence_repo.get_knowledge_base_by_investigation(inv.investigation_id)
    assert len(kb_evidence) == 1
    assert kb_evidence[0].evidence_type == "KNOWLEDGE_BASE"
    assert kb_evidence[0].source_reference == "chunk-repo-1"

    # Also verify alias
    assert InvestigationEvidenceRepository is EvidenceRepository
