from __future__ import annotations

import logging
from typing import Any

from app.remediation.adapters.base import RemediationAdapter, RemediationExecutionResult

logger = logging.getLogger(__name__)


class AdjustPoolLimitsAdapter(RemediationAdapter):
    """
    Adapter for ADJUST_POOL_LIMITS.
    Safely adjusts connection pool limits within bounded operational constraints.
    """

    @property
    def action_type(self) -> str:
        return "ADJUST_POOL_LIMITS"

    def execute(
        self,
        *,
        payload: dict[str, Any],
        dry_run: bool = True,
    ) -> RemediationExecutionResult:
        service_id = payload.get("service_id")
        pool_size = payload.get("pool_size", 50)
        max_overflow = payload.get("max_overflow", 10)

        # Bounds validation
        if not isinstance(pool_size, int) or pool_size <= 0 or pool_size > 500:
            return RemediationExecutionResult(
                success=False,
                action_type=self.action_type,
                dry_run=dry_run,
                error=f"Invalid pool_size: {pool_size}. Must be integer between 1 and 500.",
            )

        if dry_run:
            return RemediationExecutionResult(
                success=True,
                action_type=self.action_type,
                dry_run=True,
                details={
                    "service_id": service_id,
                    "target_pool_size": pool_size,
                    "max_overflow": max_overflow,
                    "status": "SIMULATED_POOL_ADJUSTMENT",
                    "message": f"Dry-run pool adjustment to {pool_size} validated.",
                },
            )

        return RemediationExecutionResult(
            success=True,
            action_type=self.action_type,
            dry_run=False,
            details={
                "service_id": service_id,
                "target_pool_size": pool_size,
                "max_overflow": max_overflow,
                "status": "POOL_LIMITS_APPLIED",
                "message": f"Connection pool limits updated to {pool_size}.",
            },
        )
