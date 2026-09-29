from __future__ import annotations

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_investigation_graph
from app.core.security import create_access_token
from app.main import app


def _auth(user_id: int):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


class _FakeInvestigationGraph:
    """Deterministic LangGraph runner that provides multi-agent evidence and RAG citations."""
    class _Wrapper:
        def invoke(self, state):
            return {
                "status": "COMPLETED",
                "current_stage": "completed",
                "final_summary": "Investigation into Payment API database connection pool exhaustion completed.",
                "tool_results": [
                    {
                        "tool_name": "get_incident",
                        "status": "SUCCESS",
                        "data": {"incident_number": "INC-1042", "title": "Payment API elevated error rate"},
                    },
                    {
                        "tool_name": "search_knowledge",
                        "status": "SUCCESS",
                        "data": {"results": [{"chunk_id": "chunk-pay-101", "score": 0.885}]},
                    },
                ],
                "evidence": [
                    {
                        "evidence_type": "LOG",
                        "source": "Payment API",
                        "content": "FATAL: remaining connection slots are reserved for non-replication superuser connections",
                        "metadata": {"severity": "ERROR"},
                    },
                    {
                        "evidence_type": "METRIC",
                        "source": "Prometheus",
                        "content": "database_connection_pool_active = 50/50 (exhausted)",
                        "metadata": {"metric": "pool_active"},
                    },
                ],
                "findings": [
                    {
                        "finding_type": "ROOT_CAUSE",
                        "finding_text": "PostgreSQL connection pool exhausted by v2.9.0 deployment.",
                        "evidence_refs": [],
                    }
                ],
                "rag_query": "Why is Payment API database timing out?",
                "rag_context": "Runbook: Payment API database connection pool exhaustion...",
                "rag_citations": [
                    {
                        "citation_id": "KB-1",
                        "chunk_id": "chunk-pay-101",
                        "document_id": "doc-payment-timeouts",
                        "source_name": "payment-api-database-timeouts.md",
                        "source_type": "FILE",
                        "version_number": 1,
                        "score": 0.885,
                        "title": "Payment API Database Timeouts Runbook",
                        "content": "Check database connection pool timeouts and max connections.",
                    }
                ],
                "risk_prediction": None,
            }

    @property
    def graph(self):
        return self._Wrapper()


# ============================================================
# Step 21: Full System Integration Test
# Validates the complete user journey:
# Frontend -> Auth -> FastAPI -> PostgreSQL -> LangGraph ->
# RAG -> Risk -> Incident Intelligence -> Remediation ->
# Verification -> Incident Mitigated -> Audit Trail
# ============================================================

def test_full_system_integration_lifecycle(client: TestClient):
    """
    Executes the complete OpsPilot operational lifecycle:
    1. Authentication: Login as Arun (L1), Priya (L2), Rahul (Manager).
    2. Operations Dashboard: Summary KPIs and service catalog health.
    3. Incident Discovery: Incident #1 details, status, and event timeline.
    4. LangGraph Multi-Agent Investigation: Runs graph with tools, collects evidence, persists to DB.
    5. Grounded RAG Runbooks: Validates retrieved knowledge citations with sim >= 0.65.
    6. Incident Intelligence Synthesis: Correlates signals, computes risk, ranks root causes, recommends actions.
    7. Remediation Request & RBAC Gate: Arun (L1) blocked (403), Priya (L2) creates remediation (201, PENDING_APPROVAL).
    8. Human Approval Gate: Priya (L2) blocked from approving (403), Rahul (Manager) approves (200, APPROVED).
    9. Idempotent Execution: Safe adapter dry-run executes (200, COMPLETED), duplicate request blocked (409 Conflict).
    10. Automated Verification Probes: Post-remediation health check passes (200, VERIFIED).
    11. Incident Auto-Mitigation: Incident status transitions to MITIGATED, event recorded.
    12. Immutable Audit Trail: Verifies complete audit record trace from request to verification.
    """
    app.dependency_overrides[get_investigation_graph] = lambda: _FakeInvestigationGraph()

    try:
        # Define headers for all three personas
        l1_headers = _auth(1)   # Arun (L1 Engineer)
        l2_headers = _auth(2)   # Priya (L2 Engineer)
        mgr_headers = _auth(3)  # Rahul (SRE Manager)

        # ------------------------------------------------------------
        # 1. Authentication & Dashboard
        # ------------------------------------------------------------
        login_resp = client.post("/api/v1/auth/login", json={"email": "arun@opspilot.local", "password": "OpsPilot@123"})
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()

        me_resp = client.get("/api/v1/auth/me", headers=l1_headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "arun@opspilot.local"
        assert me_resp.json()["role_id"] == 1

        dash_resp = client.get("/api/v1/dashboard/summary", headers=l1_headers)
        assert dash_resp.status_code == 200
        dash_data = dash_resp.json()
        assert dash_data["kpis"]["fleet_health_score"] > 0
        assert any(s["name"] == "Payment API" for s in dash_data["services"])

        # ------------------------------------------------------------
        # 2. Incident Discovery & Timeline
        # ------------------------------------------------------------
        inc_resp = client.get("/api/v1/incidents/1", headers=l1_headers)
        assert inc_resp.status_code == 200
        incident = inc_resp.json()
        assert incident["incident_id"] == 1
        assert "Payment" in incident["title"]

        events_resp = client.get("/api/v1/incidents/1/events", headers=l1_headers)
        assert events_resp.status_code == 200
        assert len(events_resp.json()) >= 1

        # ------------------------------------------------------------
        # 3. LangGraph Multi-Agent Investigation
        # ------------------------------------------------------------
        inv_create_payload = {
            "incident_id": 1,
            "question": "Investigate root cause of database connection timeouts in Payment API",
            "investigation_type": "ASSISTED",
        }
        inv_resp = client.post("/api/v1/investigations", headers=l1_headers, json=inv_create_payload)
        assert inv_resp.status_code == 200
        inv_data = inv_resp.json()
        inv_id = inv_data["investigation_id"]
        assert inv_data["status"] == "COMPLETED"
        assert inv_data["incident_id"] == 1
        assert len(inv_data["findings"]) >= 1

        # Check RAG evidence endpoint
        rag_resp = client.get(f"/api/v1/investigations/{inv_id}/rag-evidence", headers=l1_headers)
        assert rag_resp.status_code == 200
        rag_citations = rag_resp.json()
        assert isinstance(rag_citations, list)
        assert len(rag_citations) >= 1
        assert rag_citations[0]["score"] >= 0.65

        # ------------------------------------------------------------
        # 4. Incident Intelligence & Operational Decision Engine
        # ------------------------------------------------------------
        gen_intel_resp = client.post(f"/api/v1/incidents/1/intelligence?investigation_id={inv_id}", headers=mgr_headers)
        assert gen_intel_resp.status_code == 200
        intel_data = gen_intel_resp.json()

        # Root cause candidate verification
        assert len(intel_data["probable_root_causes"]) >= 1
        top_cause = intel_data["probable_root_causes"][0]
        assert float(top_cause["confidence"]) > 0
        assert len(top_cause["explanation"]) > 0

        # Risk and decision
        assert intel_data["operational_decision"]["requires_human_approval"] is True
        assert len(intel_data["recommended_actions"]) >= 1

        # Find the top recommendation
        rec = intel_data["recommended_actions"][0]
        assert rec["requires_human_approval"] is True

        # ------------------------------------------------------------
        # 5. Remediation Request & RBAC Gate
        # ------------------------------------------------------------
        rem_payload = {
            "action_id": f"ACT-STEP21-{rec['action_id']}",
            "action_type": "DEPLOYMENT_ROLLBACK",
            "title": f"Step 21 E2E: {rec['title']}",
            "description": rec["description"],
            "rationale": rec["rationale"],
            "intelligence_id": intel_data.get("intelligence_id"),
            "investigation_id": inv_id,
            "execution_payload": {
                "service_id": 1,
                "target_version": "2.8.1",
                "current_version": "2.9.0",
            },
        }

        # Arun (L1) attempt -> 403 Forbidden
        l1_rem_resp = client.post("/api/v1/incidents/1/remediations", headers=l1_headers, json=rem_payload)
        assert l1_rem_resp.status_code == 403

        # Priya (L2) attempt -> 201 Created
        l2_rem_resp = client.post("/api/v1/incidents/1/remediations", headers=l2_headers, json=rem_payload)
        assert l2_rem_resp.status_code == 201
        rem_record = l2_rem_resp.json()
        rem_id = rem_record["remediation_id"]
        assert rem_record["status"] == "PENDING_APPROVAL"

        # ------------------------------------------------------------
        # 6. Human Approval Gate
        # ------------------------------------------------------------
        # Priya (L2) attempt to approve -> 403 Forbidden
        l2_appr_resp = client.post(f"/api/v1/remediations/{rem_id}/approve", headers=l2_headers, json={"decision": "APPROVE"})
        assert l2_appr_resp.status_code == 403

        # Rahul (SRE Manager) approves -> 200 OK, APPROVED
        mgr_appr_resp = client.post(
            f"/api/v1/remediations/{rem_id}/approve",
            headers=mgr_headers,
            json={"decision": "APPROVE", "review_comment": "Step 21 Manager Authorized"},
        )
        assert mgr_appr_resp.status_code == 200
        assert mgr_appr_resp.json()["status"] == "APPROVED"
        assert mgr_appr_resp.json()["approved_by_user_id"] == 3

        # ------------------------------------------------------------
        # 7. Safe Adapter Execution & Strict Idempotency Lock
        # ------------------------------------------------------------
        # First execution succeeds
        exec_resp = client.post(f"/api/v1/remediations/{rem_id}/execute", headers=mgr_headers, json={"dry_run": True})
        assert exec_resp.status_code == 200
        assert exec_resp.json()["status"] == "COMPLETED"
        assert exec_resp.json()["execution_result"]["success"] is True
        assert exec_resp.json()["execution_result"]["dry_run"] is True

        # Duplicate execution attempt must fail with 409 Conflict (Idempotency)
        dup_exec_resp = client.post(f"/api/v1/remediations/{rem_id}/execute", headers=mgr_headers, json={"dry_run": True})
        assert dup_exec_resp.status_code == 409
        assert "already been executed" in dup_exec_resp.json()["detail"].lower()

        # ------------------------------------------------------------
        # 8. Automated Post-Remediation Verification & Incident Mitigated
        # ------------------------------------------------------------
        verif_resp = client.post(f"/api/v1/remediations/{rem_id}/verify", headers=l2_headers)
        assert verif_resp.status_code == 200
        assert verif_resp.json()["status"] == "VERIFIED"
        assert verif_resp.json()["verification_status"] == "VERIFIED"

        # Verify incident #1 status updated to MITIGATED
        updated_inc = client.get("/api/v1/incidents/1", headers=l1_headers).json()
        assert updated_inc["status"] == "MITIGATED"

        # Verify MITIGATION_APPLIED event recorded
        updated_events = client.get("/api/v1/incidents/1/events", headers=l1_headers).json()
        assert any(e["event_type"] == "MITIGATION_APPLIED" for e in updated_events)

        # ------------------------------------------------------------
        # 9. Immutable Audit Trail & Observability
        # ------------------------------------------------------------
        audit_resp = client.get("/api/v1/audit-logs?limit=50", headers=l1_headers)
        assert audit_resp.status_code == 200
        logs = audit_resp.json()
        rem_audit_actions = [log["action"] for log in logs if log["resource_id"] == str(rem_id)]
        assert "REMEDIATION_REQUESTED" in rem_audit_actions
        assert "REMEDIATION_APPROVED" in rem_audit_actions
        assert "REMEDIATION_EXECUTED" in rem_audit_actions
        assert "REMEDIATION_VERIFIED" in rem_audit_actions

    finally:
        app.dependency_overrides.pop(get_investigation_graph, None)
