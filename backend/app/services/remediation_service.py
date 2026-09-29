from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.incident_event import IncidentEvent
from app.models.remediation_action import RemediationAction
from app.observability.metrics import (
    REMEDIATION_APPROVALS_TOTAL,
    REMEDIATION_DURATION_SECONDS,
    REMEDIATION_EXECUTIONS_TOTAL,
    REMEDIATIONS_TOTAL,
)
from app.observability.tracing import get_tracer
from app.remediation.engine import RemediationExecutionEngine
from app.remediation.verifier import RemediationVerifier
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.remediation_repository import RemediationRepository
from app.schemas.remediation import (
    RemediationApprovalRequest,
    RemediationCreateRequest,
    RemediationResponse,
)
from app.services.audit_log_service import AuditLogService

tracer = get_tracer("opspilot.remediation")


class RemediationService:
    def __init__(
        self,
        db: Session,
        repository: RemediationRepository,
        incident_repository: IncidentRepository,
        investigation_repository: InvestigationRepository,
        audit_log_service: AuditLogService,
        execution_engine: RemediationExecutionEngine | None = None,
        verifier: RemediationVerifier | None = None,
    ) -> None:
        self.db = db
        self.repository = repository
        self.incident_repository = incident_repository
        self.investigation_repository = investigation_repository
        self.audit_log_service = audit_log_service
        self.execution_engine = execution_engine or RemediationExecutionEngine()
        self.verifier = verifier or RemediationVerifier()

    def get_by_id(self, remediation_id: int) -> RemediationAction:
        action = self.repository.get_by_id(remediation_id)
        if action is None:
            raise NotFoundError(f"Remediation action {remediation_id} not found.")
        return action

    def get_by_incident(self, incident_id: int) -> list[RemediationAction]:
        if self.incident_repository.get_by_id(incident_id) is None:
            raise NotFoundError("Incident not found.")
        return self.repository.get_by_incident(incident_id)

    def create_remediation(
        self,
        *,
        incident_id: int,
        request: RemediationCreateRequest,
        user_id: int,
        request_id: str | None = None,
    ) -> RemediationAction:
        incident = self.incident_repository.get_by_id(incident_id)
        if incident is None:
            raise NotFoundError("Incident not found.")

        if request.investigation_id is not None:
            inv = self.investigation_repository.get_by_id(request.investigation_id)
            if inv is None:
                raise NotFoundError(f"Investigation {request.investigation_id} not found.")

        action = RemediationAction(
            incident_id=incident_id,
            investigation_id=request.investigation_id,
            intelligence_id=request.intelligence_id,
            action_id=request.action_id,
            action_type=request.action_type,
            title=request.title,
            description=request.description,
            rationale=request.rationale,
            status="PENDING_APPROVAL",
            execution_payload=request.execution_payload,
            requested_by_user_id=user_id,
        )

        self.repository.add(action)

        # Audit log
        self.audit_log_service.add_to_transaction(
            action="REMEDIATION_REQUESTED",
            user_id=user_id,
            resource_type="REMEDIATION_ACTION",
            resource_id=str(action.remediation_id),
            action_result="SUCCESS",
            incident_id=incident_id,
            investigation_id=request.investigation_id,
            request_id=request_id,
            details={
                "action_id": action.action_id,
                "action_type": action.action_type,
                "title": action.title,
            },
        )
        self.db.commit()

        REMEDIATIONS_TOTAL.labels(
            action_type=action.action_type,
            status="PENDING_APPROVAL",
        ).inc()

        return action

    def review_remediation(
        self,
        *,
        remediation_id: int,
        review: RemediationApprovalRequest,
        user_id: int,
        request_id: str | None = None,
    ) -> RemediationAction:
        with tracer.start_as_current_span("remediation.approval") as span:
            span.set_attribute("remediation_id", remediation_id)
            span.set_attribute("decision", review.decision)

            action = self.get_by_id(remediation_id)

            # Strict state transition: Can only review from PENDING_APPROVAL or REQUEST_MORE_INFO
            if action.status not in ("PENDING_APPROVAL", "REQUEST_MORE_INFO"):
                raise ValidationError(
                    f"Invalid state transition: Cannot review remediation in status '{action.status}'. "
                    "Must be in PENDING_APPROVAL or REQUEST_MORE_INFO."
                )

            now = datetime.now(timezone.utc)
            action.review_comment = review.review_comment

            if review.decision == "APPROVE":
                action.status = "APPROVED"
                action.approved_by_user_id = user_id
                action.approved_at = now
                audit_action = "REMEDIATION_APPROVED"
            elif review.decision == "REJECT":
                action.status = "REJECTED"
                audit_action = "REMEDIATION_REJECTED"
            elif review.decision == "REQUEST_MORE_INFO":
                action.status = "REQUEST_MORE_INFO"
                audit_action = "REMEDIATION_INFO_REQUESTED"
            else:
                raise ValidationError(f"Unknown review decision: {review.decision}")

            self.audit_log_service.add_to_transaction(
                action=audit_action,
                user_id=user_id,
                resource_type="REMEDIATION_ACTION",
                resource_id=str(action.remediation_id),
                action_result="SUCCESS",
                incident_id=action.incident_id,
                investigation_id=action.investigation_id,
                request_id=request_id,
                details={
                    "decision": review.decision,
                    "review_comment": review.review_comment,
                },
            )
            self.db.commit()

            REMEDIATION_APPROVALS_TOTAL.labels(decision=review.decision).inc()
            return action

    def execute_remediation(
        self,
        *,
        remediation_id: int,
        user_id: int,
        dry_run: bool = True,
        request_id: str | None = None,
    ) -> RemediationAction:
        start_time = time.perf_counter()

        with tracer.start_as_current_span("remediation.execution") as span:
            span.set_attribute("remediation_id", remediation_id)
            span.set_attribute("dry_run", dry_run)

            action = self.get_by_id(remediation_id)

            # Idempotency check: Claim the transition from APPROVED -> EXECUTING atomically
            claimed = self.repository.claim_execution_lock(remediation_id)
            if not claimed:
                # Refresh status to report precise conflict reason
                current_action = self.get_by_id(remediation_id)
                if current_action.status == "EXECUTING":
                    raise ConflictError(
                        f"Remediation {remediation_id} is already currently executing."
                    )
                if current_action.status in ("COMPLETED", "VERIFIED", "FAILED", "VERIFICATION_FAILED"):
                    raise ConflictError(
                        f"Remediation {remediation_id} has already been executed (status: '{current_action.status}')."
                    )
                raise ValidationError(
                    f"Invalid state transition: Remediation must be in APPROVED status to execute, but is currently '{current_action.status}'."
                )

            # We successfully claimed the lock; action.status is now EXECUTING in DB
            self.db.refresh(action)

            # Execute via safe adapter registry
            exec_result = self.execution_engine.execute(
                action_type=action.action_type,
                payload=action.execution_payload,
                dry_run=dry_run,
            )

            now = datetime.now(timezone.utc)
            action.execution_completed_at = now
            action.execution_result = exec_result.to_dict()

            if exec_result.success:
                action.status = "COMPLETED"
                audit_action = "REMEDIATION_EXECUTED"
                action_result = "SUCCESS"
            else:
                action.status = "FAILED"
                audit_action = "REMEDIATION_EXECUTION_FAILED"
                action_result = "FAILURE"

            self.audit_log_service.add_to_transaction(
                action=audit_action,
                user_id=user_id,
                resource_type="REMEDIATION_ACTION",
                resource_id=str(action.remediation_id),
                action_result=action_result,
                incident_id=action.incident_id,
                investigation_id=action.investigation_id,
                request_id=request_id,
                details={
                    "dry_run": dry_run,
                    "action_type": action.action_type,
                    "result": exec_result.to_dict(),
                },
            )
            self.db.commit()

            duration = time.perf_counter() - start_time
            REMEDIATION_DURATION_SECONDS.labels(
                action_type=action.action_type,
                status=action.status,
            ).observe(duration)
            REMEDIATION_EXECUTIONS_TOTAL.labels(
                action_type=action.action_type,
                result=action_result,
            ).inc()

            return action

    def verify_remediation(
        self,
        *,
        remediation_id: int,
        user_id: int,
        force_fail: bool = False,
        request_id: str | None = None,
    ) -> RemediationAction:
        with tracer.start_as_current_span("remediation.verification") as span:
            span.set_attribute("remediation_id", remediation_id)

            action = self.get_by_id(remediation_id)

            # Strict state transition: Can only verify COMPLETED actions
            if action.status not in ("COMPLETED", "VERIFIED"):
                raise ValidationError(
                    f"Invalid state transition: Cannot verify remediation in status '{action.status}'. "
                    "Remediation must be in COMPLETED status."
                )

            verif_result = self.verifier.verify(
                action_type=action.action_type,
                execution_payload=action.execution_payload,
                execution_result=action.execution_result,
                force_fail=force_fail,
            )

            now = datetime.now(timezone.utc)
            action.verified_at = now
            action.verification_result = verif_result.to_dict()

            if verif_result.verified:
                action.status = "VERIFIED"
                action.verification_status = "VERIFIED"

                # Update incident status to MITIGATED
                incident = self.incident_repository.get_by_id(action.incident_id)
                if incident:
                    incident.status = "MITIGATED"

                # Record IncidentEvent
                evt = IncidentEvent(
                    incident_id=action.incident_id,
                    event_type="MITIGATION_APPLIED",
                    description=f"Remediation action '{action.action_type}' ({action.title}) successfully verified.",
                    event_time=now,
                    created_by=user_id,
                    event_metadata={
                        "remediation_id": action.remediation_id,
                        "action_type": action.action_type,
                        "verification": verif_result.to_dict(),
                    },
                )
                self.db.add(evt)
                audit_action = "REMEDIATION_VERIFIED"
                audit_result = "SUCCESS"
            else:
                action.status = "VERIFICATION_FAILED"
                action.verification_status = "FAILED"
                audit_action = "REMEDIATION_VERIFICATION_FAILED"
                audit_result = "FAILURE"

            self.audit_log_service.add_to_transaction(
                action=audit_action,
                user_id=user_id,
                resource_type="REMEDIATION_ACTION",
                resource_id=str(action.remediation_id),
                action_result=audit_result,
                incident_id=action.incident_id,
                investigation_id=action.investigation_id,
                request_id=request_id,
                details=verif_result.to_dict(),
            )
            self.db.commit()

            return action
