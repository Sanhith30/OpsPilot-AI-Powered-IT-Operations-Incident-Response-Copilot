from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.ai.rag.access.policy import (
    KnowledgeAccessContext,
    KnowledgeAccessPolicy,
)
from app.ai.rag.retrieval.schemas import (
    RetrievalFilters,
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


class FakeVectorStore(VectorStore):

    def __init__(self):
        self.last_query = None
        self.last_top_k = None
        self.last_threshold = None
        self.last_filter = None

        self.results = [
            RetrievalResult(
                chunk_id="chunk-1",
                document_id="doc-1",
                content="Database timeout symptoms.",
                score=0.91,
                metadata={
                    "source_type": "RUNBOOK",
                    "source_name": "payment.md",
                    "version_number": 2,
                },
            )
        ]

    def add_chunks(self, chunks):
        pass

    def delete_document(self, document_id):
        pass

    def delete_document_version(
        self,
        document_id,
        version_number,
    ):
        pass

    def search(
        self,
        query,
        *,
        top_k=5,
        score_threshold=None,
        metadata_filter=None,
    ):
        self.last_query = query
        self.last_top_k = top_k
        self.last_threshold = score_threshold
        self.last_filter = metadata_filter

        return self.results


@pytest.fixture
def mock_document_repository():
    repo = MagicMock()
    mock_doc = MagicMock()
    mock_doc.status = "ACTIVE"
    mock_doc.owner_team_id = None

    mock_version = MagicMock()
    mock_version.version_number = 2

    repo.get_access_record.return_value = (mock_doc, mock_version)
    return repo


@pytest.fixture
def access_context():
    return KnowledgeAccessContext(user_id=1, team_id=10)


@pytest.fixture
def retrieval_service(mock_document_repository):
    store = FakeVectorStore()
    return KnowledgeRetrievalService(
        vector_store=store,
        document_repository=mock_document_repository,
        access_policy=KnowledgeAccessPolicy(),
    ), store


def test_retrieval_builds_metadata_filter(retrieval_service, access_context):
    service, store = retrieval_service

    response = service.retrieve(
        RetrievalQuery(
            query="database timeout",
            top_k=5,
            score_threshold=0.35,
            filters=RetrievalFilters(
                source_type="RUNBOOK",
                source_name="payment.md",
                document_id="doc-1",
                version_number=2,
            ),
        ),
        context=access_context,
    )

    assert response.result_count == 1
    assert store.last_query == "database timeout"
    assert store.last_top_k == 15  # candidate_k = min(max(5*3, 5), 50) = 15
    assert store.last_threshold == 0.35
    assert store.last_filter == {
        "source_type": "RUNBOOK",
        "source_name": "payment.md",
        "document_id": "doc-1",
        "version_number": 2,
    }


def test_retrieval_rejects_blank_query(retrieval_service, access_context):
    service, _ = retrieval_service

    with pytest.raises(ValueError):
        service.retrieve_text("   ", context=access_context)

    with pytest.raises(ValueError):
        service.retrieve_text("", context=access_context)


def test_retrieval_query_validation():
    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="database timeout",
            top_k=0,
        )

    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="database timeout",
            top_k=100,
        )

    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="database timeout",
            score_threshold=1.5,
        )

    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="",
        )


def test_version_filter_validation():
    with pytest.raises(ValidationError):
        RetrievalFilters(
            version_number=0
        )


def test_retrieve_text(retrieval_service, access_context):
    service, store = retrieval_service

    results = service.retrieve_text(
        "database timeout",
        top_k=3,
        score_threshold=0.50,
        context=access_context,
    )

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"
    assert store.last_query == "database timeout"
    assert store.last_top_k == 9  # candidate_k = min(max(3*3, 3), 50) = 9
    assert store.last_threshold == 0.50
    assert store.last_filter is None


def test_document_version_filter(retrieval_service, access_context):
    service, store = retrieval_service

    service.retrieve_text(
        "database timeout",
        filters=RetrievalFilters(
            document_id="doc-1",
            version_number=3,
        ),
        context=access_context,
    )

    assert store.last_filter == {
        "document_id": "doc-1",
        "version_number": 3,
    }
