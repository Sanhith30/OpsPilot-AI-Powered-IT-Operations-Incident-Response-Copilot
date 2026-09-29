from unittest.mock import MagicMock

import pytest

from app.ai.rag.access.policy import (
    KnowledgeAccessContext,
    KnowledgeAccessPolicy,
)
from app.ai.rag.retrieval.schemas import (
    RetrievalQuery,
)
from app.ai.rag.retrieval.service import (
    KnowledgeRetrievalService,
)
from app.ai.rag.schemas import (
    RetrievalResult,
)
from app.ai.rag.vectorstore.base import (
    VectorStore,
)
from app.observability.metrics import (
    RAG_RETRIEVAL_RESULTS_TOTAL,
    RAG_RETRIEVALS_TOTAL,
)


def test_shared_document_access():
    policy = KnowledgeAccessPolicy()
    context = KnowledgeAccessContext(
        user_id=1,
        team_id=10,
    )
    assert policy.can_access(
        owner_team_id=None,
        context=context,
    )


def test_same_team_access():
    policy = KnowledgeAccessPolicy()
    context = KnowledgeAccessContext(
        user_id=1,
        team_id=10,
    )
    assert policy.can_access(
        owner_team_id=10,
        context=context,
    )


def test_different_team_denied():
    policy = KnowledgeAccessPolicy()
    context = KnowledgeAccessContext(
        user_id=1,
        team_id=20,
    )
    assert not policy.can_access(
        owner_team_id=10,
        context=context,
    )


def test_user_without_team_cannot_access_team_document():
    policy = KnowledgeAccessPolicy()
    context = KnowledgeAccessContext(
        user_id=1,
        team_id=None,
    )
    assert not policy.can_access(
        owner_team_id=10,
        context=context,
    )


def test_stale_version_is_rejected():
    mock_store = MagicMock(spec=VectorStore)
    mock_repo = MagicMock()
    policy = KnowledgeAccessPolicy()

    mock_doc = MagicMock()
    mock_doc.status = "ACTIVE"
    mock_doc.owner_team_id = None

    mock_version = MagicMock()
    mock_version.version_number = 2  # Current version is 2

    mock_repo.get_access_record.return_value = (mock_doc, mock_version)

    service = KnowledgeRetrievalService(
        vector_store=mock_store,
        document_repository=mock_repo,
        access_policy=policy,
    )

    stale_result = RetrievalResult(
        chunk_id="chunk-v1",
        document_id="logical-doc",
        content="old content",
        score=0.95,
        metadata={
            "source_type": "FILE",
            "source_name": "payment.md",
            "version_number": 1,  # Stale version 1
        },
    )

    assert service._is_current_version(stale_result) is False


def test_current_version_is_accepted():
    mock_store = MagicMock(spec=VectorStore)
    mock_repo = MagicMock()
    policy = KnowledgeAccessPolicy()

    mock_doc = MagicMock()
    mock_doc.status = "ACTIVE"
    mock_doc.owner_team_id = None

    mock_version = MagicMock()
    mock_version.version_number = 2

    mock_repo.get_access_record.return_value = (mock_doc, mock_version)

    service = KnowledgeRetrievalService(
        vector_store=mock_store,
        document_repository=mock_repo,
        access_policy=policy,
    )

    current_result = RetrievalResult(
        chunk_id="chunk-v2",
        document_id="logical-doc",
        content="current content",
        score=0.90,
        metadata={
            "source_type": "FILE",
            "source_name": "payment.md",
            "version_number": 2,  # Current version 2
        },
    )

    assert service._is_current_version(current_result) is True


def test_archived_document_is_rejected():
    mock_store = MagicMock(spec=VectorStore)
    mock_repo = MagicMock()
    policy = KnowledgeAccessPolicy()

    mock_doc = MagicMock()
    mock_doc.status = "ARCHIVED"
    mock_doc.owner_team_id = None

    mock_version = MagicMock()
    mock_version.version_number = 1

    mock_repo.get_access_record.return_value = (mock_doc, mock_version)

    service = KnowledgeRetrievalService(
        vector_store=mock_store,
        document_repository=mock_repo,
        access_policy=policy,
    )

    result = RetrievalResult(
        chunk_id="chunk-v1",
        document_id="logical-doc",
        content="archived content",
        score=0.90,
        metadata={
            "source_type": "FILE",
            "source_name": "old_runbook.md",
            "version_number": 1,
        },
    )

    assert service._is_current_version(result) is False


def test_access_filtering_end_to_end():
    mock_store = MagicMock(spec=VectorStore)
    mock_repo = MagicMock()
    policy = KnowledgeAccessPolicy()

    # Document 1: Team 10
    doc_team_10 = MagicMock()
    doc_team_10.status = "ACTIVE"
    doc_team_10.owner_team_id = 10

    ver_10 = MagicMock()
    ver_10.version_number = 1

    # Document 2: Team 20
    doc_team_20 = MagicMock()
    doc_team_20.status = "ACTIVE"
    doc_team_20.owner_team_id = 20

    ver_20 = MagicMock()
    ver_20.version_number = 1

    def fake_get_access_record(source_type, source_name):
        if source_name == "payment.md":
            return doc_team_10, ver_10
        elif source_name == "database.md":
            return doc_team_20, ver_20
        return None

    mock_repo.get_access_record.side_effect = fake_get_access_record

    res1 = RetrievalResult(
        chunk_id="c1",
        document_id="doc-1",
        content="Payment runbook content",
        score=0.92,
        metadata={"source_type": "FILE", "source_name": "payment.md", "version_number": 1},
    )
    res2 = RetrievalResult(
        chunk_id="c2",
        document_id="doc-2",
        content="Database runbook content",
        score=0.88,
        metadata={"source_type": "FILE", "source_name": "database.md", "version_number": 1},
    )

    mock_store.search.return_value = [res1, res2]

    service = KnowledgeRetrievalService(
        vector_store=mock_store,
        document_repository=mock_repo,
        access_policy=policy,
    )

    # User belongs to team 10
    context = KnowledgeAccessContext(user_id=1, team_id=10)
    response = service.retrieve(
        RetrievalQuery(query="runbook guide"),
        context=context,
    )

    assert response.result_count == 1
    assert response.results[0].chunk_id == "c1"
    assert response.results[0].metadata["source_name"] == "payment.md"


def test_retrieval_returns_no_more_than_top_k():
    mock_store = MagicMock(spec=VectorStore)
    mock_repo = MagicMock()
    policy = KnowledgeAccessPolicy()

    doc = MagicMock()
    doc.status = "ACTIVE"
    doc.owner_team_id = None
    ver = MagicMock()
    ver.version_number = 1

    mock_repo.get_access_record.return_value = (doc, ver)

    candidates = [
        RetrievalResult(
            chunk_id=f"c-{i}",
            document_id=f"doc-{i}",
            content=f"content {i}",
            score=0.9 - (i * 0.01),
            metadata={"source_type": "FILE", "source_name": f"doc-{i}.md", "version_number": 1},
        )
        for i in range(10)
    ]
    mock_store.search.return_value = candidates

    service = KnowledgeRetrievalService(
        vector_store=mock_store,
        document_repository=mock_repo,
        access_policy=policy,
    )

    context = KnowledgeAccessContext(user_id=1, team_id=None)
    response = service.retrieve(
        RetrievalQuery(query="test query", top_k=3),
        context=context,
    )

    assert len(response.results) == 3


def test_metrics_and_tracing_success_and_failure():
    mock_store = MagicMock(spec=VectorStore)
    mock_repo = MagicMock()
    policy = KnowledgeAccessPolicy()

    doc = MagicMock()
    doc.status = "ACTIVE"
    doc.owner_team_id = None
    ver = MagicMock()
    ver.version_number = 1
    mock_repo.get_access_record.return_value = (doc, ver)

    mock_store.search.return_value = [
        RetrievalResult(
            chunk_id="c1",
            document_id="d1",
            content="content",
            score=0.9,
            metadata={"source_type": "FILE", "source_name": "d1.md", "version_number": 1},
        )
    ]

    service = KnowledgeRetrievalService(
        vector_store=mock_store,
        document_repository=mock_repo,
        access_policy=policy,
    )

    context = KnowledgeAccessContext(user_id=1, team_id=None)

    init_success = RAG_RETRIEVALS_TOTAL.labels(status="SUCCESS")._value.get()
    init_results = RAG_RETRIEVAL_RESULTS_TOTAL._value.get()

    service.retrieve(
        RetrievalQuery(query="metrics test"),
        context=context,
    )

    after_success = RAG_RETRIEVALS_TOTAL.labels(status="SUCCESS")._value.get()
    after_results = RAG_RETRIEVAL_RESULTS_TOTAL._value.get()

    assert after_success == init_success + 1
    assert after_results == init_results + 1

    # Failure case
    mock_store.search.side_effect = RuntimeError("Pinecone timeout")
    init_failure = RAG_RETRIEVALS_TOTAL.labels(status="FAILURE")._value.get()

    with pytest.raises(RuntimeError, match="Pinecone timeout"):
        service.retrieve(
            RetrievalQuery(query="fail test"),
            context=context,
        )

    after_failure = RAG_RETRIEVALS_TOTAL.labels(status="FAILURE")._value.get()
    assert after_failure == init_failure + 1
