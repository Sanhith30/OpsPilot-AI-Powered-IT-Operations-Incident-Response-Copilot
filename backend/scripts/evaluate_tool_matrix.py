"""
Comprehensive Tool Evaluation Matrix for OpsPilot.

Evaluates:
  [Part 1] Individual Tool Invocations across all 9 operational tools:
           - get_incident
           - get_recent_deployments
           - search_incident_events
           - search_knowledge
           - search_logs
           - get_service_metrics
           - query_tickets
           - create_ticket
           - read_only_sql
  [Part 2] Multi-Tool Composite Workflows (Golden Investigations):
           - Diagnostics: get_incident -> get_service_metrics -> search_logs
           - Correlation: get_recent_deployments -> search_logs -> read_only_sql
           - Remediation: search_knowledge -> create_ticket
  [Part 3] Safety & Security Guardrails:
           - SQL DDL / DML rejection (DROP, DELETE, UPDATE, INSERT)
           - System catalog isolation
           - Schema boundary validation
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

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


def run_tool_evaluation_matrix():
    print("=" * 70)
    print("OpsPilot End-to-End Operational Tool Evaluation Matrix")
    print("=" * 70)

    db = SessionLocal()
    matrix_results = {"passed": 0, "failed": 0, "tests": []}

    def record_test(category: str, test_name: str, passed: bool, details: str = ""):
        status_str = "PASS" if passed else "FAIL"
        matrix_results["tests"].append({
            "category": category,
            "test": test_name,
            "status": status_str,
            "details": details,
        })
        if passed:
            matrix_results["passed"] += 1
            print(f"  [{status_str}] {test_name}: {details}")
        else:
            matrix_results["failed"] += 1
            print(f"  [{status_str}] {test_name}: {details}")

    # Build registry
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

    all_tools = registry.list_tools()
    tool_names = [t["name"] if isinstance(t, dict) else str(t) for t in all_tools]
    print(f"\n[Registry Initialized]: {len(tool_names)} tools active ({', '.join(tool_names)})\n")

    # ------------------------------------------------------------------ #
    # Part 1: Individual Tool Invocations
    # ------------------------------------------------------------------ #
    print("=== PART 1: Individual Tool Invocations ===")

    # 1. get_incident
    tool_inc = registry.get("get_incident")
    res_inc = tool_inc.execute(GetIncidentInput(incident_id=1))
    record_test(
        "Individual Tools",
        "get_incident",
        res_inc.get("incident_id") == 1 and res_inc.get("incident_number") == "INC-1042",
        f"Fetched Incident {res_inc.get('incident_number')} (Severity: {res_inc.get('severity')})",
    )

    # 2. get_recent_deployments
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)
    tool_dep = registry.get("get_recent_deployments")
    res_dep = tool_dep.execute(GetRecentDeploymentsInput(service_id=1, before_time=now_utc, limit=10))
    record_test(
        "Individual Tools",
        "get_recent_deployments",
        "deployments" in res_dep and len(res_dep["deployments"]) > 0,
        f"Retrieved {len(res_dep.get('deployments', []))} deployments for payment-api",
    )

    # 3. search_incident_events
    tool_ev = registry.get("search_incident_events")
    res_ev = tool_ev.execute(SearchIncidentEventsInput(incident_id=1, limit=10))
    record_test(
        "Individual Tools",
        "search_incident_events",
        "events" in res_ev and len(res_ev["events"]) > 0,
        f"Retrieved {len(res_ev.get('events', []))} timeline events for Incident #1",
    )

    # 4. search_knowledge
    tool_rag = registry.get("search_knowledge")
    res_rag = tool_rag.execute(SearchKnowledgeInput(query="HikariCP connection pool timeout"))
    record_test(
        "Individual Tools",
        "search_knowledge",
        len(res_rag.get("results", [])) > 0,
        f"Found {len(res_rag.get('results', []))} relevant runbook chunks (Score: {res_rag.get('results', [{}])[0].get('score')})",
    )

    # 5. search_logs
    tool_logs = registry.get("search_logs")
    res_logs = tool_logs.execute(SearchLogsInput(keyword="timeout", service_name="payment-api", limit=10))
    record_test(
        "Individual Tools",
        "search_logs",
        res_logs.get("total_returned", 0) > 0,
        f"Found {res_logs.get('total_returned')} matching log entries",
    )

    # 6. get_service_metrics
    tool_met = registry.get("get_service_metrics")
    res_met = tool_met.execute(GetServiceMetricsInput(service_name="payment-api", lookback_minutes=1440, limit=20))
    record_test(
        "Individual Tools",
        "get_service_metrics",
        res_met.get("total_data_points", 0) > 0,
        f"Summarized {res_met.get('total_data_points')} metric points across metrics: {list(res_met.get('summary', {}).keys())[:3]}",
    )

    # 7. query_tickets
    tool_qtix = registry.get("query_tickets")
    res_qtix = tool_qtix.execute(QueryTicketsInput(incident_id=1, limit=5))
    record_test(
        "Individual Tools",
        "query_tickets",
        res_qtix.get("total", 0) > 0,
        f"Retrieved {res_qtix.get('total')} linked tickets",
    )

    # 8. create_ticket
    tool_ctix = registry.get("create_ticket")
    unique_title = f"Tool Matrix Remediation Ticket - {uuid.uuid4().hex[:6]}"
    res_ctix = tool_ctix.execute(CreateTicketInput(
        incident_id=1,
        title=unique_title,
        description="Created during automated tool matrix evaluation.",
        priority="HIGH",
        created_by_user_id=1,
    ))
    record_test(
        "Individual Tools",
        "create_ticket",
        res_ctix.get("status") == "CREATED" and res_ctix.get("ticket_number", "").startswith("TICK-"),
        f"Created ticket {res_ctix.get('ticket_number')} (ID: {res_ctix.get('ticket_id')})",
    )

    # 9. query_database_readonly
    tool_sql = registry.get("query_database_readonly")
    res_sql = tool_sql.execute(ReadOnlySqlInput(
        query="SELECT service_id, service_name, environment FROM core.services ORDER BY service_id LIMIT 3"
    ))
    record_test(
        "Individual Tools",
        "query_database_readonly",
        res_sql.get("row_count") == 3,
        f"Safely executed SELECT and returned {res_sql.get('row_count')} rows with columns {res_sql.get('columns')}",
    )

    # ------------------------------------------------------------------ #
    # Part 2: Multi-Tool Composite Scenarios
    # ------------------------------------------------------------------ #
    print("\n=== PART 2: Multi-Tool Composite Scenarios ===")

    # Scenario A: Performance Spike Investigation (Incident + Metrics + Logs)
    inc = tool_inc.execute(GetIncidentInput(incident_id=1))
    metrics = tool_met.execute(GetServiceMetricsInput(service_name="payment-api", lookback_minutes=60))
    logs = tool_logs.execute(SearchLogsInput(keyword="timeout", service_name="payment-api", limit=5))
    record_test(
        "Composite Scenarios",
        "Scenario A (Incident + Metrics + Logs)",
        bool(inc and metrics.get("total_data_points") is not None and logs.get("total_returned") is not None),
        f"Grounded incident '{inc['title']}' with {metrics.get('total_data_points')} telemetry metrics and {logs.get('total_returned')} logs",
    )

    # Scenario B: Deployment Correlation (Deployment + Logs + SQL)
    deps = tool_dep.execute(GetRecentDeploymentsInput(service_id=1, before_time=now_utc, limit=10))
    sql_check = tool_sql.execute(ReadOnlySqlInput(query="SELECT COUNT(*) AS total_incidents FROM core.incidents"))
    record_test(
        "Composite Scenarios",
        "Scenario B (Deployment + SQL Analytics)",
        len(deps.get("deployments", [])) > 0 and sql_check.get("row_count") == 1,
        f"Correlated {len(deps.get('deployments', []))} deployments against {sql_check.get('rows', [{}])[0].get('total_incidents')} total incidents",
    )

    # Scenario C: Guided Remediation (Knowledge RAG + Create Ticket)
    rag_rec = tool_rag.execute(SearchKnowledgeInput(query="connection pool exhaustion"))
    remediation_tix = tool_ctix.execute(CreateTicketInput(
        incident_id=1,
        title="Apply HikariCP connection pool scale-out",
        description=rag_rec["results"][0]["content"][:100],
        priority="HIGH",
        created_by_user_id=1,
    ))
    record_test(
        "Composite Scenarios",
        "Scenario C (Knowledge RAG + Ticket Creation)",
        remediation_tix.get("status") == "CREATED",
        f"Transformed runbook recommendation into ticket {remediation_tix.get('ticket_number')}",
    )

    # ------------------------------------------------------------------ #
    # Part 3: Security & Safety Guardrails
    # ------------------------------------------------------------------ #
    print("\n=== PART 3: Security & Safety Guardrails ===")

    # Guard 1: Drop Table Rejection
    res_drop = tool_sql.execute(ReadOnlySqlInput(query="DROP TABLE core.services CASCADE;"))
    record_test(
        "Security Guardrails",
        "SQL DROP TABLE rejection",
        res_drop.get("status", "").upper() == "ERROR" and "read-only" in res_drop.get("error", "").lower(),
        f"Blocked malicious statement: '{res_drop.get('error')}'",
    )

    # Guard 2: Delete Rejection
    res_del = tool_sql.execute(ReadOnlySqlInput(query="DELETE FROM core.incidents WHERE incident_id = 1;"))
    record_test(
        "Security Guardrails",
        "SQL DELETE statement rejection",
        res_del.get("status", "").upper() == "ERROR" and "read-only" in res_del.get("error", "").lower(),
        f"Blocked destructive statement: '{res_del.get('error')}'",
    )

    # Guard 3: Update Rejection
    res_upd = tool_sql.execute(ReadOnlySqlInput(query="UPDATE core.users SET email = 'hacked@local';"))
    record_test(
        "Security Guardrails",
        "SQL UPDATE statement rejection",
        res_upd.get("status", "").upper() == "ERROR" and "read-only" in res_upd.get("error", "").lower(),
        f"Blocked modification statement: '{res_upd.get('error')}'",
    )

    # Guard 4: Insert Rejection
    res_ins = tool_sql.execute(ReadOnlySqlInput(query="INSERT INTO core.users (full_name) VALUES ('Hacker');"))
    record_test(
        "Security Guardrails",
        "SQL INSERT statement rejection",
        res_ins.get("status", "").upper() == "ERROR" and "read-only" in res_ins.get("error", "").lower(),
        f"Blocked injection statement: '{res_ins.get('error')}'",
    )

    # Guard 5: System table isolation
    res_shadow = tool_sql.execute(ReadOnlySqlInput(query="SELECT * FROM pg_shadow;"))
    record_test(
        "Security Guardrails",
        "pg_shadow system catalog protection",
        res_shadow.get("status", "").upper() == "ERROR",
        f"Blocked system catalog access: '{res_shadow.get('error')}'",
    )

    print("\n" + "=" * 70)
    print(f"Tool Matrix Evaluation Completed: {matrix_results['passed']} PASSED, {matrix_results['failed']} FAILED")
    print("=" * 70)

    db.close()
    return matrix_results


if __name__ == "__main__":
    results = run_tool_evaluation_matrix()
    if results["failed"] > 0:
        sys.exit(1)
