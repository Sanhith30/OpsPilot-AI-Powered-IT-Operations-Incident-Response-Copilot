from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


class RiskPredictionResult(BaseModel):
    risk_score: Decimal = Field(
        ...,
        ge=0,
        le=1,
    )
    risk_level: RiskLevel
    model_name: str
    model_version: str
    features: dict
    explanation: str

    @property
    def failure_probability(self) -> float:
        return float(self.risk_score)

    @property
    def model_type(self) -> str:
        return "ML Random Forest" if ("rf" in self.model_name or "ml" in self.model_name.lower()) else self.model_name

