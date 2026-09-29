from __future__ import annotations

from app.ai.risk.base import RiskPredictor


def create_risk_predictor(
    predictor_type: str = "ml",
) -> RiskPredictor:
    """
    Factory for OpsPilot risk predictors.

    Types:
    - "ml"        : Trained Random Forest model (Phase C). Falls back to
                    heuristic if model artifact is not available.
    - "heuristic" : Rule-based baseline predictor (Phase A original).
    """
    if predictor_type == "ml":
        from app.ai.risk.ml_predictor import MLRiskPredictor
        return MLRiskPredictor()

    if predictor_type == "heuristic":
        from app.ai.risk.heuristic import HeuristicRiskPredictor
        return HeuristicRiskPredictor()

    raise ValueError(
        f"Unsupported risk predictor type: '{predictor_type}'. "
        "Valid options: 'ml', 'heuristic'."
    )
