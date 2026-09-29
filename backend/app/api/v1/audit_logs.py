from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_audit_log_repository,
    require_permission,
)
from app.repositories.audit_log_repository import AuditLogRepository

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("")
def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    resource_type: str | None = Query(default=None),
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
) -> list[dict[str, Any]]:
    """
    Returns immutable audit logs ordered chronologically descending.
    Accessible to users with INCIDENT_VIEW or AUDIT_VIEW permission.
    """
    logs = audit_repo.get_recent(limit=limit, resource_type=resource_type)
    return [
        {
            "audit_id": log.audit_id,
            "action": log.action,
            "actor_user_id": log.actor_user_id,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "action_result": log.action_result,
            "incident_id": log.incident_id,
            "investigation_id": log.investigation_id,
            "request_id": log.request_id,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
