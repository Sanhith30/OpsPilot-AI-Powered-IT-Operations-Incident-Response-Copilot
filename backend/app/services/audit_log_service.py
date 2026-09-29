from ipaddress import IPv4Address, IPv6Address
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundError,
    ValidationError,
)
from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import (
    AuditLogRepository,
)
from app.repositories.user_repository import (
    UserRepository,
)


class AuditLogService:

    VALID_ACTOR_TYPES = {
        "USER",
        "AI",
        "SYSTEM",
    }

    VALID_ACTION_RESULTS = {
        "SUCCESS",
        "FAILURE",
        "DENIED",
    }

    def __init__(
        self,
        db: Session,
        repository: AuditLogRepository,
        user_repository: UserRepository,
    ):
        self.db = db
        self.repository = repository
        self.user_repository = user_repository

    def add_to_transaction(
        self,
        *,
        action: str,
        user_id: int | None,
        resource_type: str | None = None,
        resource_id: str | int | None = None,
        details: dict[str, Any] | None = None,
        actor_type: str = "USER",
        action_result: str = "SUCCESS",
        incident_id: int | None = None,
        investigation_id: int | None = None,
        ticket_id: int | None = None,
        request_id: str | None = None,
        ip_address: IPv4Address | IPv6Address | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:

        if actor_type not in self.VALID_ACTOR_TYPES:
            raise ValidationError(
                "Invalid actor type."
            )

        if action_result not in self.VALID_ACTION_RESULTS:
            raise ValidationError(
                "Invalid action result."
            )

        if user_id is not None:

            user = self.user_repository.get_by_id(
                user_id
            )

            if user is None:
                raise NotFoundError(
                    "Audit actor user not found."
                )

        audit_log = AuditLog(
            actor_user_id=user_id,
            actor_type=actor_type,
            action=action,
            resource_type=resource_type,
            resource_id=(
                str(resource_id)
                if resource_id is not None
                else None
            ),
            incident_id=incident_id,
            investigation_id=investigation_id,
            ticket_id=ticket_id,
            action_result=action_result,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )

        self.repository.add(audit_log)

        self.db.flush()

        return audit_log

    def get_by_resource(
        self,
        *,
        resource_type: str,
        resource_id: str | int,
    ) -> list[AuditLog]:
        return self.repository.get_by_resource(
            resource_type=resource_type,
            resource_id=str(resource_id),
        )