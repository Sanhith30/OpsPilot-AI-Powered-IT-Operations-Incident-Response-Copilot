from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:

    def __init__(self, db: Session):
        self.db = db

    def add(
        self,
        audit_log: AuditLog,
    ) -> AuditLog:

        self.db.add(audit_log)

        return audit_log

    def get_by_id(
        self,
        audit_id: int,
    ) -> AuditLog | None:

        statement = (
            select(AuditLog)
            .where(
                AuditLog.audit_id == audit_id
            )
        )

        return self.db.scalars(
            statement
        ).one_or_none()

    def get_by_actor(
        self,
        actor_user_id: int,
    ) -> list[AuditLog]:

        statement = (
            select(AuditLog)
            .where(
                AuditLog.actor_user_id
                == actor_user_id
            )
            .order_by(
                AuditLog.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_by_action(
        self,
        action: str,
    ) -> list[AuditLog]:

        statement = (
            select(AuditLog)
            .where(
                AuditLog.action == action
            )
            .order_by(
                AuditLog.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> list[AuditLog]:

        statement = (
            select(AuditLog)
            .where(
                AuditLog.resource_type
                == resource_type,
                AuditLog.resource_id
                == resource_id,
            )
            .order_by(
                AuditLog.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_recent(
        self,
        limit: int = 50,
        resource_type: str | None = None,
    ) -> list[AuditLog]:
        statement = select(AuditLog)
        if resource_type:
            statement = statement.where(AuditLog.resource_type == resource_type)
        statement = statement.order_by(AuditLog.created_at.desc()).limit(limit)
        return list(self.db.scalars(statement).all())