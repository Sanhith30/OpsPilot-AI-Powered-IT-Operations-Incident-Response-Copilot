from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

RemediationStatus = Literal[
    "PENDING_APPROVAL",
    "APPROVED",
    "REJECTED",
    "REQUEST_MORE_INFO",
    "EXECUTING",
    "COMPLETED",
    "FAILED",
    "VERIFIED",
    "VERIFICATION_FAILED",
]

RemediationActionType = Literal[
    "DEPLOYMENT_ROLLBACK",
    "RESTART_SERVICE_INSTANCE",
    "ADJUST_POOL_LIMITS",
    "RUNBOOK_STEP_EXECUTION",
]


class RemediationCreateRequest(BaseModel):
    action_id: str = Field(description="Action identifier from intelligence recommendation, e.g. ACT-001")
    action_type: RemediationActionType = Field(description="Whitelisted remediation action type")
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    investigation_id: int | None = None
    intelligence_id: int | None = None
    execution_payload: dict[str, Any] = Field(default_factory=dict)


class RemediationApprovalRequest(BaseModel):
    decision: Literal["APPROVE", "REJECT", "REQUEST_MORE_INFO"]
    review_comment: str | None = None


class RemediationExecuteRequest(BaseModel):
    dry_run: bool = Field(default=True, description="Execute in safe dry-run mode by default")


class RemediationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    remediation_id: int
    incident_id: int
    investigation_id: int | None = None
    intelligence_id: int | None = None
    action_id: str
    action_type: str
    title: str
    description: str
    rationale: str
    status: str
    execution_payload: dict[str, Any] = Field(default_factory=dict)
    requested_by_user_id: int
    approved_by_user_id: int | None = None
    approved_at: datetime | None = None
    review_comment: str | None = None
    execution_result: dict[str, Any] = Field(default_factory=dict)
    execution_started_at: datetime | None = None
    execution_completed_at: datetime | None = None
    verification_status: str
    verification_result: dict[str, Any] = Field(default_factory=dict)
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
