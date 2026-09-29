from __future__ import annotations

from app.remediation.adapters.base import RemediationAdapter, RemediationExecutionResult
from app.remediation.adapters.config import AdjustPoolLimitsAdapter
from app.remediation.adapters.restart import RestartServiceInstanceAdapter
from app.remediation.adapters.rollback import DeploymentRollbackAdapter
from app.remediation.adapters.runbook import RunbookStepExecutionAdapter

WHITELISTED_ACTION_TYPES = {
    "DEPLOYMENT_ROLLBACK",
    "RESTART_SERVICE_INSTANCE",
    "ADJUST_POOL_LIMITS",
    "RUNBOOK_STEP_EXECUTION",
}

DEFAULT_ADAPTER_REGISTRY: dict[str, RemediationAdapter] = {
    "DEPLOYMENT_ROLLBACK": DeploymentRollbackAdapter(),
    "RESTART_SERVICE_INSTANCE": RestartServiceInstanceAdapter(),
    "ADJUST_POOL_LIMITS": AdjustPoolLimitsAdapter(),
    "RUNBOOK_STEP_EXECUTION": RunbookStepExecutionAdapter(),
}

__all__ = [
    "RemediationAdapter",
    "RemediationExecutionResult",
    "DeploymentRollbackAdapter",
    "RestartServiceInstanceAdapter",
    "AdjustPoolLimitsAdapter",
    "RunbookStepExecutionAdapter",
    "WHITELISTED_ACTION_TYPES",
    "DEFAULT_ADAPTER_REGISTRY",
]
