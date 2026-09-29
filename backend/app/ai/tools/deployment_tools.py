from typing import Any

from app.ai.schemas.deployment_tool import (
    GetRecentDeploymentsInput,
)
from app.ai.tools.base import BaseTool
from app.services.deployment_service import DeploymentService


class GetRecentDeploymentsTool(BaseTool):
    """
    Retrieve recent deployments for a service before a
    specified investigation timestamp.
    """

    name = "get_recent_deployments"

    description = (
        "Retrieve the most recent deployments for a service "
        "before a specified timestamp."
    )

    args_schema = GetRecentDeploymentsInput

    def __init__(
        self,
        deployment_service: DeploymentService,
    ):
        self.deployment_service = deployment_service

    def execute(
        self,
        validated_input: GetRecentDeploymentsInput,
    ) -> dict[str, Any]:

        deployments = (
            self.deployment_service.get_recent_deployments(
                service_id=validated_input.service_id,
                environment=validated_input.environment,
                before_time=validated_input.before_time,
                limit=validated_input.limit,
            )
        )

        return {
            "service_id": validated_input.service_id,
            "environment": validated_input.environment,
            "before_time": (
                validated_input.before_time.isoformat()
            ),
            "deployments": [
                {
                    "deployment_id": deployment.deployment_id,
                    "service_id": deployment.service_id,
                    "version": deployment.version,
                    "environment": deployment.environment,
                    "commit_hash": deployment.commit_hash,
                    "deployment_type": deployment.deployment_type,
                    "trigger_type": deployment.trigger_type,
                    "status": deployment.status,
                    "started_at": (
                        deployment.started_at.isoformat()
                    ),
                    "completed_at": (
                        deployment.completed_at.isoformat()
                        if deployment.completed_at
                        else None
                    ),
                    "deployed_by": deployment.deployed_by,
                }
                for deployment in deployments
            ],
        }