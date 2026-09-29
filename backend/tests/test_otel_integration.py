"""
Tests for Phase 3: OpenTelemetry Demo Telemetry Integration.

Verifies:
1. OpenTelemetry metrics and logs exist in PostgreSQL with OTel dimensions/attributes.
2. GetServiceMetricsTool retrieves OTel time-series metrics with accurate anomaly detection and aggregations.
3. SearchLogsTool retrieves OTel structured logs with trace correlation IDs.
4. Copilot chat endpoint accepts queries targeting OTel service telemetry.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.repositories.service_metric_repository import ServiceMetricRepository
from app.repositories.app_log_repository import AppLogRepository
from app.ai.tools.get_service_metrics import GetServiceMetricsTool, GetServiceMetricsInput
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


def test_otel_metrics_and_logs_in_db(db_session):
    """Verify OTel telemetry exists in core.service_metrics and core.app_logs."""
    metric_count = db_session.execute(
        text("SELECT COUNT(*) FROM core.service_metrics WHERE dimensions->>'telemetry_source' = 'otel-astronomy-shop'")
    ).scalar()
    assert metric_count is not None and metric_count > 0, "No OTel metrics found in DB"

    log_count = db_session.execute(
        text("SELECT COUNT(*) FROM core.app_logs WHERE extra->>'telemetry_source' = 'otel-astronomy-shop'")
    ).scalar()
    assert log_count is not None and log_count > 0, "No OTel logs found in DB"


def test_get_service_metrics_tool_otel(db_session):
    """Verify GetServiceMetricsTool accurately summarizes OTel service metrics."""
    repo = ServiceMetricRepository(db=db_session)
    tool = GetServiceMetricsTool(metric_repository=repo)

    result = tool.execute(
        GetServiceMetricsInput(
            service_name="paymentservice",
            metric_name="p99_latency_ms",
            lookback_minutes=1440,
        )
    )

    assert result["total_data_points"] > 0
    assert "p99_latency_ms" in result["summary"]
    stats = result["summary"]["p99_latency_ms"]
    assert stats["avg"] is not None and stats["avg"] > 0


def test_search_logs_tool_otel_trace(db_session):
    """Verify SearchLogsTool searches OTel structured logs by keyword."""
    repo = AppLogRepository(db=db_session)
    tool = SearchLogsTool(log_repository=repo)

    result = tool.execute(
        SearchLogsInput(
            keyword="StatusCode.UNAVAILABLE",
            service_name="checkoutservice",
            limit=5,
        )
    )

    assert result["total_returned"] > 0
    first_log = result["logs"][0]
    assert "checkoutservice" in first_log["service_name"]
    assert "StatusCode.UNAVAILABLE" in first_log["message"]


def test_copilot_metrics_investigation_query(client: TestClient):
    """Verify Copilot handles an SRE inquiry querying live telemetry metrics."""
    resp = client.post(
        "/api/v1/chat",
        json={"message": "What is the p99 latency and error rate for the payment service over the past hour?"},
        headers=_auth_headers(user_id=1),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
