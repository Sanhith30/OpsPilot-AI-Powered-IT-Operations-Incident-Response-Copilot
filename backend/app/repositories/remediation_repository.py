from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.remediation_action import RemediationAction


class RemediationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, remediation_id: int) -> RemediationAction | None:
        return self.db.scalars(
            select(RemediationAction).where(
                RemediationAction.remediation_id == remediation_id
            )
        ).one_or_none()

    def get_by_incident(self, incident_id: int) -> list[RemediationAction]:
        return list(
            self.db.scalars(
                select(RemediationAction)
                .where(RemediationAction.incident_id == incident_id)
                .order_by(RemediationAction.created_at.desc())
            ).all()
        )

    def get_by_investigation(self, investigation_id: int) -> list[RemediationAction]:
        return list(
            self.db.scalars(
                select(RemediationAction)
                .where(RemediationAction.investigation_id == investigation_id)
                .order_by(RemediationAction.created_at.desc())
            ).all()
        )

    def add(self, action: RemediationAction) -> RemediationAction:
        self.db.add(action)
        self.db.flush()
        return action

    def claim_execution_lock(self, remediation_id: int) -> bool:
        """
        Atomic conditional claim to ensure execution is strictly idempotent.
        Only one concurrent request can transition APPROVED -> EXECUTING.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(RemediationAction)
            .where(
                RemediationAction.remediation_id == remediation_id,
                RemediationAction.status == "APPROVED",
            )
            .values(
                status="EXECUTING",
                execution_started_at=now,
                updated_at=now,
            )
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return result.rowcount == 1
