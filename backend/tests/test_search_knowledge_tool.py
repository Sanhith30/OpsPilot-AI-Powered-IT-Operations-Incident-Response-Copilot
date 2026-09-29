from unittest.mock import MagicMock

import pytest

from app.ai.rag.access.policy import KnowledgeAccessContext
from app.ai.rag.retrieval.schemas import (
    RetrievalFilters,
    RetrievalResponse,
)
from app.ai.rag.retrieval.service import KnowledgeRetrievalService
from app.ai.rag.schemas import RetrievalResult
from app.ai.tools.registry_factory import create_tool_registry
from app.ai.tools.search_knowledge import SearchKnowledgeTool


@pytest.fixture
def mock_retrieval_service():
    return MagicMock(spec=KnowledgeRetrievalService)


@pytest.fixture
def access_context():
    return KnowledgeAccessContext(user_id=1, team_id=10)


@pytest.fixture
def search_tool(mock_retrieval_service, access_context):
    return SearchKnowledgeTool(
        retrieval_service=mock_retrieval_service,
        access_context=access_context,
    )


def test_successful_retrieval(search_tool, mock_retrieval_service):
    mock_result = RetrievalResult(
        chunk_id="chunk-1",
        document_id="doc-1",
        content="Payment API database timeout symptoms.",
        score=0.88,
        metadata={
            "source_type": "FILE",
            "source_name": "payment.md",
            "version_number": 1,
        },
    )
    mock_retrieval_service.retrieve.return_value = RetrievalResponse(
        query="database timeout",
        results=[mock_result],
        result_count=1,
        applied_filters=RetrievalFilters(),
    )

    result = search_tool.run({"query": "database timeout", "top_k": 3})

    assert result.status == "SUCCESS"
    assert result.tool_name == "search_knowledge"
    assert result.data["result_count"] == 1
    assert len(result.data["results"]) == 1
    assert result.data["results"][0]["content"] == "Payment API database timeout symptoms."
    assert result.data["results"][0]["score"] == 0.88


def test_filters_forwarded(search_tool, mock_retrieval_service):
    mock_retrieval_service.retrieve.return_value = RetrievalResponse(
        query="database timeout",
        results=[],
        result_count=0,
        applied_filters=RetrievalFilters(),
    )

    raw_input = {
        "query": "database timeout",
        "filters": {
            "source_type": "FILE",
            "source_name": "payment-api-database-timeouts.md",
            "version_number": 1,
        },
    }

    result = search_tool.run(raw_input)

    assert result.status == "SUCCESS"
    called_query_obj = mock_retrieval_service.retrieve.call_args[0][0]
    assert called_query_obj.filters.source_type == "FILE"
    assert called_query_obj.filters.source_name == "payment-api-database-timeouts.md"
    assert called_query_obj.filters.version_number == 1


def test_access_context_forwarded(search_tool, mock_retrieval_service, access_context):
    mock_retrieval_service.retrieve.return_value = RetrievalResponse(
        query="database timeout",
        results=[],
        result_count=0,
        applied_filters=RetrievalFilters(),
    )

    result = search_tool.run({"query": "database timeout"})

    assert result.status == "SUCCESS"
    passed_context = mock_retrieval_service.retrieve.call_args.kwargs.get("context")
    assert passed_context == access_context
    assert passed_context.user_id == 1
    assert passed_context.team_id == 10


def test_empty_knowledge_result(search_tool, mock_retrieval_service):
    mock_retrieval_service.retrieve.return_value = RetrievalResponse(
        query="unknown issue",
        results=[],
        result_count=0,
        applied_filters=RetrievalFilters(),
    )

    result = search_tool.run({"query": "unknown issue"})

    assert result.status == "SUCCESS"
    assert result.data["result_count"] == 0
    assert result.data["results"] == []


def test_invalid_query_validation(search_tool):
    # Empty query
    res_empty = search_tool.run({"query": ""})
    assert res_empty.status == "FAILED"
    assert res_empty.error_code == "INVALID_INPUT"

    # Query exceeding 4000 characters
    res_long = search_tool.run({"query": "A" * 4001})
    assert res_long.status == "FAILED"
    assert res_long.error_code == "INVALID_INPUT"

    # top_k <= 0
    res_invalid_top_k = search_tool.run({"query": "timeout", "top_k": 0})
    assert res_invalid_top_k.status == "FAILED"
    assert res_invalid_top_k.error_code == "INVALID_INPUT"

    # top_k > 20
    res_large_top_k = search_tool.run({"query": "timeout", "top_k": 25})
    assert res_large_top_k.status == "FAILED"
    assert res_large_top_k.error_code == "INVALID_INPUT"


def test_retrieval_failure(search_tool, mock_retrieval_service):
    mock_retrieval_service.retrieve.side_effect = RuntimeError("Pinecone timeout")

    result = search_tool.run({"query": "database timeout"})

    assert result.status == "FAILED"
    assert result.error_code == "TOOL_EXECUTION_ERROR"
    assert result.error_message == "Tool execution failed."


def test_tool_registry_registration(mock_retrieval_service, access_context):
    fake_incident_service = MagicMock()
    fake_deployment_service = MagicMock()
    fake_incident_event_service = MagicMock()

    registry = create_tool_registry(
        incident_service=fake_incident_service,
        deployment_service=fake_deployment_service,
        incident_event_service=fake_incident_event_service,
        knowledge_retrieval_service=mock_retrieval_service,
        knowledge_access_context=access_context,
    )

    tool = registry.get("search_knowledge")
    assert tool is not None
    assert tool.name == "search_knowledge"
    assert "knowledge base" in tool.description.lower()
