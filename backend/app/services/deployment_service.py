from datetime import datetime

from app.repositories.deployment_repository import (
    DeploymentRepository,
)


class DeploymentService:
    def __init__(
        self,
        db,
        repository: DeploymentRepository,
    ):
        self.db = db
        self.repository = repository

    def get_recent_deployments(
        self,
        *,
        service_id: int,
        environment: str,
        before_time: datetime,
        limit: int = 5,
    ):
        return self.repository.get_recent_by_service(
            service_id=service_id,
            environment=environment,
            before_time=before_time,
            limit=limit,
        )