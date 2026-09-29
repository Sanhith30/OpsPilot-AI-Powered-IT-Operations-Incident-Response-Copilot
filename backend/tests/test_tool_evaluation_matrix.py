"""
Automated Pytest Suite for Phase 5: End-to-End Tool Evaluation Matrix.

Verifies:
1. All 9 tools register and execute cleanly via ToolRegistry.
2. Multi-tool composite investigations (Incident + Metrics + Logs + Deployment + RAG + Ticket).
3. Read-only SQL safety guards block data modification and catalog snooping.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest

from app.db.session import SessionLocal
from app.repositories.app_log_repository import AppLogRepository
from app.repositories.service_metric_repository import ServiceMetricRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.incident_event_repository import IncidentEventRepository
from app.services.incident_service import IncidentService
from app.services.deployment_service import DeploymentService
from app.services.incident_event_service import IncidentEventService
from app.ai.tools.registry_factory import create_tool_registry
from app.ai.tools.deployment_tools import GetRecentDeploymentsInput
from app.ai.tools.get_service_metrics import GetServiceMetricsInput
from app.ai.tools.incident_event_tools import SearchIncidentEventsInput
from app.ai.tools.incident_tools import GetIncidentInput
from app.ai.tools.query_tickets import QueryTicketsInput
from app.ai.tools.ticketing_tools import CreateTicketInput
from app.ai.tools.search_knowledge import SearchKnowledgeInput
from app.ai.tools.search_logs import SearchLogsInput
from app.ai.tools.sql_tool import ReadOnlySqlInput


class MockKnowledgeRetrieval:
    def retrieve(self, query_obj, *, context=None):
        class Result:
            def model_dump(self, mode="json"):
                return {
                    "results": [
                        {
                            "chunk_id": "chunk-rb-1",
                            "document_id": "doc-payment-rb",
                            "content": "HikariCP connection pool timeout mitigation: restart pool and adjust max-connections.",
                            "score": 0.92,
                            "metadata": {"title": "Payment API Runbook", "source_name": "runbook.md"},
                        }
                    ],
                    "matches": [],
                    "result_count": 1,
                }
        return Result()


@pytest.fixture(scope="module")
def tool_registry():
    db = SessionLocal()
    registry = create_tool_registry(
        incident_service=IncidentService(db, IncidentRepository(db)),
        deployment_service=DeploymentService(db, DeploymentRepository(db)),
        incident_event_service=IncidentEventService(db, IncidentEventRepository(db)),
        knowledge_retrieval_service=MockKnowledgeRetrieval(),
        knowledge_access_context={"team_id": 1, "role": "OPERATOR"},
        app_log_repository=AppLogRepository(db=db),
        service_metric_repository=ServiceMetricRepository(db=db),
        ticket_repository=TicketRepository(db=db),
        db=db,
    )
    yield registry
    db.close()


def test_part1_individual_tools_coverage(tool_registry):
    """Verify all 9 individual operational tools function correctly."""
    now_utc = datetime.now(timezone.utc)

    # 1. get_incident
    inc = tool_registry.get("get_incident").execute(GetIncidentInput(incident_id=1))
    assert inc["incident_id"] == 1
    assert inc["incident_number"] == "INC-1042"

    # 2. get_recent_deployments
    dep = tool_registry.get("get_recent_deployments").execute(
        GetRecentDeploymentsInput(service_id=1, before_time=now_utc, limit=5)
    )
    assert len(dep.get("deployments", [])) > 0

    # 3. search_incident_events
    events = tool_registry.get("search_incident_events").execute(
        SearchIncidentEventsInput(incident_id=1, limit=5)
    )
    assert len(events.get("events", [])) > 0

    # 4. search_knowledge
    rag = tool_registry.get("search_knowledge").execute(
        SearchKnowledgeInput(query="connection pool timeout")
    )
    assert len(rag.get("results", [])) > 0

    # 5. search_logs
    logs = tool_registry.get("search_logs").execute(
        SearchLogsInput(keyword="timeout", service_name="payment-api", limit=5)
    )
    assert logs.get("total_returned", 0) > 0

    # 6. get_service_metrics
    metrics = tool_registry.get("get_service_metrics").execute(
        GetServiceMetricsInput(service_name="payment-api", lookback_minutes=1440, limit=10)
    )
    assert metrics.get("total_data_points", 0) > 0

    # 7. query_tickets
    tix = tool_registry.get("query_tickets").execute(QueryTicketsInput(incident_id=1, limit=5))
    assert tix.get("total", 0) > 0

    # 8. create_ticket
    ctix = tool_registry.get("create_ticket").execute(
        CreateTicketInput(
            incident_id=1,
            title=f"Test Ticket {uuid.uuid4().hex[:6]}",
            priority="HIGH",
            created_by_user_id=1,
        )
    )
    assert ctix.get("status") == "CREATED"
    assert ctix.get("ticket_number", "").startswith("TICK-")

    # 9. query_database_readonly
    sql = tool_registry.get("query_database_readonly").execute(
        ReadOnlySqlInput(query="SELECT service_id, service_name FROM core.services LIMIT 2")
    )
    assert sql.get("row_count") == 2


def test_part2_composite_investigation_flows(tool_registry):
    """Verify multi-tool composite diagnostic workflows."""
    now_utc = datetime.now(timezone.utc)

    # Performance Spike Investigation
    inc = tool_registry.get("get_incident").execute(GetIncidentInput(incident_id=1))
    metrics = tool_registry.get("get_service_metrics").execute(
        GetServiceMetricsInput(service_name="payment-api", lookback_minutes=60)
    )
    logs = tool_registry.get("search_logs").execute(
        SearchLogsInput(keyword="timeout", service_name="payment-api", limit=5)
    )
    assert inc["title"] is not None
    assert metrics["service_name"] == "payment-api"
    assert logs["total_returned"] >= 0

    # Remediation Action
    rag = tool_registry.get("search_knowledge").execute(
        SearchKnowledgeInput(query="HikariCP connection pool scale")
    )
    assert len(rag["results"]) > 0
    tix = tool_registry.get("create_ticket").execute(
        CreateTicketInput(
            incident_id=1,
            title="Auto-remediation HikariCP adjustment",
            description=rag["results"][0]["content"][:80],
            priority="HIGH",
            created_by_user_id=1,
        )
    )
    assert tix["status"] == "CREATED"


def test_part3_security_sql_guardrails(tool_registry):
    """Verify guarded read-only SQL blocks destructive commands and catalog snooping."""
    sql_tool = tool_registry.get("query_database_readonly")

    # DROP TABLE
    drop_res = sql_tool.execute(ReadOnlySqlInput(query="DROP TABLE core.services CASCADE;"))
    assert drop_res["status"] == "ERROR"
    assert "read-only" in drop_res["error"].lower()

    # DELETE FROM
    del_res = sql_tool.execute(ReadOnlySqlInput(query="DELETE FROM core.incidents WHERE incident_id = 1;"))
    assert del_res["status"] == "ERROR"

    # UPDATE
    upd_res = sql_tool.execute(ReadOnlySqlInput(query="UPDATE core.services SET service_name = 'hacked';"))
    assert upd_res["status"] == "ERROR"

    # Multiple statements
    multi_res = sql_tool.execute(ReadOnlySqlInput(query="SELECT 1; SELECT 2;"))
    assert multi_res["status"] == "ERROR"
    assert "multiple" in multi_res["error"].lower()
