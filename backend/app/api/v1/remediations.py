from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Request

from app.api.dependencies import (
    get_remediation_service,
    require_permission,
)
from app.schemas.remediation import (
    RemediationApprovalRequest,
    RemediationCreateRequest,
    RemediationExecuteRequest,
    RemediationResponse,
)
from app.services.remediation_service import RemediationService

router = APIRouter(tags=["Remediations"])


@router.post(
    "/incidents/{incident_id}/remediations",
    response_model=RemediationResponse,
    status_code=201,
)
def create_remediation(
    incident_id: int,
    request: RemediationCreateRequest,
    req: Request = None,
    current_user=Depends(require_permission("ACTION_REQUEST")),
    remediation_service: RemediationService = Depends(get_remediation_service),
):
    """
    Request a human-approved remediation action for an incident.
    """
    request_id = getattr(req.state, "request_id", None) if req and hasattr(req, "state") else None
    return remediation_service.create_remediation(
        incident_id=incident_id,
        request=request,
        user_id=current_user.user_id,
        request_id=request_id,
    )


@router.get(
    "/incidents/{incident_id}/remediations",
    response_model=list[RemediationResponse],
)
def get_incident_remediations(
    incident_id: int,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    remediation_service: RemediationService = Depends(get_remediation_service),
):
    """
    List all remediation actions requested for an incident.
    """
    return remediation_service.get_by_incident(incident_id)


@router.get(
    "/remediations/{remediation_id}",
    response_model=RemediationResponse,
)
def get_remediation(
    remediation_id: int,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    remediation_service: RemediationService = Depends(get_remediation_service),
):
    """
    Retrieve details of a specific remediation action.
    """
    return remediation_service.get_by_id(remediation_id)


@router.post(
    "/remediations/{remediation_id}/approve",
    response_model=RemediationResponse,
)
def approve_remediation(
    remediation_id: int,
    body: RemediationApprovalRequest | None = None,
    req: Request = None,
    current_user=Depends(require_permission("ACTION_APPROVE")),
    remediation_service: RemediationService = Depends(get_remediation_service),
):
    """
    Approve a pending remediation action (strictly requires ACTION_APPROVE).
    """
    request_id = getattr(req.state, "request_id", None) if req and hasattr(req, "state") else None
    review_req = body or RemediationApprovalRequest(decision="APPROVE")
    # Enforce decision is APPROVE for this route
    review_req.decision = "APPROVE"
    return remediation_service.review_remediation(
        remediation_id=remediation_id,
        review=review_req,
        user_id=current_user.user_id,
        request_id=request_id,
    )


@router.post(
    "/remediations/{remediation_id}/reject",
    response_model=RemediationResponse,
)
def reject_remediation(
    remediation_id: int,
    body: RemediationApprovalRequest | None = None,
    req: Request = None,
    current_user=Depends(require_permission("ACTION_APPROVE")),
    remediation_service: RemediationService = Depends(get_remediation_service),
):
    """
    Reject a pending remediation action.
    """
    request_id = getattr(req.state, "request_id", None) if req and hasattr(req, "state") else None
    review_req = body or RemediationApprovalRequest(decision="REJECT")
    review_req.decision = "REJECT"
    return remediation_service.review_remediation(
        remediation_id=remediation_id,
        review=review_req,
        user_id=current_user.user_id,
        request_id=request_id,
    )


@router.post(
    "/remediations/{remediation_id}/execute",
    response_model=RemediationResponse,
)
def execute_remediation(
    remediation_id: int,
    body: RemediationExecuteRequest | None = None,
    req: Request = None,
    current_user=Depends(require_permission("ACTION_APPROVE")),
    remediation_service: RemediationService = Depends(get_remediation_service),
):
    """
    Execute an approved remediation action using a safe registered adapter.
    Idempotent: Cannot be executed simultaneously or multiple times.
    """
    dry_run = body.dry_run if body is not None else True
    request_id = getattr(req.state, "request_id", None) if req and hasattr(req, "state") else None
    return remediation_service.execute_remediation(
        remediation_id=remediation_id,
        user_id=current_user.user_id,
        dry_run=dry_run,
        request_id=request_id,
    )


@router.post(
    "/remediations/{remediation_id}/verify",
    response_model=RemediationResponse,
)
def verify_remediation(
    remediation_id: int,
    force_fail: bool = Query(default=False),
    req: Request = None,
    current_user=Depends(require_permission("ACTION_REQUEST")),
    remediation_service: RemediationService = Depends(get_remediation_service),
):
    """
    Verify completed remediation via health probes and service metrics.
    Updates incident status upon verification.
    """
    request_id = getattr(req.state, "request_id", None) if req and hasattr(req, "state") else None
    return remediation_service.verify_remediation(
        remediation_id=remediation_id,
        user_id=current_user.user_id,
        force_fail=force_fail,
        request_id=request_id,
    )
