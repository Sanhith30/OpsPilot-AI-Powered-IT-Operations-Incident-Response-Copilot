from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.deployment import Deployment


class DeploymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        deployment_id: int,
    ) -> Deployment | None:
        statement = select(Deployment).where(
            Deployment.deployment_id == deployment_id
        )

        return self.db.execute(statement).scalar_one_or_none()

    def get_recent_by_service(
        self,
        *,
        service_id: int,
        environment: str,
        before_time: datetime,
        limit: int = 5,
    ) -> list[Deployment]:
        statement = (
            select(Deployment)
            .where(
                Deployment.service_id == service_id,
                Deployment.environment == environment,
                Deployment.started_at <= before_time,
            )
            .order_by(
                Deployment.started_at.desc()
            )
            .limit(limit)
        )

        return list(
            self.db.execute(statement).scalars().all()
        )