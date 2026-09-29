from unittest.mock import MagicMock
import pytest

from app.ai.rag.access.policy import KnowledgeAccessContext, KnowledgeAccessPolicy
from app.ai.rag.reranking.base import Reranker
from app.ai.rag.reranking.factory import create_reranker, create_reranking_service
from app.ai.rag.reranking.lexical import (
    DeterministicLexicalReranker,
    extract_meaningful_tokens,
    tokenize,
)
from app.ai.rag.reranking.schemas import RerankingWeights
from app.ai.rag.reranking.service import RerankingService
from app.ai.rag.retrieval.schemas import RetrievalFilters, RetrievalQuery
from app.ai.rag.retrieval.service import KnowledgeRetrievalService
from app.ai.rag.schemas import RetrievalResult


def test_tokenize_and_meaningful_tokens():
    tokens = tokenize("What is the DB timeout in payment-api?")
    assert "timeout" in tokens
    assert "payment-api" in tokens or "payment" in tokens

    meaningful = extract_meaningful_tokens("What is the timeout in payment-api?")
    assert "what" not in meaningful
    assert "is" not in meaningful
    assert "the" not in meaningful
    assert "timeout" in meaningful


def test_deterministic_lexical_reranker_reorders_by_relevance():
    reranker = DeterministicLexicalReranker(
        weights=RerankingWeights(vector_weight=0.5, lexical_weight=0.35, title_weight=0.15)
    )

    query = "database connection timeout payment api"

    # Candidate 1: High vector score, but unrelated generic content
    c1 = RetrievalResult(
        chunk_id="chunk-1",
        document_id="doc-1",
        content="General guidelines for kubernetes cluster maintenance and pod restarts.",
        score=0.85,
        metadata={"source_name": "k8s-general.md"},
    )

    # Candidate 2: Slightly lower vector score, but exact term match and title match
    c2 = RetrievalResult(
        chunk_id="chunk-2",
        document_id="doc-2",
        content="Payment API database connection timeout handling and pool recovery procedures.",
        score=0.75,
        metadata={"source_name": "payment-api-database-timeouts.md"},
    )

    results = reranker.rerank(
        query=query,
        candidates=[c1, c2],
        top_k=2,
    )

    assert len(results) == 2
    # Candidate 2 should be reranked to 1st position due to lexical & title match
    assert results[0].chunk_id == "chunk-2"
    assert results[0].metadata["title_match_score"] > results[1].metadata["title_match_score"]
    assert results[0].metadata["lexical_score"] > results[1].metadata["lexical_score"]
    assert results[0].metadata["original_vector_score"] == 0.75
    assert results[0].metadata["reranker"] == "deterministic_lexical"


def test_deterministic_lexical_reranker_empty_and_top_k():
    reranker = DeterministicLexicalReranker()
    assert reranker.rerank(query="test", candidates=[], top_k=5) == []

    c1 = RetrievalResult(
        chunk_id="chunk-1",
        document_id="doc-1",
        content="Some content",
        score=0.8,
        metadata={},
    )
    assert reranker.rerank(query="test", candidates=[c1], top_k=0) == []

    c2 = RetrievalResult(
        chunk_id="chunk-2",
        document_id="doc-2",
        content="Some other content",
        score=0.9,
        metadata={},
    )
    results = reranker.rerank(query="test", candidates=[c1, c2], top_k=1)
    assert len(results) == 1


def test_reranking_factory():
    reranker = create_reranker("lexical")
    assert isinstance(reranker, DeterministicLexicalReranker)

    service = create_reranking_service("lexical")
    assert isinstance(service, RerankingService)

    with pytest.raises(ValueError, match="Unknown reranker type"):
        create_reranker("invalid_reranker_type")


def test_knowledge_retrieval_service_with_reranker_pipeline():
    mock_vector_store = MagicMock()
    mock_doc_repo = MagicMock()
    mock_access_policy = MagicMock()

    # Reranker mock
    mock_reranker = MagicMock(spec=Reranker)

    # 15 candidate chunks from vector store
    raw_candidates = [
        RetrievalResult(
            chunk_id=f"chunk-{i}",
            document_id="doc-payment",
            content=f"Payment content {i}",
            score=0.90 - (i * 0.01),
            metadata={"source_name": "payment.md", "source_type": "RUNBOOK", "version_number": 1},
        )
        for i in range(15)
    ]
    mock_vector_store.search.return_value = raw_candidates

    # Reranker returns them reordered
    reranked_candidates = list(reversed(raw_candidates))
    mock_reranker.rerank.return_value = reranked_candidates

    # Access record
    mock_doc = MagicMock()
    mock_doc.status = "ACTIVE"
    mock_doc.owner_team_id = 1
    mock_version = MagicMock()
    mock_version.version_number = 1
    mock_doc_repo.get_access_record.return_value = (mock_doc, mock_version)

    mock_access_policy.can_access.return_value = True

    service = KnowledgeRetrievalService(
        vector_store=mock_vector_store,
        document_repository=mock_doc_repo,
        access_policy=mock_access_policy,
        reranker=mock_reranker,
    )

    req = RetrievalQuery(
        query="payment database timeout",
        top_k=5,
        score_threshold=0.65,
    )
    context = KnowledgeAccessContext(user_id=1, team_id=1)

    response = service.retrieve(req, context=context)

    # Verify vector store search called with candidate_k=15 and score_threshold=None (so reranker gets all candidates)
    mock_vector_store.search.assert_called_once_with(
        "payment database timeout",
        top_k=15,
        score_threshold=None,
        metadata_filter=None,
    )

    # Verify reranker was called
    mock_reranker.rerank.assert_called_once_with(
        query="payment database timeout",
        candidates=raw_candidates,
        top_k=15,
    )

    # Top 5 final results returned
    assert len(response.results) == 5
    assert response.results[0].chunk_id == "chunk-14"


def test_knowledge_retrieval_service_reranker_relevance_gate_filters_low_scores():
    mock_vector_store = MagicMock()
    mock_doc_repo = MagicMock()
    mock_access_policy = MagicMock()
    mock_reranker = MagicMock(spec=Reranker)

    # 3 candidates: two above 0.65, one below 0.65
    c1 = RetrievalResult(chunk_id="c1", document_id="d1", content="t1", score=0.80, metadata={"source_name": "s.md", "source_type": "RUNBOOK", "version_number": 1})
    c2 = RetrievalResult(chunk_id="c2", document_id="d1", content="t2", score=0.55, metadata={"source_name": "s.md", "source_type": "RUNBOOK", "version_number": 1})
    c3 = RetrievalResult(chunk_id="c3", document_id="d1", content="t3", score=0.72, metadata={"source_name": "s.md", "source_type": "RUNBOOK", "version_number": 1})

    mock_vector_store.search.return_value = [c1, c2, c3]
    mock_reranker.rerank.return_value = [c1, c2, c3]

    mock_doc = MagicMock()
    mock_doc.status = "ACTIVE"
    mock_doc.owner_team_id = 1
    mock_version = MagicMock()
    mock_version.version_number = 1
    mock_doc_repo.get_access_record.return_value = (mock_doc, mock_version)
    mock_access_policy.can_access.return_value = True

    service = KnowledgeRetrievalService(
        vector_store=mock_vector_store,
        document_repository=mock_doc_repo,
        access_policy=mock_access_policy,
        reranker=mock_reranker,
    )

    req = RetrievalQuery(query="test", top_k=5, score_threshold=0.65)
    resp = service.retrieve(req, context=KnowledgeAccessContext(user_id=1, team_id=1))

    # c2 (score 0.55) must be dropped by relevance gate
    assert len(resp.results) == 2
    assert [r.chunk_id for r in resp.results] == ["c1", "c3"]


def test_knowledge_retrieval_service_without_reranker_backward_compatible():
    mock_vector_store = MagicMock()
    mock_doc_repo = MagicMock()
    mock_access_policy = MagicMock()

    raw_candidates = [
        RetrievalResult(
            chunk_id="chunk-1",
            document_id="doc-payment",
            content="Payment content",
            score=0.85,
            metadata={"source_name": "payment.md", "source_type": "RUNBOOK", "version_number": 1},
        )
    ]
    mock_vector_store.search.return_value = raw_candidates

    mock_doc = MagicMock()
    mock_doc.status = "ACTIVE"
    mock_doc.owner_team_id = 1
    mock_version = MagicMock()
    mock_version.version_number = 1
    mock_doc_repo.get_access_record.return_value = (mock_doc, mock_version)
    mock_access_policy.can_access.return_value = True

    # No reranker provided
    service = KnowledgeRetrievalService(
        vector_store=mock_vector_store,
        document_repository=mock_doc_repo,
        access_policy=mock_access_policy,
        reranker=None,
    )

    req = RetrievalQuery(
        query="payment timeout",
        top_k=5,
        score_threshold=0.65,
    )
    context = KnowledgeAccessContext(user_id=1, team_id=1)
    response = service.retrieve(req, context=context)

    # Verify score_threshold=0.65 passed directly to vector store
    mock_vector_store.search.assert_called_once_with(
        "payment timeout",
        top_k=15,
        score_threshold=0.65,
        metadata_filter=None,
    )
    assert len(response.results) == 1
