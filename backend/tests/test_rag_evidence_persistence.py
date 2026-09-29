from datetime import datetime, timezone

from app.models.investigation_evidence import InvestigationEvidence
from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_document_version import KnowledgeDocumentVersion
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.repositories.knowledge_document_version_repository import (
    KnowledgeDocumentVersionRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService
from app.services.investigation_service import InvestigationService


class _RAGTestGraph:
    def __init__(
        self,
        rag_citations=None,
        rag_query="Why is Payment API timing out?",
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
                "final_summary": "RAG evidence investigation completed.",
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
                "rag_context": "Sample formatted context",
                "rag_citations": self.outer.rag_citations,
                "risk_prediction": None,
            }

    @property
    def graph(self):
        return self._Wrapper(self)


def _build_service(db_session) -> InvestigationService:
    inv_repo = InvestigationRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    user_repo = UserRepository(db_session)
    audit_repo = AuditLogRepository(db_session)
    audit_service = AuditLogService(db_session, audit_repo, user_repo)
    return InvestigationService(db_session, inv_repo, inc_repo, audit_service)


def test_rag_evidence_is_persisted(db_session):
    """
    Test 1: Given KB-1 and KB-2, verify two investigation evidence rows exist
    with source_type = KNOWLEDGE_BASE and chunk_id as source_reference.
    """
    service = _build_service(db_session)

    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-payment-001",
            "document_id": "doc-payment-timeouts",
            "source_type": "FILE",
            "source_name": "payment-api-database-timeouts.md",
            "title": "Payment API Database Timeouts Runbook",
            "version_number": 1,
            "score": 0.885,
            "content": "Check connection pool exhaustion and max_connections settings.",
        },
        {
            "citation_id": "KB-2",
            "chunk_id": "chunk-gateway-002",
            "document_id": "doc-api-gateway",
            "source_type": "FILE",
            "source_name": "api-gateway-troubleshooting.md",
            "title": "API Gateway Troubleshooting",
            "version_number": 1,
            "score": 0.792,
            "content": "Check 504 Gateway Timeout upstream connections.",
        },
    ]

    graph = _RAGTestGraph(rag_citations=rag_citations)
    detail = service.run_investigation(
        incident_id=1,
        question="Why is Payment API timing out?",
        actor_user_id=1,
        graph=graph,
    )

    assert detail is not None
    assert detail.status == "COMPLETED"

    kb_evidence = [
        e for e in detail.evidence if e.evidence_type == "KNOWLEDGE_BASE"
    ]
    assert len(kb_evidence) == 2
    chunk_ids = {e.source_reference for e in kb_evidence}
    assert chunk_ids == {"chunk-payment-001", "chunk-gateway-002"}


def test_rag_evidence_metadata_preserved(db_session):
    """
    Test 2: Verify PostgreSQL contains all required provenance metadata:
    citation_id, document_id, version_number, score, source_name, rag_query.
    """
    service = _build_service(db_session)

    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-prov-001",
            "document_id": "doc-auth-runbook",
            "source_type": "FILE",
            "source_name": "auth-service-runbook.md",
            "title": "Auth Service Runbook",
            "version_number": 3,
            "score": 0.912,
            "content": "Verify JWT signing key rotation and cache TTL.",
        }
    ]

    graph = _RAGTestGraph(
        rag_citations=rag_citations,
        rag_query="What caused auth failures?",
    )
    detail = service.run_investigation(
        incident_id=1,
        question="What caused auth failures?",
        actor_user_id=1,
        graph=graph,
    )

    kb_evidence = [
        e for e in detail.evidence if e.evidence_type == "KNOWLEDGE_BASE"
    ]
    assert len(kb_evidence) == 1
    ev = kb_evidence[0]

    meta = ev.evidence_metadata
    assert meta is not None
    assert meta["citation_id"] == "KB-1"
    assert meta["document_id"] == "doc-auth-runbook"
    assert meta["version_number"] == 3
    assert abs(meta["score"] - 0.912) < 1e-4
    assert meta["source_name"] == "auth-service-runbook.md"
    assert meta["source_type"] == "FILE"
    assert meta["rag_query"] == "What caused auth failures?"


def test_rag_chunk_content_preserved(db_session):
    """
    Test 3: The persisted evidence content must exactly represent
    the retrieved chunk used by the investigation.
    """
    service = _build_service(db_session)

    chunk_text = (
        "Runbook section 3.2: Inspect RDS Postgres connections. "
        "Run `SELECT * FROM pg_stat_activity WHERE state = 'active';`"
    )

    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-exact-content",
            "document_id": "doc-pg-activity",
            "source_type": "RUNBOOK",
            "source_name": "postgres-diagnostics.md",
            "title": "Postgres Diagnostics",
            "version_number": 2,
            "score": 0.84,
            "content": chunk_text,
        }
    ]

    graph = _RAGTestGraph(rag_citations=rag_citations)
    detail = service.run_investigation(
        incident_id=1,
        question="How to inspect active queries?",
        actor_user_id=1,
        graph=graph,
    )

    kb_evidence = [
        e for e in detail.evidence if e.evidence_type == "KNOWLEDGE_BASE"
    ]
    assert len(kb_evidence) == 1
    assert kb_evidence[0].content == chunk_text


def test_findings_link_to_rag_evidence(db_session):
    """
    Test 4: Given finding -> KB-1, verify the corresponding finding_evidence
    row points to the persisted evidence row.
    """
    service = _build_service(db_session)

    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-pool-exhaustion",
            "document_id": "doc-pool",
            "source_type": "FILE",
            "source_name": "db-pool.md",
            "title": "Database Connection Pool Guide",
            "version_number": 1,
            "score": 0.89,
            "content": "Connection pool timeout occurs under high spike load.",
        }
    ]
    findings = [
        {
            "finding": "The runbook identifies connection pool exhaustion as a cause for database timeouts.",
            "confidence": "HIGH",
            "evidence_refs": [
                {
                    "source_type": "KNOWLEDGE_BASE",
                    "source_id": "KB-1",
                }
            ],
        }
    ]

    graph = _RAGTestGraph(rag_citations=rag_citations, findings=findings)
    detail = service.run_investigation(
        incident_id=1,
        question="Why did DB timeouts occur?",
        actor_user_id=1,
        graph=graph,
    )

    assert len(detail.findings) == 1
    f = detail.findings[0]
    assert len(f.evidence_links) == 1

    link = f.evidence_links[0]
    assert link.relationship_type == "SUPPORTS"
    assert link.evidence is not None
    assert link.evidence.evidence_type == "KNOWLEDGE_BASE"
    assert link.evidence.source_reference == "chunk-pool-exhaustion"
    assert link.evidence.evidence_metadata["citation_id"] == "KB-1"


def test_multiple_findings_share_rag_evidence(db_session):
    """
    Test 5: Given finding 1 -> KB-1 and finding 2 -> KB-1, verify there is
    still only ONE investigation evidence record for that citation.
    """
    service = _build_service(db_session)

    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-shared-001",
            "document_id": "doc-shared",
            "source_type": "FILE",
            "source_name": "shared-doc.md",
            "title": "Shared Knowledge Document",
            "version_number": 1,
            "score": 0.85,
            "content": "Shared knowledge content for multiple findings.",
        }
    ]
    findings = [
        {
            "finding": "First finding derived from KB-1 runbook guidance.",
            "confidence": "HIGH",
            "evidence_refs": [
                {"source_type": "KNOWLEDGE_BASE", "source_id": "KB-1"}
            ],
        },
        {
            "finding": "Second finding confirming recommendation from KB-1.",
            "confidence": "MEDIUM",
            "evidence_refs": [
                {"source_type": "KNOWLEDGE_BASE", "source_id": "KB-1"}
            ],
        },
    ]

    graph = _RAGTestGraph(rag_citations=rag_citations, findings=findings)
    detail = service.run_investigation(
        incident_id=1,
        question="What are the findings?",
        actor_user_id=1,
        graph=graph,
    )

    # 1. Exactly one investigation_evidence record
    kb_evidence = [
        e for e in detail.evidence if e.evidence_type == "KNOWLEDGE_BASE"
    ]
    assert len(kb_evidence) == 1
    evidence_id = kb_evidence[0].evidence_id

    # 2. Both findings point to that same evidence_id
    assert len(detail.findings) == 2
    f1_links = detail.findings[0].evidence_links
    f2_links = detail.findings[1].evidence_links
    assert len(f1_links) == 1
    assert len(f2_links) == 1
    assert f1_links[0].evidence_id == evidence_id
    assert f2_links[0].evidence_id == evidence_id


def test_rag_version_immutable_in_history(db_session):
    """
    Test 6: Verify version immutability in history.
    Simulate version 1 retrieved for an investigation.
    Then version 2 is ingested and becomes current in PostgreSQL.
    Verify the old investigation's persisted evidence still contains version_number = 1.
    """
    service = _build_service(db_session)
    doc_repo = KnowledgeDocumentRepository(db_session)
    version_repo = KnowledgeDocumentVersionRepository(db_session)

    # 1. Create document with version 1 in DB
    doc = KnowledgeDocument(
        source_type="RUNBOOK",
        source_name="immutable_test_runbook.md",
        title="Immutable Test Runbook",
        status="ACTIVE",
    )
    doc_repo.add(doc)
    db_session.flush()

    v1 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=1,
        content_hash="hash-v1",
        content="Version 1 runbook content.",
        chunk_count=1,
    )
    version_repo.add(v1)
    db_session.flush()
    doc.current_version_id = v1.version_id
    db_session.flush()

    # 2. Investigation retrieves version 1
    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-v1-001",
            "document_id": str(doc.document_id),
            "source_type": "RUNBOOK",
            "source_name": "immutable_test_runbook.md",
            "title": "Immutable Test Runbook",
            "version_number": 1,
            "score": 0.87,
            "content": "Version 1 runbook content.",
        }
    ]
    graph = _RAGTestGraph(rag_citations=rag_citations)
    detail = service.run_investigation(
        incident_id=1,
        question="What does the runbook say?",
        actor_user_id=1,
        graph=graph,
    )
    inv_id = detail.investigation_id

    # 3. Ingest version 2 in DB and mark it current
    v2 = KnowledgeDocumentVersion(
        document_id=doc.document_id,
        version_number=2,
        content_hash="hash-v2",
        content="Version 2 runbook content.",
        chunk_count=2,
    )
    version_repo.add(v2)
    db_session.flush()
    doc.current_version_id = v2.version_id
    db_session.flush()

    # Verify DB now has v2 as current
    latest = version_repo.get_latest(doc.document_id)
    assert latest is not None
    assert latest.version_number == 2
    assert doc.current_version_id == v2.version_id

    # 4. Check that the historical investigation's evidence record still has version_number = 1
    historic_inv = service.get_investigation_details(inv_id)
    kb_evidence = [
        e for e in historic_inv.evidence if e.evidence_type == "KNOWLEDGE_BASE"
    ]
    assert len(kb_evidence) == 1
    assert kb_evidence[0].evidence_metadata["version_number"] == 1
    assert kb_evidence[0].content == "Version 1 runbook content."


def test_investigation_without_rag_context_behaves_normally(db_session):
    """
    Test 7: Regression test — an investigation with no RAG context (rag_citations empty)
    must behave exactly as the previous non-RAG investigation path:
    persisting operational evidence and linking findings normally without KNOWLEDGE_BASE rows.
    """
    service = _build_service(db_session)

    operational_evidence = [
        {
            "source_type": "deployment",
            "source_id": "14",
            "title": "Deployment v2.9.0",
            "content": "Deployment completed successfully.",
            "metadata": {"version": "2.9.0"},
        }
    ]
    findings = [
        {
            "finding": "Deployment v2.9.0 was triggered immediately before error rate increased.",
            "confidence": "HIGH",
            "evidence_refs": [{"source_type": "deployment", "source_id": "14"}],
        }
    ]

    graph = _RAGTestGraph(
        rag_citations=[],
        evidence=operational_evidence,
        findings=findings,
    )
    detail = service.run_investigation(
        incident_id=1,
        question="What deployment caused this?",
        actor_user_id=1,
        graph=graph,
    )

    assert detail.status == "COMPLETED"
    assert len(detail.evidence) == 1
    assert detail.evidence[0].evidence_type == "deployment"
    assert detail.evidence[0].source_reference == "14"

    # Verify no KNOWLEDGE_BASE evidence rows exist
    kb_evidence = [
        e for e in detail.evidence if e.evidence_type == "KNOWLEDGE_BASE"
    ]
    assert len(kb_evidence) == 0

    # Verify findings linked correctly to deployment evidence
    assert len(detail.findings) == 1
    assert len(detail.findings[0].evidence_links) == 1
    link = detail.findings[0].evidence_links[0]
    assert link.evidence_id == detail.evidence[0].evidence_id


def test_persist_rag_evidence_direct_method(db_session):
    """
    Direct unit test for persist_rag_evidence method:
    - Verifies citation_to_evidence_id mapping returned: {"KB-1": id1, "KB-2": id2}
    - Verifies deduplication prevents redundant rows when the same citation_id appears twice.
    """
    service = _build_service(db_session)

    inv = service.create_investigation(
        incident_id=1,
        investigation_type="ASSISTED",
        question="Test direct persistence",
        actor_user_id=1,
    )

    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-direct-1",
            "document_id": "doc-direct-1",
            "source_type": "FILE",
            "source_name": "direct1.md",
            "title": "Direct Doc 1",
            "version_number": 1,
            "score": 0.85,
            "content": "Direct content 1",
        },
        {
            "citation_id": "KB-2",
            "chunk_id": "chunk-direct-2",
            "document_id": "doc-direct-2",
            "source_type": "FILE",
            "source_name": "direct2.md",
            "title": "Direct Doc 2",
            "version_number": 1,
            "score": 0.80,
            "content": "Direct content 2",
        },
        # Duplicate of KB-1
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-direct-1",
            "document_id": "doc-direct-1",
            "source_type": "FILE",
            "source_name": "direct1.md",
            "title": "Direct Doc 1",
            "version_number": 1,
            "score": 0.85,
            "content": "Direct content 1",
        },
    ]

    mapping = service.persist_rag_evidence(
        investigation_id=inv.investigation_id,
        rag_citations=rag_citations,
        rag_query="Direct query",
    )

    assert set(mapping.keys()) == {"KB-1", "KB-2"}
    assert mapping["KB-1"] != mapping["KB-2"]

    # Verify exactly 2 rows exist in database for this investigation
    details = service.get_investigation_details(inv.investigation_id)
    assert len(details.evidence) == 2
