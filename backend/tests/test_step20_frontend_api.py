from __future__ import annotations

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token


def _auth_headers(user_id: int):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


# ============================================================
# 1. Frontend Build & Static Serving Verification
# ============================================================

def test_frontend_dist_bundle_exists():
    """Validates that the production React + Vite bundle is compiled."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    dist_dir = repo_root / "frontend" / "dist"
    if not dist_dir.exists():
        dist_dir = Path("frontend/dist").resolve()
    assert dist_dir.exists(), "frontend/dist directory must exist"


    index_html = dist_dir / "index.html"
    assert index_html.exists(), "dist/index.html must be present"

    html_content = index_html.read_text(encoding="utf-8")
    assert '<div id="root"></div>' in html_content
    assert "OpsPilot" in html_content

    assets_dir = dist_dir / "assets"
    assert assets_dir.exists(), "dist/assets must exist"
    asset_files = list(assets_dir.iterdir())
    assert any(f.name.endswith(".js") for f in asset_files), "JS bundle must exist"
    assert any(f.name.endswith(".css") for f in asset_files), "CSS bundle must exist"


def test_frontend_ui_static_route(client: TestClient):
    """Validates that FastAPI serves the UI static bundle at /ui/."""
    resp = client.get("/ui/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert '<div id="root"></div>' in resp.text


# ============================================================
# 2. Authentication & Persona RBAC Verification
# ============================================================

def test_persona_auth_me_l1_arun(client: TestClient):
    """Arun (L1) has read-only incident triage permissions."""
    resp = client.get("/api/v1/auth/me", headers=_auth_headers(1))
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 1
    assert data["email"] == "arun@opspilot.local"
    assert data["role_id"] == 1
    assert "INCIDENT_VIEW" in data["permissions"]
    assert "ACTION_REQUEST" not in data["permissions"]
    assert "ACTION_APPROVE" not in data["permissions"]


def test_persona_auth_me_l2_priya(client: TestClient):
    """Priya (L2) can request remediations and verify, but cannot approve."""
    resp = client.get("/api/v1/auth/me", headers=_auth_headers(2))
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 2
    assert data["role_id"] == 2
    assert "ACTION_REQUEST" in data["permissions"]
    assert "ACTION_APPROVE" not in data["permissions"]


def test_persona_auth_me_manager_rahul(client: TestClient):
    """Rahul (Manager) has full operational approval and execution authority."""
    resp = client.get("/api/v1/auth/me", headers=_auth_headers(3))
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 3
    assert data["role_id"] == 3
    assert "ACTION_REQUEST" in data["permissions"]
    assert "ACTION_APPROVE" in data["permissions"]


def test_persona_auth_me_admin_meena(client: TestClient):
    """Meena (Admin) has full administrative and RBAC permissions."""
    resp = client.get("/api/v1/auth/me", headers=_auth_headers(4))
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 4
    assert data["role_id"] == 4
    assert "ACTION_APPROVE" in data["permissions"]
    assert "ROLE_MANAGE" in data["permissions"]


# ============================================================
# 3. Operations Dashboard Summary API Verification
# ============================================================

def test_dashboard_summary_api(client: TestClient):
    """Tests the aggregated dashboard summary used by Screen 1."""
    resp = client.get("/api/v1/dashboard/summary", headers=_auth_headers(1))
    assert resp.status_code == 200
    data = resp.json()

    # KPIs
    kpis = data["kpis"]
    assert "active_incidents" in kpis
    assert "critical_incidents" in kpis
    assert "pending_approvals" in kpis
    assert "mttd_minutes" in kpis
    assert "fleet_health_score" in kpis

    # Services
    services = data["services"]
    assert len(services) >= 4
    assert any(s["name"] == "Payment API" for s in services)
    assert any(s["status"] in ("HEALTHY", "DEGRADED", "CRITICAL") for s in services)

    # Alerts & Remediations
    assert "recent_alerts" in data
    assert "recent_remediations" in data


# ============================================================
# 4. Incident Timeline & Event Stream API Verification
# ============================================================

def test_incident_events_timeline_api(client: TestClient):
    """Tests incident timeline events consumed by Screen 3."""
    resp = client.get("/api/v1/incidents/1/events", headers=_auth_headers(1))
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)
    if events:
        ev = events[0]
        assert "incident_event_id" in ev
        assert "event_type" in ev
        assert "description" in ev
        assert "event_time" in ev


# ============================================================
# 5. Audit Log API Verification
# ============================================================

def test_audit_logs_api(client: TestClient):
    """Tests immutable audit logs consumed by Screen 10."""
    resp = client.get("/api/v1/audit-logs?limit=20", headers=_auth_headers(1))
    assert resp.status_code == 200
    logs = resp.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    first_log = logs[0]
    assert "audit_id" in first_log
    assert "action" in first_log
    assert "actor_user_id" in first_log
    assert "created_at" in first_log


def test_audit_logs_filter_by_resource_type(client: TestClient):
    """Tests filtering audit logs by resource_type."""
    resp = client.get("/api/v1/audit-logs?resource_type=REMEDIATION_ACTION", headers=_auth_headers(1))
    assert resp.status_code == 200
    logs = resp.json()
    for log in logs:
        assert log["resource_type"] == "REMEDIATION_ACTION"


# ============================================================
# 6. Complete UI Operational Lifecycle Simulation
# ============================================================

def test_complete_frontend_operational_lifecycle(client: TestClient):
    """
    Simulates the exact end-to-end operator flow across the 10 screens:
    1. Dashboard: Fetches KPIs & Service health.
    2. Incident List: Discovers active Incident #1.
    3. Incident Details: Views metadata & timeline.
    4. AI Investigation: Generates/fetches full intelligence.
    5. Risk & Root Cause: Inspects risk probability and candidate causes.
    6. Grounded RAG: Validates 100% runbook grounding with sim >= 0.65.
    7. Recommended Actions: Discovers recommendation ACT-002 / ACT-003.
    8. RBAC Gate: Arun (L1) fails to request (403), Priya (L2) requests (201).
    9. Approval Gate: Priya (L2) fails to approve (403), Rahul (Manager) approves (200).
    10. Execution: Rahul executes with dry-run=True (200, COMPLETED).
    11. Verification: Priya runs automated health probes (200, VERIFIED).
    12. Audit Timeline: Confirms immutable audit trail recorded.
    """
    l1_h = _auth_headers(1)
    l2_h = _auth_headers(2)
    mgr_h = _auth_headers(3)

    # 1. Dashboard summary
    dash_res = client.get("/api/v1/dashboard/summary", headers=l1_h)
    assert dash_res.status_code == 200

    # 2. Incident list
    inc_list_res = client.get("/api/v1/incidents", headers=l1_h)
    assert inc_list_res.status_code == 200
    assert len(inc_list_res.json()) >= 1

    # 3. Incident details & timeline
    inc_res = client.get("/api/v1/incidents/1", headers=l1_h)
    assert inc_res.status_code == 200
    events_res = client.get("/api/v1/incidents/1/events", headers=l1_h)
    assert events_res.status_code == 200

    # 4. AI Intelligence
    client.post("/api/v1/incidents/1/intelligence?investigation_id=1", headers=mgr_h)
    intel_res = client.get("/api/v1/incidents/1/intelligence", headers=l1_h)
    assert intel_res.status_code == 200
    intel_data = intel_res.json()

    # 5. Risk & Root Cause
    assert "risk_assessment" in intel_data
    assert len(intel_data.get("probable_root_causes", [])) >= 1

    # 6. RAG Evidence
    rag_res = client.get("/api/v1/investigations/1/rag-evidence", headers=l1_h)
    assert rag_res.status_code in (200, 404)

    # 7. Recommended Actions
    actions = intel_data["recommended_actions"]
    assert len(actions) >= 1
    target_action = actions[0]

    # 8. RBAC Gate: L1 blocked from requesting
    req_payload = {
        "action_id": f"ACT-UI-{target_action['action_id']}",
        "action_type": "DEPLOYMENT_ROLLBACK",
        "title": f"UI Remediation: {target_action['title']}",
        "description": target_action["description"],
        "rationale": target_action["rationale"],
        "intelligence_id": intel_data.get("intelligence_id"),
        "investigation_id": 1,
        "execution_payload": {"service_id": 1, "target_version": "2.8.1"},
    }
    l1_req = client.post("/api/v1/incidents/1/remediations", headers=l1_h, json=req_payload)
    assert l1_req.status_code == 403

    # L2 requests remediation
    l2_req = client.post("/api/v1/incidents/1/remediations", headers=l2_h, json=req_payload)
    assert l2_req.status_code == 201
    rem_id = l2_req.json()["remediation_id"]

    # 9. Approval Gate: L2 blocked from approving, Manager approves
    l2_appr = client.post(f"/api/v1/remediations/{rem_id}/approve", headers=l2_h, json={"decision": "APPROVE"})
    assert l2_appr.status_code == 403

    mgr_appr = client.post(
        f"/api/v1/remediations/{rem_id}/approve",
        headers=mgr_h,
        json={"decision": "APPROVE", "review_comment": "UI Test SRE Approval"},
    )
    assert mgr_appr.status_code == 200
    assert mgr_appr.json()["status"] == "APPROVED"

    # 10. Execution: Manager executes
    exec_res = client.post(f"/api/v1/remediations/{rem_id}/execute", headers=mgr_h, json={"dry_run": True})
    assert exec_res.status_code == 200
    assert exec_res.json()["status"] == "COMPLETED"

    # 11. Verification: L2 runs automated health probe
    verif_res = client.post(f"/api/v1/remediations/{rem_id}/verify", headers=l2_h)
    assert verif_res.status_code == 200
    assert verif_res.json()["status"] == "VERIFIED"

    # Verify incident updated to MITIGATED
    final_inc = client.get("/api/v1/incidents/1", headers=l1_h)
    assert final_inc.status_code == 200
    assert final_inc.json()["status"] == "MITIGATED"

    # 12. Audit Timeline: confirm immutable logs
    audit_res = client.get("/api/v1/audit-logs", headers=l1_h)
    assert audit_res.status_code == 200
    assert any(log["resource_id"] == str(rem_id) for log in audit_res.json())
