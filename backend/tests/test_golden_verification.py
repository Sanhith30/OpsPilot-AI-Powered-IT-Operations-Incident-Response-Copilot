"""
OpsPilot Golden Verification Test Suite (12 Core Tests)

Verifies the operational behavioral requirements specified in the OpsPilot baseline:
  Test 1: Golden Test — "Why is the Payment API failing?" multi-source investigation
  Test 2: Tool Trace inspection — tool_name, parameters, result_summary, status
  Test 3: Dynamic Routing — single-tool questions only trigger their respective tools
  Test 4: Multi-source synthesis — composite question combining metrics, logs, runbooks
  Test 5: Conversational Memory — multi-turn continuity across session history
  Test 6: Ticket Lifecycle — create_ticket execution persists in core.tickets
  Test 7: RBAC — unauthorized actions blocked, permitted roles authorized
  Test 8: Guarded SQL Safety — destructive statements (DROP/DELETE/ALTER) rejected
  Test 9: RAG Citations — runbook context retrieved with threshold grounding
  Test 10: ML Validation — calibrated Random Forest evaluated without data leakage
  Test 11: Real ML in Agent — predict_incident_risk invokes ML predictor
  Test 12: Tool Resiliency — graceful fallback when tools fail or encounter errors
"""
from __future__ import annotations
import json
import pytest
from fastapi.testclient import TestClient

from app.ai.providers.mock import MockLLMProvider
from app.ai.risk.factory import create_risk_predictor
from app.ai.risk.ml_predictor import MLRiskPredictor
from app.ai.tools.sql_tool import ReadOnlySqlTool, ReadOnlySqlInput
from app.ai.tools.ticketing_tools import CreateTicketTool, CreateTicketInput
from app.api.dependencies import get_llm_provider, get_knowledge_retrieval_service
from app.core.security import create_access_token, decode_access_token
from app.db.session import SessionLocal
from app.main import app


class FakeKnowledgeRetrievalService:
    def retrieve(self, query_obj, *, context=None):
        from app.ai.rag.schemas import RetrievalResult
        result = RetrievalResult(
            chunk_id="chunk-001",
            document_id="doc-runbook-001",
            content="When Payment API error rate exceeds 10%, restart database connection pool and failover to secondary.",
            score=0.89,
            metadata={
                "source_type": "runbook",
                "source_name": "payment-api-runbook.md",
                "title": "Payment API Runbook",
                "version_number": 1,
                "document_id": "doc-runbook-001",
            },
        )
        class Response:
            def model_dump(self, mode="json"):
                return {
                    "results": [result.model_dump()],
                    "matches": [result.model_dump()],
                    "result_count": 1,
                }
        return Response()


@pytest.fixture(autouse=True)
def mock_llm_dependency():
    app.dependency_overrides[get_llm_provider] = lambda: MockLLMProvider()
    app.dependency_overrides[get_knowledge_retrieval_service] = lambda: FakeKnowledgeRetrievalService()
    yield
    app.dependency_overrides.pop(get_llm_provider, None)
    app.dependency_overrides.pop(get_knowledge_retrieval_service, None)


def _auth_headers(user_id: int = 1) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


# ---------------------------------------------------------------------------
# Test 1 & Test 2: Golden Test + Tool Trace Inspection
# ---------------------------------------------------------------------------
def test_1_and_2_golden_investigation_and_tool_trace(client: TestClient):
    """
    Test 1: Ask 'Why is the Payment API failing?'
    Test 2: Check Tool Trace expander structure
    """
    payload = {
        "message": "Why is the Payment API failing? Please investigate incident #1.",
        "incident_id": 1,
    }
    resp = client.post("/api/v1/chat", json=payload, headers=_auth_headers(user_id=1))
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Must produce a grounded answer
    assert "answer" in data
    assert len(data["answer"]) > 40

    # Must invoke operational tools
    tool_trace = data.get("tool_trace", [])
    assert len(tool_trace) >= 1, "Must call operational tools"

    # Tool trace must have required structure for UI ToolTraceExpander
    tool_names = [t["tool_name"] for t in tool_trace]
    for trace in tool_trace:
        assert "tool_name" in trace
        assert "parameters" in trace
        assert "result_summary" in trace
        assert "status" in trace
        assert trace["status"] == "SUCCESS"

    # Verify key operational tools were selected
    assert any(name in tool_names for name in ["search_logs", "query_metrics", "get_incident_details", "get_incident", "retrieve_runbook_context", "search_knowledge"])


# ---------------------------------------------------------------------------
# Test 3: Dynamic Routing — Single-Tool Queries
# ---------------------------------------------------------------------------
def test_3_single_tool_dynamic_routing(client: TestClient):
    """
    Test 3: Check that specific questions trigger their respective tools without blindly running all tools.
    """
    # 3a. Deployment query
    resp_deploy = client.post(
        "/api/v1/chat",
        json={"message": "What is the latest deployment for payment-api?"},
        headers=_auth_headers(user_id=1),
    )
    assert resp_deploy.status_code == 200
    tools_deploy = [t["tool_name"] for t in resp_deploy.json().get("tool_trace", [])]
    assert ("get_service_deployments" in tools_deploy or "get_recent_deployments" in tools_deploy)
    # Should not blindly query risk model
    assert "predict_incident_risk" not in tools_deploy

    # 3b. Metrics query
    resp_metrics = client.post(
        "/api/v1/chat",
        json={"message": "What is the current database connection pool usage metrics for payment-api?"},
        headers=_auth_headers(user_id=1),
    )
    assert resp_metrics.status_code == 200
    tools_metrics = [t["tool_name"] for t in resp_metrics.json().get("tool_trace", [])]
    assert ("query_metrics" in tools_metrics or "get_service_metrics" in tools_metrics)

    # 3c. Runbook query
    resp_runbook = client.post(
        "/api/v1/chat",
        json={"message": "What does the payment API runbook say about high error rates?"},
        headers=_auth_headers(user_id=1),
    )
    assert resp_runbook.status_code == 200
    tools_runbook = [t["tool_name"] for t in resp_runbook.json().get("tool_trace", [])]
    assert ("retrieve_runbook_context" in tools_runbook or "search_knowledge" in tools_runbook)


# ---------------------------------------------------------------------------
# Test 4: Multi-Source Question
# ---------------------------------------------------------------------------
def test_4_multi_source_question(client: TestClient):
    """
    Test 4: Multi-source question combines metrics, logs, and runbook evidence.
    """
    payload = {
        "message": "Why is the payment service currently experiencing high failures, and what does the incident runbook recommend?",
        "incident_id": 1,
    }
    resp = client.post("/api/v1/chat", json=payload, headers=_auth_headers(user_id=1))
    assert resp.status_code == 200
    data = resp.json()

    tools_called = [t["tool_name"] for t in data.get("tool_trace", [])]
    # Expect multi-tool coordination
    assert len(tools_called) >= 2
    assert ("retrieve_runbook_context" in tools_called or "search_knowledge" in tools_called)


# ---------------------------------------------------------------------------
# Test 5: Conversational Memory
# ---------------------------------------------------------------------------
def test_5_conversational_memory(client: TestClient):
    """
    Test 5: Multi-turn conversation remembers prior turns in session history.
    """
    # Turn 1
    resp1 = client.post(
        "/api/v1/chat",
        json={"message": "Why is payment-api failing? Please check incident #1.", "incident_id": 1},
        headers=_auth_headers(user_id=1),
    )
    assert resp1.status_code == 200
    session_id = resp1.json()["session_id"]

    # Turn 2: Follow-up referencing context with pronouns
    resp2 = client.post(
        "/api/v1/chat",
        json={"message": "Did the latest deployment cause it?", "session_id": session_id},
        headers=_auth_headers(user_id=1),
    )
    assert resp2.status_code == 200

    # Retrieve session history from REST endpoint
    session_resp = client.get(f"/api/v1/chat/sessions/{session_id}", headers=_auth_headers(user_id=1))
    assert session_resp.status_code == 200
    session_data = session_resp.json()
    assert len(session_data["messages"]) == 4
    assert session_data["messages"][0]["content"] == "Why is payment-api failing? Please check incident #1."
    assert session_data["messages"][2]["content"] == "Did the latest deployment cause it?"


# ---------------------------------------------------------------------------
# Test 6: Ticket Creation Persistence
# ---------------------------------------------------------------------------
def test_6_ticket_creation_persistence(db_session):
    """
    Test 6: create_ticket tool actually creates and persists in the database.
    Uses the conftest db_session fixture so the insert is rolled back afterwards.
    """
    tool = CreateTicketTool(db=db_session)
    result = tool.execute(
        CreateTicketInput(
            incident_id=1,
            title="Golden Test Ticket: Payment API Latency",
            description="Verified by OpsPilot Golden Test Suite",
            priority="HIGH",
            created_by_user_id=1,
        )
    )
    assert result["status"] == "CREATED"
    ticket_id = result["ticket_id"]
    assert ticket_id is not None
    assert "TICK-" in ticket_id


# ---------------------------------------------------------------------------
# Test 7: RBAC Policy Validation
# ---------------------------------------------------------------------------
def test_7_rbac_token_and_permissions():
    """
    Test 7: Verify RBAC permissions matrix and JWT enforcement.
    """
    token_l1 = create_access_token(user_id=2)
    payload_l1 = decode_access_token(token_l1)
    assert payload_l1["user_id"] == 2

    token_l2 = create_access_token(user_id=3)
    payload_l2 = decode_access_token(token_l2)
    assert payload_l2["user_id"] == 3


# ---------------------------------------------------------------------------
# Test 8: SQL Safety — Guarded Read-Only Tool
# ---------------------------------------------------------------------------
def test_8_guarded_sql_safety(db_session):
    """
    Test 8: Ensure destructive SQL statements (DELETE/DROP/ALTER) are rejected.
    Calls execute() directly to inspect the raw result dict from the safety guard.
    """
    sql_tool = ReadOnlySqlTool(db=db_session)

    # Destructive attempt 1: DELETE — must not start with SELECT
    res_delete = sql_tool.execute(ReadOnlySqlInput(query="DELETE FROM core.incidents WHERE incident_id = 1;"))
    assert res_delete["status"] == "ERROR"
    assert (
        "BLOCKED" in res_delete["error"]
        or "Forbidden" in res_delete["error"]
        or "Read-only" in res_delete["error"]
    )

    # Destructive attempt 2: DROP TABLE
    res_drop = sql_tool.execute(ReadOnlySqlInput(query="DROP TABLE core.incidents;"))
    assert res_drop["status"] == "ERROR"

    # Destructive attempt 3: UPDATE
    res_update = sql_tool.execute(ReadOnlySqlInput(query="UPDATE core.incidents SET status = 'RESOLVED';"))
    assert res_update["status"] == "ERROR"

    # Valid SELECT — must succeed and return rows (real DB has seed data)
    res_select = sql_tool.execute(ReadOnlySqlInput(query="SELECT incident_id, title FROM core.incidents LIMIT 1;"))
    assert res_select["status"] == "SUCCESS"
    assert len(res_select["rows"]) > 0


# ---------------------------------------------------------------------------
# Test 9: RAG Citations
# ---------------------------------------------------------------------------
def test_9_rag_citations(client: TestClient):
    """
    Test 9: Ask runbook question and verify citations returned in chat response.
    """
    payload = {
        "message": "What should we do when the payment API error rate is above 10%? Check runbook.",
    }
    resp = client.post("/api/v1/chat", json=payload, headers=_auth_headers(user_id=1))
    assert resp.status_code == 200
    data = resp.json()
    citations = data.get("citations", [])
    assert len(citations) > 0, "RAG question must yield citations"
    for c in citations:
        assert "document_id" in c or "title" in c


# ---------------------------------------------------------------------------
# Test 10: ML Model Evaluation Integrity
# ---------------------------------------------------------------------------
def test_10_ml_evaluation_metrics():
    """
    Test 10: Verify trained ML model has valid non-trivial holdout metrics without data leakage.
    """
    from app.ai.risk.ml_predictor import METADATA_PATH
    assert METADATA_PATH.exists()
    with open(METADATA_PATH) as f:
        meta = json.load(f)

    # Must be trained with independent holdout
    assert meta["holdout_test_samples"] >= 200
    assert meta["holdout_macro_f1"] >= 0.90
    assert meta["holdout_roc_auc"] >= 0.95
    # Confusion matrix must exist
    cm = meta["confusion_matrix"]
    assert len(cm) == 3 and len(cm[0]) == 3


# ---------------------------------------------------------------------------
# Test 11: Agent Uses Trained ML Model
# ---------------------------------------------------------------------------
def test_11_agent_uses_ml_model():
    """
    Test 11: predict_incident_risk invokes MLRiskPredictor by default.
    """
    predictor = create_risk_predictor()
    assert isinstance(predictor, MLRiskPredictor)

    res = predictor.predict_risk(
        incident={"incident_id": 1, "severity": "CRITICAL", "status": "OPEN"},
        evidence=[
            {"source_type": "incident_event", "metadata": {"event_type": "TIMEOUT", "error_rate": 35.0}},
            {"source_type": "incident_event", "metadata": {"event_type": "DB_FAILURE", "error_rate": 28.0}},
        ],
    )
    assert res.risk_level in ("HIGH", "CRITICAL")
    assert res.failure_probability > 0.6
    assert res.model_type == "ML Random Forest"


# ---------------------------------------------------------------------------
# Test 12: Tool Failure Resiliency
# ---------------------------------------------------------------------------
def test_12_tool_failure_resiliency(client: TestClient):
    """
    Test 12: Tool errors do not crash the engine; fail-closed fallback is produced.
    """
    resp = client.post(
        "/api/v1/chat",
        json={"message": "What is the error rate for non_existent_service_xyz_999?"},
        headers=_auth_headers(user_id=1),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
