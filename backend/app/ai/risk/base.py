from abc import ABC, abstractmethod
from typing import Any

from app.ai.risk.schemas import RiskPredictionResult


class RiskPredictor(ABC):

    @abstractmethod
    def predict(
        self,
        *,
        incident: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> RiskPredictionResult:
        raise NotImplementedError

    def predict_risk(
        self,
        *,
        incident: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> RiskPredictionResult:
        return self.predict(incident=incident, evidence=evidence)

