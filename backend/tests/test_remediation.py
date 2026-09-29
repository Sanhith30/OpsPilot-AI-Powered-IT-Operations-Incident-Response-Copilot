from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
import pytest
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.security import create_access_token
from app.models.remediation_action import RemediationAction
from app.remediation.adapters import (
    DEFAULT_ADAPTER_REGISTRY,
    WHITELISTED_ACTION_TYPES,
    AdjustPoolLimitsAdapter,
    DeploymentRollbackAdapter,
    RestartServiceInstanceAdapter,
    RunbookStepExecutionAdapter,
)
from app.remediation.engine import RemediationExecutionEngine
from app.remediation.verifier import RemediationVerifier
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.remediation_repository import RemediationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.remediation import (
    RemediationApprovalRequest,
    RemediationCreateRequest,
    RemediationExecuteRequest,
    RemediationResponse,
)
from app.services.audit_log_service import AuditLogService
from app.services.remediation_service import RemediationService


# ============================================================
# Helpers
# ============================================================

def _build_service(db_session) -> RemediationService:
    repo = RemediationRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    inv_repo = InvestigationRepository(db_session)
    user_repo = UserRepository(db_session)
    audit_repo = AuditLogRepository(db_session)
    audit_svc = AuditLogService(db_session, audit_repo, user_repo)
    return RemediationService(
        db=db_session,
        repository=repo,
        incident_repository=inc_repo,
        investigation_repository=inv_repo,
        audit_log_service=audit_svc,
    )


def _auth_headers(user_id: int = 1):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


# ============================================================
# 1. Schema & Validation Tests
# ============================================================

def test_remediation_schema_valid():
    req = RemediationCreateRequest(
        action_id="ACT-001",
        action_type="DEPLOYMENT_ROLLBACK",
        title="Rollback release 2.9.0",
        description="Revert to 2.8.1",
        rationale="Connection pool regression",
        execution_payload={"service_id": 1, "target_version": "2.8.1"},
    )
    assert req.action_type == "DEPLOYMENT_ROLLBACK"
    assert req.execution_payload["target_version"] == "2.8.1"


def test_remediation_schema_rejects_unwhitelisted_action():
    with pytest.raises(PydanticValidationError):
        RemediationCreateRequest(
            action_id="ACT-002",
            action_type="ARBITRARY_BASH_SCRIPT",  # Not in RemediationActionType
            title="Run shell",
            description="bash script",
            rationale="test",
        )


# ============================================================
# 2. Adapter Registry & Dry-Run Tests
# ============================================================

def test_adapter_whitelist_contains_only_safe_actions():
    expected = {
        "DEPLOYMENT_ROLLBACK",
        "RESTART_SERVICE_INSTANCE",
        "ADJUST_POOL_LIMITS",
        "RUNBOOK_STEP_EXECUTION",
    }
    assert WHITELISTED_ACTION_TYPES == expected


def test_deployment_rollback_adapter_dry_run():
    adapter = DeploymentRollbackAdapter()
    res = adapter.execute(
        payload={"service_id": 1, "target_version": "2.8.1"},
        dry_run=True,
    )
    assert res.success is True
    assert res.dry_run is True
    assert "Dry-run" in res.details["message"]


def test_adjust_pool_limits_adapter_bounds():
    adapter = AdjustPoolLimitsAdapter()
    # Out of bounds (> 500)
    res_invalid = adapter.execute(payload={"service_id": 1, "pool_size": 9999})
    assert res_invalid.success is False
    assert "Invalid pool_size" in res_invalid.error

    # Valid bounds
    res_valid = adapter.execute(payload={"service_id": 1, "pool_size": 75}, dry_run=True)
    assert res_valid.success is True
    assert res_valid.details["target_pool_size"] == 75


def test_execution_engine_rejects_unsupported_action():
    engine = RemediationExecutionEngine()
    with pytest.raises(ValidationError) as exc:
        engine.execute(action_type="UNKNOWN_ACTION", payload={})
    assert "not permitted" in str(exc.value)


# ============================================================
# 3. State Machine & Transition Tests
# ============================================================

def test_state_machine_approval_and_rejection_flows(db_session):
    service = _build_service(db_session)

    # 1. Create remediation -> PENDING_APPROVAL
    action = service.create_remediation(
        incident_id=1,
        request=RemediationCreateRequest(
            action_id="ACT-001",
            action_type="DEPLOYMENT_ROLLBACK",
            title="Rollback Payment API",
            description="Revert to 2.8.1",
            rationale="High 504 errors",
        ),
        user_id=1,
    )
    assert action.status == "PENDING_APPROVAL"

    # 2. More info flow
    more_info = service.review_remediation(
        remediation_id=action.remediation_id,
        review=RemediationApprovalRequest(
            decision="REQUEST_MORE_INFO",
            review_comment="Please provide target commit hash",
        ),
        user_id=1,
    )
    assert more_info.status == "REQUEST_MORE_INFO"

    # 3. Approve from REQUEST_MORE_INFO
    approved = service.review_remediation(
        remediation_id=action.remediation_id,
        review=RemediationApprovalRequest(
            decision="APPROVE",
            review_comment="Target commit verified",
        ),
        user_id=1,
    )
    assert approved.status == "APPROVED"
    assert approved.approved_by_user_id == 1
    assert approved.approved_at is not None


def test_invalid_state_transitions_rejected(db_session):
    service = _build_service(db_session)

    action = service.create_remediation(
        incident_id=1,
        request=RemediationCreateRequest(
            action_id="ACT-001",
            action_type="RESTART_SERVICE_INSTANCE",
            title="Restart pod",
            description="Restart",
            rationale="Test",
        ),
        user_id=1,
    )

    # Cannot execute while in PENDING_APPROVAL
    with pytest.raises(ValidationError) as exc:
        service.execute_remediation(
            remediation_id=action.remediation_id,
            user_id=1,
        )
    assert "must be in APPROVED status" in str(exc.value)

    # Cannot verify while in PENDING_APPROVAL
    with pytest.raises(ValidationError) as exc:
        service.verify_remediation(
            remediation_id=action.remediation_id,
            user_id=1,
        )
    assert "Cannot verify remediation" in str(exc.value)


# ============================================================
# 4. Strict Idempotency Tests
# ============================================================

def test_execution_is_strictly_idempotent(db_session):
    service = _build_service(db_session)

    # Create and approve
    action = service.create_remediation(
        incident_id=1,
        request=RemediationCreateRequest(
            action_id="ACT-002",
            action_type="ADJUST_POOL_LIMITS",
            title="Increase pool size",
            description="Adjust pool size to 60",
            rationale="Slight pool exhaustion",
            execution_payload={"pool_size": 60},
        ),
        user_id=1,
    )
    service.review_remediation(
        remediation_id=action.remediation_id,
        review=RemediationApprovalRequest(decision="APPROVE"),
        user_id=1,
    )

    # First execution succeeds -> status becomes COMPLETED
    executed = service.execute_remediation(
        remediation_id=action.remediation_id,
        user_id=1,
        dry_run=True,
    )
    assert executed.status == "COMPLETED"

    # Second execution attempt must fail with ConflictError (HTTP 409)
    with pytest.raises(ConflictError) as exc:
        service.execute_remediation(
            remediation_id=action.remediation_id,
            user_id=1,
            dry_run=True,
        )
    assert "already been executed" in str(exc.value)


# ============================================================
# 5. Automated Verification & Incident Status Update Tests
# ============================================================

def test_verification_success_updates_incident(db_session):
    service = _build_service(db_session)

    action = service.create_remediation(
        incident_id=1,
        request=RemediationCreateRequest(
            action_id="ACT-003",
            action_type="DEPLOYMENT_ROLLBACK",
            title="Rollback Payment API",
            description="Revert",
            rationale="Regression",
        ),
        user_id=1,
    )
    service.review_remediation(
        remediation_id=action.remediation_id,
        review=RemediationApprovalRequest(decision="APPROVE"),
        user_id=1,
    )
    service.execute_remediation(
        remediation_id=action.remediation_id,
        user_id=1,
        dry_run=True,
    )

    # Verify successfully
    verified = service.verify_remediation(
        remediation_id=action.remediation_id,
        user_id=1,
        force_fail=False,
    )

    assert verified.status == "VERIFIED"
    assert verified.verification_status == "VERIFIED"
    assert verified.verified_at is not None

    # Check that incident status was updated
    incident = service.incident_repository.get_by_id(1)
    assert incident.status == "MITIGATED"


def test_verification_failure_records_failed_status(db_session):
    service = _build_service(db_session)

    action = service.create_remediation(
        incident_id=1,
        request=RemediationCreateRequest(
            action_id="ACT-004",
            action_type="RESTART_SERVICE_INSTANCE",
            title="Restart",
            description="Restart",
            rationale="Test",
        ),
        user_id=1,
    )
    service.review_remediation(
        remediation_id=action.remediation_id,
        review=RemediationApprovalRequest(decision="APPROVE"),
        user_id=1,
    )
    service.execute_remediation(
        remediation_id=action.remediation_id,
        user_id=1,
        dry_run=True,
    )

    # Force verification failure
    failed = service.verify_remediation(
        remediation_id=action.remediation_id,
        user_id=1,
        force_fail=True,
    )

    assert failed.status == "VERIFICATION_FAILED"
    assert failed.verification_status == "FAILED"


# ============================================================
# 6. Audit Trail Tests
# ============================================================

def test_remediation_records_complete_audit_trail(db_session):
    service = _build_service(db_session)

    action = service.create_remediation(
        incident_id=1,
        request=RemediationCreateRequest(
            action_id="ACT-005",
            action_type="RUNBOOK_STEP_EXECUTION",
            title="Runbook Step 1",
            description="Execute payment reset step",
            rationale="Reset runbook",
        ),
        user_id=1,
    )
    service.review_remediation(
        remediation_id=action.remediation_id,
        review=RemediationApprovalRequest(decision="APPROVE"),
        user_id=1,
    )
    service.execute_remediation(
        remediation_id=action.remediation_id,
        user_id=1,
        dry_run=True,
    )
    service.verify_remediation(
        remediation_id=action.remediation_id,
        user_id=1,
        force_fail=False,
    )

    logs = service.audit_log_service.get_by_resource(
        resource_type="REMEDIATION_ACTION",
        resource_id=str(action.remediation_id),
    )

    action_names = [log.action for log in logs]
    assert "REMEDIATION_REQUESTED" in action_names
    assert "REMEDIATION_APPROVED" in action_names
    assert "REMEDIATION_EXECUTED" in action_names
    assert "REMEDIATION_VERIFIED" in action_names


# ============================================================
# 7. API Routes & RBAC Tests
# ============================================================

def test_api_remediation_rbac_enforcement(client):
    """
    Validates role-based access control across remediation endpoints:
    - User 1 (L1 Engineer): has INCIDENT_VIEW, but NOT ACTION_REQUEST or ACTION_APPROVE.
    - User 2 (L2 Engineer): has ACTION_REQUEST, but NOT ACTION_APPROVE.
    - User 3 (Manager): has both ACTION_REQUEST and ACTION_APPROVE.
    """
    l1_headers = _auth_headers(1)
    l2_headers = _auth_headers(2)
    mgr_headers = _auth_headers(3)

    payload = {
        "action_id": "ACT-RBAC-001",
        "action_type": "DEPLOYMENT_ROLLBACK",
        "title": "RBAC Rollback Test",
        "description": "Testing permissions",
        "rationale": "RBAC check",
        "execution_payload": {"target_version": "2.8.1"},
    }

    # 1. L1 cannot create remediation (requires ACTION_REQUEST -> 403 Forbidden)
    l1_create = client.post("/api/v1/incidents/1/remediations", headers=l1_headers, json=payload)
    assert l1_create.status_code == 403

    # 2. L2 can create remediation (has ACTION_REQUEST -> 201 Created)
    l2_create = client.post("/api/v1/incidents/1/remediations", headers=l2_headers, json=payload)
    assert l2_create.status_code == 201
    rem_id = l2_create.json()["remediation_id"]

    # 3. L1 can view remediation (has INCIDENT_VIEW -> 200 OK)
    l1_view = client.get(f"/api/v1/remediations/{rem_id}", headers=l1_headers)
    assert l1_view.status_code == 200

    # 4. L2 cannot approve remediation (requires ACTION_APPROVE -> 403 Forbidden)
    l2_appr = client.post(
        f"/api/v1/remediations/{rem_id}/approve",
        headers=l2_headers,
        json={"decision": "APPROVE"},
    )
    assert l2_appr.status_code == 403

    # 5. Manager can approve remediation (has ACTION_APPROVE -> 200 OK)
    mgr_appr = client.post(
        f"/api/v1/remediations/{rem_id}/approve",
        headers=mgr_headers,
        json={"decision": "APPROVE"},
    )
    assert mgr_appr.status_code == 200

    # 6. L2 cannot execute remediation (requires ACTION_APPROVE -> 403 Forbidden)
    l2_exec = client.post(
        f"/api/v1/remediations/{rem_id}/execute",
        headers=l2_headers,
        json={"dry_run": True},
    )
    assert l2_exec.status_code == 403

    # 7. Manager can execute remediation (has ACTION_APPROVE -> 200 OK)
    mgr_exec = client.post(
        f"/api/v1/remediations/{rem_id}/execute",
        headers=mgr_headers,
        json={"dry_run": True},
    )
    assert mgr_exec.status_code == 200

    # 8. L1 cannot verify remediation (requires ACTION_REQUEST -> 403 Forbidden)
    l1_verif = client.post(f"/api/v1/remediations/{rem_id}/verify", headers=l1_headers)
    assert l1_verif.status_code == 403

    # 9. L2 can verify remediation (has ACTION_REQUEST -> 200 OK)
    l2_verif = client.post(f"/api/v1/remediations/{rem_id}/verify", headers=l2_headers)
    assert l2_verif.status_code == 200


def test_api_remediation_lifecycle_full(client):
    headers = _auth_headers(3)  # Manager with both ACTION_REQUEST and ACTION_APPROVE

    # 1. Create remediation request (POST /api/v1/incidents/1/remediations)
    create_resp = client.post(
        "/api/v1/incidents/1/remediations",
        headers=headers,
        json={
            "action_id": "ACT-API-001",
            "action_type": "DEPLOYMENT_ROLLBACK",
            "title": "API Test Rollback",
            "description": "Rollback deployment",
            "rationale": "High latency",
            "execution_payload": {"target_version": "2.8.1"},
        },
    )
    assert create_resp.status_code == 201
    rem_data = create_resp.json()
    rem_id = rem_data["remediation_id"]
    assert rem_data["status"] == "PENDING_APPROVAL"

    # 2. Get incident remediations (GET /api/v1/incidents/1/remediations)
    get_list = client.get("/api/v1/incidents/1/remediations", headers=headers)
    assert get_list.status_code == 200
    assert any(r["remediation_id"] == rem_id for r in get_list.json())

    # 3. Get single remediation (GET /api/v1/remediations/{id})
    get_single = client.get(f"/api/v1/remediations/{rem_id}", headers=headers)
    assert get_single.status_code == 200
    assert get_single.json()["action_id"] == "ACT-API-001"

    # 4. Approve (POST /api/v1/remediations/{id}/approve)
    approve_resp = client.post(
        f"/api/v1/remediations/{rem_id}/approve",
        headers=headers,
        json={"decision": "APPROVE", "review_comment": "Approved by SRE Lead"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"

    # 5. Execute (POST /api/v1/remediations/{id}/execute)
    exec_resp = client.post(
        f"/api/v1/remediations/{rem_id}/execute",
        headers=headers,
        json={"dry_run": True},
    )
    assert exec_resp.status_code == 200
    assert exec_resp.json()["status"] == "COMPLETED"

    # 6. Idempotency on execute (Second POST returns 409 Conflict)
    dup_exec_resp = client.post(
        f"/api/v1/remediations/{rem_id}/execute",
        headers=headers,
        json={"dry_run": True},
    )
    assert dup_exec_resp.status_code == 409

    # 7. Verify (POST /api/v1/remediations/{id}/verify)
    verif_resp = client.post(
        f"/api/v1/remediations/{rem_id}/verify",
        headers=headers,
    )
    assert verif_resp.status_code == 200
    assert verif_resp.json()["status"] == "VERIFIED"


def test_api_remediation_rejection_flow(client):
    headers = _auth_headers(3)

    create_resp = client.post(
        "/api/v1/incidents/1/remediations",
        headers=headers,
        json={
            "action_id": "ACT-API-REJECT",
            "action_type": "RESTART_SERVICE_INSTANCE",
            "title": "Unnecessary restart",
            "description": "Restart pod",
            "rationale": "Premature action",
        },
    )
    assert create_resp.status_code == 201
    rem_id = create_resp.json()["remediation_id"]

    reject_resp = client.post(
        f"/api/v1/remediations/{rem_id}/reject",
        headers=headers,
        json={"decision": "REJECT", "review_comment": "Metrics do not warrant restart"},
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "REJECTED"


# ============================================================
# 8. Step 18 -> Step 19 Payment API Remediation Scenario
# ============================================================

def test_step18_to_step19_payment_api_scenario(client, db_session):
    """
    Validates full end-to-end integration:
    1. Incident Intelligence produces RecommendedAction ACT-003 (Rollback).
    2. SRE operator requests remediation matching ACT-003.
    3. Human reviewer approves remediation.
    4. Adapter executes rollback simulation.
    5. Health verifier validates error rate stabilization.
    6. Incident is updated to MITIGATED.
    """
    mgr_headers = _auth_headers(3)
    l2_headers = _auth_headers(2)

    # 1. Generate intelligence for incident 1 / investigation 1 to ensure it exists
    gen_resp = client.post(
        "/api/v1/incidents/1/intelligence?investigation_id=1",
        headers=mgr_headers,
    )
    assert gen_resp.status_code == 200

    # Fetch latest intelligence
    intel_resp = client.get("/api/v1/incidents/1/intelligence", headers=mgr_headers)
    assert intel_resp.status_code == 200
    intel_data = intel_resp.json()

    # Find recommendation from Step 18 intelligence
    rec = next(
        (a for a in intel_data["recommended_actions"] if a["action_type"] in ("ROLLBACK", "MITIGATE", "INVESTIGATE")),
        intel_data["recommended_actions"][0],
    )
    assert rec is not None
    assert rec["requires_human_approval"] is True

    # 2. Operator (L2) requests remediation based on recommendation
    rem_req = {
        "action_id": rec["action_id"],
        "action_type": "DEPLOYMENT_ROLLBACK",
        "title": f"Remediate: {rec['title']}",
        "description": rec["description"],
        "rationale": rec["rationale"],
        "intelligence_id": intel_data.get("intelligence_id"),
        "investigation_id": intel_data.get("investigation_id"),
        "execution_payload": {
            "service_id": 1,
            "target_version": "2.8.1",
            "current_version": "2.9.0",
        },
    }

    create_resp = client.post(
        "/api/v1/incidents/1/remediations",
        headers=l2_headers,
        json=rem_req,
    )
    assert create_resp.status_code == 201
    rem_id = create_resp.json()["remediation_id"]

    # 3. Manager approves
    appr_resp = client.post(
        f"/api/v1/remediations/{rem_id}/approve",
        headers=mgr_headers,
        json={"decision": "APPROVE", "review_comment": "Approved Payment API rollback to 2.8.1"},
    )
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "APPROVED"

    # 4. Manager executes rollback
    exec_resp = client.post(
        f"/api/v1/remediations/{rem_id}/execute",
        headers=mgr_headers,
        json={"dry_run": True},
    )
    assert exec_resp.status_code == 200
    assert exec_resp.json()["status"] == "COMPLETED"

    # 5. Operator runs automated verification
    verif_resp = client.post(
        f"/api/v1/remediations/{rem_id}/verify",
        headers=l2_headers,
    )
    assert verif_resp.status_code == 200
    assert verif_resp.json()["status"] == "VERIFIED"

    # 6. Verify incident status is MITIGATED
    inc_resp = client.get("/api/v1/incidents/1", headers=mgr_headers)
    assert inc_resp.status_code == 200
    assert inc_resp.json()["status"] == "MITIGATED"
