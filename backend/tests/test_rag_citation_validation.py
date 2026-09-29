from app.ai.rag.validation.citation_validator import CitationValidator
from app.ai.rag.validation.schemas import (
    CitationValidationResult,
    FindingValidationResult,
    GroundingValidationResult,
)
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService
from app.services.investigation_service import InvestigationService


class _MockRAGGraph:
    def __init__(
        self,
        rag_citations=None,
        findings=None,
        status="COMPLETED",
        rag_grounding_status=None,
    ):
        self.rag_citations = rag_citations or []
        self.findings = findings or []
        self.status = status
        self.rag_grounding_status = rag_grounding_status

    class _Wrapper:
        def __init__(self, outer):
            self.outer = outer

        def invoke(self, state):
            return {
                "status": self.outer.status,
                "current_stage": "completed",
                "final_summary": "Investigation analysis run completed.",
                "tool_results": [],
                "evidence": [],
                "findings": self.outer.findings,
                "rag_query": "Test query",
                "rag_context": "Test formatted context",
                "rag_citations": self.outer.rag_citations,
                "rag_grounding_status": self.outer.rag_grounding_status,
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


def test_validator_all_citations_valid():
    """
    Test 1: When all referenced citations exist in retrieved RAG context,
    status is VALID and finding is valid.
    """
    validator = CitationValidator()

    rag_citations = [
        {"citation_id": "KB-1", "chunk_id": "chunk-1"},
        {"citation_id": "KB-2", "chunk_id": "chunk-2"},
    ]
    findings = [
        {
            "finding": "Issue supported by KB-1 and KB-2.",
            "confidence": "HIGH",
            "evidence_refs": [
                {"source_type": "KNOWLEDGE_BASE", "source_id": "KB-1"},
                {"source_type": "KNOWLEDGE_BASE", "source_id": "KB-2"},
            ],
        }
    ]

    result = validator.validate(findings=findings, rag_citations=rag_citations)
    assert result.valid is True
    assert result.grounding_status == "VALID"
    assert result.invalid_citations == []
    assert set(result.validated_citations) == {"KB-1", "KB-2"}
    assert len(result.findings_results) == 1
    assert result.findings_results[0].valid is True


def test_validator_unknown_citation_invalid():
    """
    Test 2: When a finding references an unretrieved citation (KB-9),
    status is INVALID and the citation is rejected.
    """
    validator = CitationValidator()

    rag_citations = [
        {"citation_id": "KB-1", "chunk_id": "chunk-1"}
    ]
    findings = [
        {
            "finding": "Unsupported claim referencing KB-9.",
            "confidence": "HIGH",
            "evidence_refs": [
                {"source_type": "KNOWLEDGE_BASE", "source_id": "KB-9"}
            ],
        }
    ]

    result = validator.validate(findings=findings, rag_citations=rag_citations)
    assert result.valid is False
    assert result.grounding_status == "INVALID"
    assert result.invalid_citations == ["KB-9"]
    assert len(result.findings_results) == 1
    assert result.findings_results[0].valid is False
    assert "KB-9" in result.findings_results[0].reason


def test_validator_operational_evidence_unaffected():
    """
    Test 3: Operational evidence references (INCIDENT_EVENT, DEPLOYMENT, etc.)
    are ignored by the RAG validator.
    """
    validator = CitationValidator()

    rag_citations = [
        {"citation_id": "KB-1", "chunk_id": "chunk-1"}
    ]
    findings = [
        {
            "finding": "Operational finding referencing event 42.",
            "confidence": "HIGH",
            "evidence_refs": [
                {"source_type": "INCIDENT_EVENT", "source_id": "42"},
                {"source_type": "DEPLOYMENT", "source_id": "10"},
            ],
        }
    ]

    result = validator.validate(findings=findings, rag_citations=rag_citations)
    assert result.valid is True
    assert result.grounding_status == "VALID"
    assert result.invalid_citations == []
    assert result.findings_results[0].valid is True
    assert result.findings_results[0].invalid_citations == []


def test_validator_mixed_evidence():
    """
    Test 4: Mixed evidence (INCIDENT_EVENT + KNOWLEDGE_BASE) validates
    the knowledge citation while leaving the operational reference intact.
    """
    validator = CitationValidator()

    rag_citations = [
        {"citation_id": "KB-1", "chunk_id": "chunk-1"}
    ]
    findings = [
        {
            "finding": "Finding backed by both operational event and runbook KB-1.",
            "confidence": "HIGH",
            "evidence_refs": [
                {"source_type": "INCIDENT_EVENT", "source_id": "42"},
                {"source_type": "KNOWLEDGE_BASE", "source_id": "KB-1"},
            ],
        }
    ]

    result = validator.validate(findings=findings, rag_citations=rag_citations)
    assert result.valid is True
    assert result.grounding_status == "VALID"
    assert result.validated_citations == ["KB-1"]
    assert result.invalid_citations == []


def test_validator_duplicate_citation():
    """
    Test 5: Duplicate citations to KB-1 in the same finding remain valid
    and do not generate duplicate validation errors or invalid records.
    """
    validator = CitationValidator()

    rag_citations = [
        {"citation_id": "KB-1", "chunk_id": "chunk-1"}
    ]
    findings = [
        {
            "finding": "Duplicate citation test.",
            "confidence": "HIGH",
            "evidence_refs": [
                {"source_type": "KNOWLEDGE_BASE", "source_id": "KB-1"},
                {"source_type": "KNOWLEDGE_BASE", "source_id": "KB-1"},
            ],
        }
    ]

    result = validator.validate(findings=findings, rag_citations=rag_citations)
    assert result.valid is True
    assert result.grounding_status == "VALID"
    assert result.validated_citations == ["KB-1"]
    assert result.invalid_citations == []


def test_validator_no_rag_context():
    """
    Test 6: When no RAG context was retrieved and no knowledge citations were cited,
    grounding status is NOT_APPLICABLE.
    """
    validator = CitationValidator()

    findings = [
        {
            "finding": "Pure operational finding without RAG.",
            "confidence": "HIGH",
            "evidence_refs": [
                {"source_type": "DEPLOYMENT", "source_id": "3"}
            ],
        }
    ]

    result = validator.validate(findings=findings, rag_citations=[])
    assert result.valid is True
    assert result.grounding_status == "NOT_APPLICABLE"
    assert result.invalid_citations == []


def test_validator_multiple_findings_independent_validation():
    """
    Test 7: Multiple findings are evaluated independently. If one finding has an
    invalid citation, the overall grounding status is INVALID and the faulty finding is flagged.
    """
    validator = CitationValidator()

    rag_citations = [
        {"citation_id": "KB-1", "chunk_id": "chunk-1"}
    ]
    findings = [
        {
            "finding": "Valid finding citing KB-1.",
            "confidence": "HIGH",
            "evidence_refs": [
                {"source_type": "KNOWLEDGE_BASE", "source_id": "KB-1"}
            ],
        },
        {
            "finding": "Invalid finding citing non-existent KB-7.",
            "confidence": "MEDIUM",
            "evidence_refs": [
                {"source_type": "KNOWLEDGE_BASE", "source_id": "KB-7"}
            ],
        },
    ]

    result = validator.validate(findings=findings, rag_citations=rag_citations)
    assert result.valid is False
    assert result.grounding_status == "INVALID"
    assert result.invalid_citations == ["KB-7"]
    assert len(result.findings_results) == 2
    assert result.findings_results[0].valid is True
    assert result.findings_results[1].valid is False


def test_invalid_citation_blocks_persistence(db_session):
    """
    Test 8: Critical safety guarantee — an investigation result with an invalid
    citation (KB-999) fails citation validation, status becomes FAILED, and the
    unsupported finding is BLOCKED from being persisted into the database.
    """
    service = _build_service(db_session)

    rag_citations = [
        {
            "citation_id": "KB-1",
            "chunk_id": "chunk-valid-1",
            "document_id": "doc-valid",
            "source_type": "FILE",
            "source_name": "valid.md",
            "title": "Valid Doc",
            "version_number": 1,
            "score": 0.88,
            "content": "Valid retrieved content.",
        }
    ]
    findings = [
        {
            "finding": "Hallucinated finding citing unretrieved KB-999.",
            "confidence": "HIGH",
            "evidence_refs": [
                {"source_type": "KNOWLEDGE_BASE", "source_id": "KB-999"}
            ],
        }
    ]

    graph = _MockRAGGraph(
        rag_citations=rag_citations,
        findings=findings,
        status="COMPLETED",
    )

    detail = service.run_investigation(
        incident_id=1,
        question="Why did the system fail?",
        actor_user_id=1,
        graph=graph,
    )

    # 1. Investigation marked as FAILED due to citation validation failure
    assert detail.status == "FAILED"
    assert "citation validation" in detail.final_summary.lower()

    # 2. Unsupported finding must NOT be persisted in PostgreSQL
    persisted_inv = service.get_investigation_details(detail.investigation_id)
    assert len(persisted_inv.findings) == 0
