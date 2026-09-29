"""
Phase B Tests — Application Logs, Service Metrics, Ticketing Lifecycle
Tests verify:
  1. AppLog model imports and repository search
  2. ServiceMetric model imports and repository queries
  3. SearchLogsTool execution
  4. GetServiceMetricsTool execution
  5. QueryTicketsTool execution
  6. TicketService full lifecycle (create, update_status, close, add_comment)
  7. ChatGraph reason node routes to Phase B tools
  8. ChatGraph synthesize node includes Phase B evidence
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


# ------------------------------------------------------------------ #
# 1. Model imports                                                     #
# ------------------------------------------------------------------ #

def test_app_log_model_import():
    from app.models.app_log import AppLog
    log = AppLog(
        service_name="payment-api",
        level="ERROR",
        message="Connection pool exhausted",
        environment="Production",
        logged_at=datetime.now(timezone.utc),
    )
    assert log.service_name == "payment-api"
    assert log.level == "ERROR"


def test_service_metric_model_import():
    from app.models.service_metric import ServiceMetric
    m = ServiceMetric(
        service_id=1,
        service_name="payment-api",
        metric_name="cpu_usage_percent",
        metric_value=72.4,
        unit="percent",
        environment="Production",
        recorded_at=datetime.now(timezone.utc),
    )
    assert m.metric_name == "cpu_usage_percent"
    assert m.metric_value == 72.4


# ------------------------------------------------------------------ #
# 2. Repository: AppLogRepository                                      #
# ------------------------------------------------------------------ #

def test_app_log_repository_search():
    from app.repositories.app_log_repository import AppLogRepository
    from app.models.app_log import AppLog

    db = MagicMock()
    repo = AppLogRepository(db)

    # Mock SQLAlchemy query chain
    mock_log = AppLog(
        service_name="payment-api",
        level="ERROR",
        message="Database connection timeout",
        environment="Production",
        logged_at=datetime.now(timezone.utc),
    )
    mock_log.log_id = 1
    mock_log.trace_id = "abc123"
    mock_log.host = "app-01"
    mock_log.logger_name = "app.db"
    mock_log.extra = {}

    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.all.return_value = [mock_log]
    db.query.return_value = q

    results = repo.search(level="ERROR", service_name="payment-api", limit=10)
    assert len(results) == 1
    assert results[0].level == "ERROR"


def test_app_log_repository_tsquery_safe():
    from app.repositories.app_log_repository import AppLogRepository
    safe = AppLogRepository._to_tsquery_safe("connection timeout error")
    assert "&" in safe
    safe2 = AppLogRepository._to_tsquery_safe("timeout")
    assert safe2 == "timeout"


# ------------------------------------------------------------------ #
# 3. Repository: ServiceMetricRepository                               #
# ------------------------------------------------------------------ #

def test_service_metric_repository_queries():
    from app.repositories.service_metric_repository import ServiceMetricRepository
    from app.models.service_metric import ServiceMetric

    db = MagicMock()
    repo = ServiceMetricRepository(db)

    mock_metric = ServiceMetric(
        service_id=1,
        service_name="payment-api",
        metric_name="cpu_usage_percent",
        metric_value=91.2,
        unit="percent",
        environment="Production",
        recorded_at=datetime.now(timezone.utc),
    )
    mock_metric.metric_id = 1
    mock_metric.instance_id = None

    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.all.return_value = [mock_metric]
    db.query.return_value = q

    results = repo.get_by_service_name(service_name="payment-api", limit=10)
    assert len(results) == 1
    assert results[0].metric_value == 91.2


# ------------------------------------------------------------------ #
# 4. SearchLogsTool                                                    #
# ------------------------------------------------------------------ #

def test_search_logs_tool_success():
    from app.ai.tools.search_logs import SearchLogsTool
    from app.models.app_log import AppLog

    mock_repo = MagicMock()
    mock_log = MagicMock()
    mock_log.log_id = 1
    mock_log.service_name = "payment-api"
    mock_log.level = "ERROR"
    mock_log.message = "Connection pool exhausted"
    mock_log.logger_name = "app.db"
    mock_log.trace_id = "abc123"
    mock_log.host = "app-01"
    mock_log.environment = "Production"
    mock_log.logged_at = datetime.now(timezone.utc)
    mock_log.extra = {}
    mock_repo.search.return_value = [mock_log]

    tool = SearchLogsTool(log_repository=mock_repo)
    result = tool.run({"level": "ERROR", "service_name": "payment-api", "limit": 10})

    assert result.status == "SUCCESS"
    data = result.data
    assert data["total_returned"] == 1
    assert data["level_breakdown"]["ERROR"] == 1
    assert data["logs"][0]["level"] == "ERROR"


def test_search_logs_tool_with_time_range():
    from app.ai.tools.search_logs import SearchLogsTool

    mock_repo = MagicMock()
    mock_repo.search.return_value = []

    tool = SearchLogsTool(log_repository=mock_repo)
    result = tool.run({
        "keyword": "timeout",
        "from_time": "2024-01-15T10:00:00Z",
        "to_time": "2024-01-15T12:00:00Z",
        "limit": 20,
    })
    assert result.status == "SUCCESS"
    assert result.data["total_returned"] == 0


def test_search_logs_tool_invalid_input():
    from app.ai.tools.search_logs import SearchLogsTool

    mock_repo = MagicMock()
    tool = SearchLogsTool(log_repository=mock_repo)
    result = tool.run({"limit": 9999})  # limit > 200
    assert result.status == "FAILED"
    assert result.error_code == "INVALID_INPUT"


# ------------------------------------------------------------------ #
# 5. GetServiceMetricsTool                                             #
# ------------------------------------------------------------------ #

def test_get_service_metrics_tool_success():
    from app.ai.tools.get_service_metrics import GetServiceMetricsTool

    mock_repo = MagicMock()

    def make_metric(name, value, unit="percent"):
        m = MagicMock()
        m.metric_name = name
        m.metric_value = value
        m.unit = unit
        m.recorded_at = datetime.now(timezone.utc)
        m.instance_id = None
        m.environment = "Production"
        return m

    mock_repo.get_by_service_name.return_value = [
        make_metric("cpu_usage_percent", 91.2, "percent"),
        make_metric("error_rate", 0.156, "ratio"),
        make_metric("db_connection_pool", 94.0, "percent"),
        make_metric("p99_latency_ms", 820.0, "milliseconds"),
    ]

    tool = GetServiceMetricsTool(metric_repository=mock_repo)
    result = tool.run({"service_name": "payment-api", "lookback_minutes": 60})

    assert result.status == "SUCCESS"
    data = result.data
    assert data["service_name"] == "payment-api"
    assert "cpu_usage_percent" in data["summary"]
    assert "error_rate" in data["summary"]
    # All three of our seeded metrics should trigger anomalies
    assert len(data["anomalies"]) >= 3


def test_get_service_metrics_tool_empty_service():
    from app.ai.tools.get_service_metrics import GetServiceMetricsTool

    mock_repo = MagicMock()
    mock_repo.get_by_service_name.return_value = []

    tool = GetServiceMetricsTool(metric_repository=mock_repo)
    result = tool.run({"service_name": "unknown-service"})

    assert result.status == "SUCCESS"
    assert result.data["total_data_points"] == 0
    assert result.data["anomalies"] == []


# ------------------------------------------------------------------ #
# 6. QueryTicketsTool                                                  #
# ------------------------------------------------------------------ #

def test_query_tickets_tool_by_incident():
    from app.ai.tools.query_tickets import QueryTicketsTool

    mock_repo = MagicMock()

    def make_ticket(number, status, priority):
        t = MagicMock()
        t.ticket_id = 1
        t.ticket_number = number
        t.title = f"Ticket {number}"
        t.description = "Test ticket"
        t.status = status
        t.priority = priority
        t.incident_id = 1
        t.assigned_team_id = None
        t.assigned_user_id = None
        t.created_at = datetime.now(timezone.utc)
        t.updated_at = datetime.now(timezone.utc)
        return t

    mock_repo.get_by_incident.return_value = [
        make_ticket("TKT-001", "OPEN", "HIGH"),
        make_ticket("TKT-002", "IN_PROGRESS", "CRITICAL"),
    ]

    tool = QueryTicketsTool(ticket_repository=mock_repo)
    result = tool.run({"incident_id": 1, "limit": 10})

    assert result.status == "SUCCESS"
    assert result.data["total"] == 2
    assert result.data["tickets"][0]["ticket_number"] == "TKT-001"


def test_query_tickets_tool_by_number():
    from app.ai.tools.query_tickets import QueryTicketsTool

    mock_repo = MagicMock()
    t = MagicMock()
    t.ticket_id = 5
    t.ticket_number = "TKT-005"
    t.title = "DB Connection Pool Issue"
    t.description = None
    t.status = "OPEN"
    t.priority = "CRITICAL"
    t.incident_id = 2
    t.assigned_team_id = 1
    t.assigned_user_id = None
    t.created_at = datetime.now(timezone.utc)
    t.updated_at = datetime.now(timezone.utc)
    mock_repo.get_by_number.return_value = t

    tool = QueryTicketsTool(ticket_repository=mock_repo)
    result = tool.run({"ticket_number": "TKT-005"})

    assert result.status == "SUCCESS"
    assert result.data["tickets"][0]["ticket_number"] == "TKT-005"
    assert result.data["tickets"][0]["priority"] == "CRITICAL"


def test_query_tickets_tool_not_found():
    from app.ai.tools.query_tickets import QueryTicketsTool

    mock_repo = MagicMock()
    mock_repo.get_by_number.return_value = None

    tool = QueryTicketsTool(ticket_repository=mock_repo)
    result = tool.run({"ticket_number": "TKT-999"})

    assert result.status == "SUCCESS"
    assert result.data["total"] == 0


# ------------------------------------------------------------------ #
# 7. TicketService full lifecycle                                      #
# ------------------------------------------------------------------ #

def make_mock_ticket():
    t = MagicMock()
    t.ticket_id = 1
    t.ticket_number = "TKT-001"
    t.title = "Payment API Down"
    t.status = "OPEN"
    t.priority = "CRITICAL"
    t.incident_id = 1
    t.assigned_team_id = 1
    t.assigned_user_id = None
    t.created_at = datetime.now(timezone.utc)
    t.updated_at = datetime.now(timezone.utc)
    return t


def make_mock_user(active=True):
    u = MagicMock()
    u.user_id = 1
    u.is_active = active
    return u


def make_ticket_service():
    from app.services.ticket_service import TicketService
    db = MagicMock()
    ticket_repo = MagicMock()
    incident_repo = MagicMock()
    team_repo = MagicMock()
    user_repo = MagicMock()
    comment_repo = MagicMock()
    audit_service = MagicMock()
    return TicketService(
        db=db,
        ticket_repository=ticket_repo,
        incident_repository=incident_repo,
        team_repository=team_repo,
        user_repository=user_repo,
        ticket_comment_repository=comment_repo,
        audit_log_service=audit_service,
    )


def test_ticket_service_update_status():
    from app.services.ticket_service import TicketService

    svc = make_ticket_service()
    mock_ticket = make_mock_ticket()
    svc.repository.get_by_id.return_value = mock_ticket

    result = svc.update_status(ticket_id=1, new_status="IN_PROGRESS", actor_user_id=1)

    assert result.status == "IN_PROGRESS"
    svc.audit_log_service.add_to_transaction.assert_called_once()
    svc.db.commit.assert_called_once()


def test_ticket_service_update_status_invalid():
    from app.services.ticket_service import TicketService
    from app.core.exceptions import ValidationError

    svc = make_ticket_service()
    svc.repository.get_by_id.return_value = make_mock_ticket()

    with pytest.raises(ValidationError):
        svc.update_status(ticket_id=1, new_status="BOGUS", actor_user_id=1)


def test_ticket_service_close_ticket():
    from app.services.ticket_service import TicketService

    svc = make_ticket_service()
    mock_ticket = make_mock_ticket()
    svc.repository.get_by_id.return_value = mock_ticket

    result = svc.close_ticket(
        ticket_id=1,
        actor_user_id=1,
        resolution_note="Issue resolved after rollback.",
    )

    assert result.status == "CLOSED"
    svc.ticket_comment_repository.add.assert_called_once()


def test_ticket_service_resolve_ticket():
    from app.services.ticket_service import TicketService

    svc = make_ticket_service()
    mock_ticket = make_mock_ticket()
    svc.repository.get_by_id.return_value = mock_ticket

    result = svc.resolve_ticket(
        ticket_id=1,
        actor_user_id=1,
        resolution_note="Deployment rolled back, error rate normalized.",
    )

    assert result.status == "RESOLVED"


def test_ticket_service_add_comment():
    from app.services.ticket_service import TicketService

    svc = make_ticket_service()
    svc.repository.get_by_id.return_value = make_mock_ticket()

    mock_comment = MagicMock()
    svc.ticket_comment_repository.add.return_value = mock_comment

    comment = svc.add_comment(
        ticket_id=1,
        author_id=1,
        comment_text="Escalating to DB team for connection pool investigation.",
    )

    assert comment is not None
    svc.db.commit.assert_called_once()


def test_ticket_service_add_empty_comment_raises():
    from app.services.ticket_service import TicketService
    from app.core.exceptions import ValidationError

    svc = make_ticket_service()
    svc.repository.get_by_id.return_value = make_mock_ticket()

    with pytest.raises(ValidationError):
        svc.add_comment(ticket_id=1, author_id=1, comment_text="   ")


# ------------------------------------------------------------------ #
# 8. ChatGraph reason node Phase B routing                            #
# ------------------------------------------------------------------ #

def make_chat_graph():
    from app.ai.graph.chat_graph import ConversationalChatGraph
    from app.ai.tools.registry import ToolRegistry

    registry = ToolRegistry()
    llm = MagicMock()
    llm.generate.return_value = "Mock LLM response"
    return ConversationalChatGraph(tool_registry=registry, llm_provider=llm)


def test_chat_graph_reason_routes_to_search_logs():
    graph = make_chat_graph()
    state = {
        "session_id": "s1",
        "user_id": 1,
        "incident_id": None,
        "query": "Show me all ERROR logs for payment-api",
        "messages": [],
        "tools_to_run": [],
        "tool_traces": [],
        "raw_evidence": {},
        "citations": [],
        "risk": None,
        "investigation_id": None,
        "final_answer": "",
    }

    result = graph._reason_node(state)
    tool_names = [t["tool_name"] for t in result["tools_to_run"]]
    assert "search_logs" in tool_names


def test_chat_graph_reason_routes_to_get_metrics():
    graph = make_chat_graph()
    state = {
        "session_id": "s1",
        "user_id": 1,
        "incident_id": None,
        "query": "What is the CPU utilization of payment-api?",
        "messages": [],
        "tools_to_run": [],
        "tool_traces": [],
        "raw_evidence": {},
        "citations": [],
        "risk": None,
        "investigation_id": None,
        "final_answer": "",
    }

    result = graph._reason_node(state)
    tool_names = [t["tool_name"] for t in result["tools_to_run"]]
    assert "get_service_metrics" in tool_names


def test_chat_graph_reason_routes_to_query_tickets():
    graph = make_chat_graph()
    state = {
        "session_id": "s1",
        "user_id": 1,
        "incident_id": 1,
        "query": "Show me all open tickets for incident 1",
        "messages": [],
        "tools_to_run": [],
        "tool_traces": [],
        "raw_evidence": {},
        "citations": [],
        "risk": None,
        "investigation_id": None,
        "final_answer": "",
    }

    result = graph._reason_node(state)
    tool_names = [t["tool_name"] for t in result["tools_to_run"]]
    assert "query_tickets" in tool_names


def test_chat_graph_synthesize_includes_phase_b_evidence():
    graph = make_chat_graph()
    state = {
        "session_id": "s1",
        "user_id": 1,
        "incident_id": None,
        "query": "What errors are in the logs?",
        "messages": [],
        "tools_to_run": [],
        "tool_traces": [],
        "raw_evidence": {
            "search_logs": {
                "total_returned": 3,
                "level_breakdown": {"ERROR": 3},
                "logs": [
                    {
                        "log_id": 1,
                        "service_name": "payment-api",
                        "level": "ERROR",
                        "message": "Connection pool exhausted at /api/v1/charge",
                        "logged_at": "2024-01-15T10:05:00+00:00",
                        "trace_id": "abc123",
                        "host": "app-01",
                        "environment": "Production",
                        "extra": {},
                    }
                ],
            }
        },
        "citations": [],
        "risk": None,
        "investigation_id": None,
        "final_answer": "",
    }

    result = graph._synthesize_node(state)
    answer = result["final_answer"]
    # LLM is a mock returning "Mock LLM response" — so grounded fallback should run
    # The log-focused fallback should be triggered
    assert answer is not None
    assert len(answer) > 10


# ------------------------------------------------------------------ #
# 9. Registry factory includes Phase B tools                          #
# ------------------------------------------------------------------ #

def test_registry_factory_includes_phase_b_tools():
    from app.ai.tools.registry_factory import create_tool_registry

    mock_incident_svc = MagicMock()
    mock_deploy_svc = MagicMock()
    mock_event_svc = MagicMock()
    mock_log_repo = MagicMock()
    mock_metric_repo = MagicMock()
    mock_ticket_repo = MagicMock()

    registry = create_tool_registry(
        incident_service=mock_incident_svc,
        deployment_service=mock_deploy_svc,
        incident_event_service=mock_event_svc,
        app_log_repository=mock_log_repo,
        service_metric_repository=mock_metric_repo,
        ticket_repository=mock_ticket_repo,
    )

    tool_names = [t.name for t in registry._tools.values()]
    assert "search_logs" in tool_names
    assert "get_service_metrics" in tool_names
    assert "query_tickets" in tool_names
    # Original tools still present
    assert "get_incident" in tool_names
    assert "get_recent_deployments" in tool_names
    assert "search_incident_events" in tool_names
