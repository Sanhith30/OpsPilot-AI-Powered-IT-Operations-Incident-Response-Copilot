from __future__ import annotations

import logging
from typing import Any

from app.core.exceptions import ValidationError
from app.remediation.adapters import (
    DEFAULT_ADAPTER_REGISTRY,
    WHITELISTED_ACTION_TYPES,
    RemediationAdapter,
    RemediationExecutionResult,
)

logger = logging.getLogger(__name__)


class RemediationExecutionEngine:
    """
    Executes permitted remediation actions using safe registered adapters.
    Strictly forbids non-whitelisted or arbitrary shell commands.
    """

    def __init__(
        self,
        adapters: dict[str, RemediationAdapter] | None = None,
    ) -> None:
        self.adapters = adapters or DEFAULT_ADAPTER_REGISTRY

    def execute(
        self,
        *,
        action_type: str,
        payload: dict[str, Any],
        dry_run: bool = True,
    ) -> RemediationExecutionResult:
        if action_type not in WHITELISTED_ACTION_TYPES:
            raise ValidationError(
                f"Action type '{action_type}' is not permitted. "
                f"Only whitelisted actions are allowed: {sorted(list(WHITELISTED_ACTION_TYPES))}."
            )

        adapter = self.adapters.get(action_type)
        if adapter is None:
            raise ValidationError(
                f"No registered remediation adapter for action type: {action_type}"
            )

        logger.info(
            "Executing remediation action '%s' (dry_run=%s)",
            action_type,
            dry_run,
        )
        return adapter.execute(payload=payload, dry_run=dry_run)
