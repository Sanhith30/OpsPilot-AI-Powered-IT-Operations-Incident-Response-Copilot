"""
Tests for Phase 2: LogHub Dataset Integration and Copilot Log Retrieval.

Verifies:
1. LogHub structured rows exist in core.app_logs across representative datasets (HDFS, Linux, BGL, Hadoop).
2. SearchLogsTool executes keyword searches against LogHub records with accurate filtering.
3. Copilot can execute search_logs and retrieve LogHub evidence.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.repositories.app_log_repository import AppLogRepository
from app.ai.tools.search_logs import SearchLogsTool, SearchLogsInput
from app.ai.providers.mock import MockLLMProvider
from app.api.dependencies import get_llm_provider, get_knowledge_retrieval_service
from app.core.security import create_access_token
from app.main import app


class FakeKnowledgeRetrievalService:
    def retrieve(self, query_obj, *, context=None):
        class Response:
            def model_dump(self, mode="json"):
                return {"results": [], "matches": [], "result_count": 0}
        return Response()


@pytest.fixture(autouse=True)
def mock_llm_dependency():
    app.dependency_overrides[get_llm_provider] = lambda: MockLLMProvider()
    app.dependency_overrides[get_knowledge_retrieval_service] = lambda: FakeKnowledgeRetrievalService()
    yield
    app.dependency_overrides.pop(get_llm_provider, None)
    app.dependency_overrides.pop(get_knowledge_retrieval_service, None)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


def _auth_headers(user_id: int = 1) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def test_loghub_records_present_in_db(db_session):
    """Verify that LogHub records are properly structured and present in core.app_logs."""
    cnt = db_session.execute(
        text("SELECT COUNT(*) FROM core.app_logs WHERE extra->>'source' = 'loghub'")
    ).scalar()
    assert cnt is not None and cnt >= 1000, f"Expected at least 1,000 LogHub logs in DB, found {cnt}"

    # Verify distribution across datasets
    datasets = db_session.execute(
        text("SELECT extra->>'dataset', COUNT(*) FROM core.app_logs WHERE extra->>'source' = 'loghub' GROUP BY 1")
    ).fetchall()
    dataset_names = [d[0] for d in datasets]
    for expected in ["HDFS", "Linux", "BGL", "Hadoop"]:
        assert expected in dataset_names, f"Expected dataset '{expected}' in LogHub logs, found {dataset_names}"


def test_search_logs_tool_retrieves_loghub(db_session):
    """Verify that SearchLogsTool retrieves LogHub entries accurately."""
    repo = AppLogRepository(db=db_session)
    tool = SearchLogsTool(log_repository=repo)

    # 1. Search Linux auth failure
    res_linux = tool.execute(SearchLogsInput(keyword="authentication failure", service_name="auth-service", limit=10))
    assert res_linux["total_returned"] > 0
    assert any("sshd" in log["message"].lower() or "authentication failure" in log["message"].lower() for log in res_linux["logs"])

    # 2. Search HDFS PacketResponder
    res_hdfs = tool.execute(SearchLogsInput(keyword="PacketResponder", service_name="order-service", limit=10))
    assert res_hdfs["total_returned"] > 0
    assert any("packetresponder" in log["message"].lower() for log in res_hdfs["logs"])

    # 3. Search BGL parity error
    res_bgl = tool.execute(SearchLogsInput(keyword="parity error", service_name="payment-api", limit=10))
    assert res_bgl["total_returned"] > 0
    assert any("parity error" in log["message"].lower() for log in res_bgl["logs"])


def test_copilot_chat_search_logs_tool(client: TestClient):
    """Verify that the Copilot chat endpoint accepts a log investigation query and executes search_logs."""
    resp = client.post(
        "/api/v1/chat",
        json={"message": "Please search the application logs for authentication failures in auth-service."},
        headers=_auth_headers(user_id=1),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    # Confirm search_logs was in the tool trace or answer is grounded
    tools = [t.get("tool_name") for t in data.get("tool_trace", [])]
    assert "search_logs" in tools or "auth" in data["answer"].lower()
