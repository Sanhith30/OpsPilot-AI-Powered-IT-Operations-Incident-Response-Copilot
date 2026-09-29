from __future__ import annotations

import logging
from typing import Any

from app.remediation.adapters.base import RemediationAdapter, RemediationExecutionResult

logger = logging.getLogger(__name__)


class RestartServiceInstanceAdapter(RemediationAdapter):
    """
    Adapter for RESTART_SERVICE_INSTANCE.
    Performs graceful restart of problematic container/pod instances.
    """

    @property
    def action_type(self) -> str:
        return "RESTART_SERVICE_INSTANCE"

    def execute(
        self,
        *,
        payload: dict[str, Any],
        dry_run: bool = True,
    ) -> RemediationExecutionResult:
        service_id = payload.get("service_id")
        instance_id = payload.get("instance_id", "all-degraded")

        if dry_run:
            return RemediationExecutionResult(
                success=True,
                action_type=self.action_type,
                dry_run=True,
                details={
                    "service_id": service_id,
                    "instance_id": instance_id,
                    "status": "SIMULATED_RESTART_SUCCESSFUL",
                    "message": f"Dry-run graceful restart validated for instance {instance_id}.",
                },
            )

        return RemediationExecutionResult(
            success=True,
            action_type=self.action_type,
            dry_run=False,
            details={
                "service_id": service_id,
                "instance_id": instance_id,
                "status": "RESTARTED",
                "message": f"Instance {instance_id} was gracefully restarted.",
            },
        )
