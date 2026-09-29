from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RemediationExecutionResult:
    success: bool
    action_type: str
    dry_run: bool
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "action_type": self.action_type,
            "dry_run": self.dry_run,
            "details": self.details,
            "error": self.error,
        }


class RemediationAdapter(ABC):
    @property
    @abstractmethod
    def action_type(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        *,
        payload: dict[str, Any],
        dry_run: bool = True,
    ) -> RemediationExecutionResult:
        raise NotImplementedError
