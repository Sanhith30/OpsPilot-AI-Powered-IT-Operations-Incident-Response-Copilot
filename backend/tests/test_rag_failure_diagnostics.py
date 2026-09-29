from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from app.ai.rag.access.policy import KnowledgeAccessContext, KnowledgeAccessPolicy
from app.ai.rag.evaluation.diagnostics import (
    AnswerFailureTrace,
    DocumentCompetition,
    FailureType,
    PrecisionAnalysis,
    RerankerShift,
    RetrievalFailureRecord,
    RetrievalFailureReport,
)
from app.ai.rag.evaluation.failure_analysis import RAGFailureAnalyzer
from app.ai.rag.evaluation.schemas import EvalCase
from app.ai.rag.reranking.lexical import DeterministicLexicalReranker
from app.ai.rag.retrieval.service import KnowledgeRetrievalService
from app.ai.rag.schemas import RetrievalResult


def test_failure_type_enum():
    assert FailureType.MISSING_VECTOR == "MISSING_VECTOR"
    assert FailureType.BELOW_THRESHOLD == "BELOW_THRESHOLD"
    assert FailureType.OUTRANKED_BY_COMPETITORS == "OUTRANKED_BY_COMPETITORS"
    assert FailureType.AUTHORIZATION_BLOCKED == "AUTHORIZATION_BLOCKED"
    assert FailureType.RERANKER_DEMOTION == "RERANKER_DEMOTION"
    assert FailureType.QUERY_AMBIGUITY == "QUERY_AMBIGUITY"
    assert FailureType.NONE == "NONE"


def test_document_competition_margin():
    comp = DocumentCompetition(
        expected_document="runbooks/order-service-latency.md",
        expected_document_score=0.7100,
        expected_document_rank=2,
        top_competitor_document="payment-api-database-timeouts.md",
        top_competitor_score=0.7450,
        margin=round(0.7450 - 0.7100, 4),
    )
    assert comp.expected_document == "runbooks/order-service-latency.md"
    assert comp.margin == 0.0350
    assert comp.expected_document_rank == 2


def test_reranker_shift_effects():
    improved = RerankerShift(
        case_id="RAG-001",
        document="payment-api-database-timeouts.md",
        vector_rank=3,
        hybrid_rank=1,
        rank_change=2,
        vector_score=0.72,
        lexical_score=0.85,
        title_score=0.60,
        final_rerank_score=0.75,
        effect="IMPROVED",
    )
    assert improved.effect == "IMPROVED"
    assert improved.rank_change == 2

    demoted = RerankerShift(
        case_id="RAG-002",
        document="database-troubleshooting.md",
        vector_rank=1,
        hybrid_rank=3,
        rank_change=-2,
        vector_score=0.73,
        lexical_score=0.40,
        title_score=0.20,
        final_rerank_score=0.68,
        effect="DEMOTED",
    )
    assert demoted.effect == "DEMOTED"
    assert demoted.rank_change == -2


def test_precision_analysis_calculation():
    pa = PrecisionAnalysis(
        total_positive_cases=10,
        top_k=5,
        mean_chunks_retrieved_per_case=5.0,
        mean_unique_docs_per_case=2.8,
        mean_target_chunks_in_top_k=2.0,
        theoretical_max_precision=0.40,
        actual_precision_at_k=0.40,
        precision_explanation="Test explanation",
    )
    assert pa.theoretical_max_precision == 0.40
    assert pa.actual_precision_at_k == 0.40
    assert pa.mean_target_chunks_in_top_k == 2.0


def test_answer_failure_trace():
    trace = AnswerFailureTrace(
        case_id="ANS-017",
        question="What is the token expiration for auth service?",
        expected_citations=["KB-1"],
        retrieved_citations=[],
        llm_cited=[],
        citation_valid=False,
        grounded=False,
        failure_origin="RETRIEVAL_MISS",
        diagnostic_trace="Target document unindexed in Pinecone.",
    )
    assert trace.failure_origin == "RETRIEVAL_MISS"
    assert not trace.citation_valid
    assert not trace.grounded


def test_analyzer_diagnoses_missing_vector():
    mock_vector_store = MagicMock()
    mock_vector_store.search.return_value = [
        RetrievalResult(
            chunk_id="chunk-1",
            document_id="doc-1",
            content="Some redis guide",
            score=0.82,
            metadata={"source_name": "runbooks/redis-connection-pool.md"},
        )
    ]

    mock_doc_repo = MagicMock()
    mock_doc = MagicMock(status="ACTIVE", owner_team_id=None)
    mock_ver = MagicMock(version_number=1)
    mock_doc_repo.get_access_record.return_value = (mock_doc, mock_ver)

    policy = KnowledgeAccessPolicy()
    service = KnowledgeRetrievalService(
        vector_store=mock_vector_store,
        document_repository=mock_doc_repo,
        access_policy=policy,
        reranker=None,
    )

    analyzer = RAGFailureAnalyzer(
        retrieval_service=service,
        reranker=None,
        candidate_k=15,
        final_k=5,
        score_threshold=0.65,
    )

    cases = [
        EvalCase(
            case_id="RAG-FAIL-01",
            query="Find payment timeout runbook",
            category="symptom_lookup",
            expected_documents=["payment-api-database-timeouts.md"],
            user_id=1,
            team_id=None,
        )
    ]

    report = analyzer.analyze_retrieval_cases(cases)
    assert report.total_failed_positive_cases == 1
    fail = report.failures[0]
    assert fail.case_id == "RAG-FAIL-01"
    assert fail.failure_type == FailureType.MISSING_VECTOR
    assert fail.competition.top_competitor_document == "runbooks/redis-connection-pool.md"


def test_analyzer_diagnoses_below_threshold():
    mock_vector_store = MagicMock()
    mock_vector_store.search.return_value = [
        RetrievalResult(
            chunk_id="chunk-1",
            document_id="doc-1",
            content="Some payment info",
            score=0.55,  # Below 0.65
            metadata={"source_name": "payment-api-database-timeouts.md", "version_number": 1, "source_type": "FILE"},
        )
    ]

    mock_doc_repo = MagicMock()
    mock_doc = MagicMock(status="ACTIVE", owner_team_id=None)
    mock_ver = MagicMock(version_number=1)
    mock_doc_repo.get_access_record.return_value = (mock_doc, mock_ver)

    policy = KnowledgeAccessPolicy()
    service = KnowledgeRetrievalService(
        vector_store=mock_vector_store,
        document_repository=mock_doc_repo,
        access_policy=policy,
        reranker=None,
    )

    analyzer = RAGFailureAnalyzer(
        retrieval_service=service,
        reranker=None,
        candidate_k=15,
        final_k=5,
        score_threshold=0.65,
    )

    cases = [
        EvalCase(
            case_id="RAG-FAIL-02",
            query="Find payment timeout runbook",
            category="symptom_lookup",
            expected_documents=["payment-api-database-timeouts.md"],
            user_id=1,
            team_id=None,
        )
    ]

    report = analyzer.analyze_retrieval_cases(cases)
    assert report.total_failed_positive_cases == 1
    fail = report.failures[0]
    assert fail.failure_type == FailureType.BELOW_THRESHOLD
    assert fail.competition.expected_document_score == 0.55


def test_analyzer_diagnoses_authorization_blocked():
    mock_vector_store = MagicMock()
    mock_vector_store.search.return_value = [
        RetrievalResult(
            chunk_id="chunk-1",
            document_id="doc-secret",
            content="Secret postmortem",
            score=0.88,
            metadata={"source_name": "postmortems/restricted.md", "version_number": 1, "source_type": "FILE"},
        )
    ]

    mock_doc_repo = MagicMock()
    # Team 999 document, but user is team 100
    mock_doc = MagicMock(status="ACTIVE", owner_team_id=999)
    mock_ver = MagicMock(version_number=1)
    mock_doc_repo.get_access_record.return_value = (mock_doc, mock_ver)

    policy = KnowledgeAccessPolicy()
    service = KnowledgeRetrievalService(
        vector_store=mock_vector_store,
        document_repository=mock_doc_repo,
        access_policy=policy,
        reranker=None,
    )

    analyzer = RAGFailureAnalyzer(
        retrieval_service=service,
        reranker=None,
        candidate_k=15,
        final_k=5,
        score_threshold=0.65,
    )

    cases = [
        EvalCase(
            case_id="RAG-FAIL-03",
            query="Restricted postmortem query",
            category="postmortem_lookup",
            expected_documents=["postmortems/restricted.md"],
            user_id=1,
            team_id=100,  # Team 100 cannot access team 999
        )
    ]

    report = analyzer.analyze_retrieval_cases(cases)
    assert report.total_failed_positive_cases == 1
    fail = report.failures[0]
    assert fail.failure_type == FailureType.AUTHORIZATION_BLOCKED


def test_failure_report_serialization():
    report = RetrievalFailureReport(
        dataset_version="2.0",
        total_cases_evaluated=60,
        total_positive_cases=38,
        total_failed_positive_cases=0,
        threshold=0.65,
        candidate_k=15,
        final_k=5,
        failures=[],
        reranker_shifts=[],
        summary={"status": "PASS"},
    )
    serialized = json.loads(report.model_dump_json())
    assert serialized["dataset_version"] == "2.0"
    assert serialized["total_positive_cases"] == 38
    assert serialized["total_failed_positive_cases"] == 0
    assert serialized["failures"] == []
