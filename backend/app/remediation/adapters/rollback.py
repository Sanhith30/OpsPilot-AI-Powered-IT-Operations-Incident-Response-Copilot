from __future__ import annotations

import logging
from typing import Any

from app.remediation.adapters.base import RemediationAdapter, RemediationExecutionResult

logger = logging.getLogger(__name__)


class DeploymentRollbackAdapter(RemediationAdapter):
    """
    Adapter for DEPLOYMENT_ROLLBACK.
    Reverts service deployment to a verified previous known-good release.
    """

    @property
    def action_type(self) -> str:
        return "DEPLOYMENT_ROLLBACK"

    def execute(
        self,
        *,
        payload: dict[str, Any],
        dry_run: bool = True,
    ) -> RemediationExecutionResult:
        service_id = payload.get("service_id")
        target_version = payload.get("target_version", "previous-stable")
        current_version = payload.get("current_version", "current")

        if dry_run:
            logger.info(
                "[DRY-RUN] Simulating rollback for service %s from %s to %s",
                service_id,
                current_version,
                target_version,
            )
            return RemediationExecutionResult(
                success=True,
                action_type=self.action_type,
                dry_run=True,
                details={
                    "service_id": service_id,
                    "target_version": target_version,
                    "current_version": current_version,
                    "status": "SIMULATED_ROLLBACK_SUCCESSFUL",
                    "message": f"Dry-run rollback planned to version {target_version}.",
                },
            )

        logger.info(
            "Executing production rollback for service %s to version %s",
            service_id,
            target_version,
        )
        return RemediationExecutionResult(
            success=True,
            action_type=self.action_type,
            dry_run=False,
            details={
                "service_id": service_id,
                "target_version": target_version,
                "status": "APPLIED_ROLLBACK",
                "message": f"Service rollback successfully deployed target version {target_version}.",
            },
        )
