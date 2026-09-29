"""
ML-based Risk Predictor for OpsPilot.

Uses a pre-trained Random Forest (calibrated for probability output) to
predict incident risk score and level. Falls back to heuristic predictor
if the model artifact is unavailable.
"""
from __future__ import annotations

import json
import logging
import pickle
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

from app.ai.risk.base import RiskPredictor
from app.ai.risk.ml_features import FEATURE_NAMES, extract_ml_features, features_to_array
from app.ai.risk.schemas import RiskPredictionResult
from app.observability.metrics import RISK_PREDICTIONS_TOTAL
from app.observability.tracing import get_tracer

logger = logging.getLogger("opspilot.risk.ml")
tracer = get_tracer("opspilot.risk.ml")

MODEL_DIR = Path(__file__).parent / "model"
MODEL_PATH = MODEL_DIR / "risk_model.pkl"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

# Class labels matching the training script
CLASSES = ["LOW", "MEDIUM", "HIGH"]
CLASS_HIGH_IDX = 2
CLASS_MEDIUM_IDX = 1
CLASS_LOW_IDX = 0


class MLRiskPredictor(RiskPredictor):
    """
    Trained Random Forest + Calibration risk predictor.

    Predicts 3-class risk (LOW / MEDIUM / HIGH) and produces a continuous
    probability score. Automatically falls back to heuristic scoring if
    the model artifact is not present.
    """

    def __init__(self, model_path: Path | None = None) -> None:
        self._model_path = model_path or MODEL_PATH
        self._model = None
        self._metadata: dict[str, Any] = {}
        self._loaded = False
        self._load()

    def _load(self) -> None:
        if not self._model_path.exists():
            logger.warning(
                "ML risk model not found at %s — will use heuristic fallback.",
                self._model_path,
            )
            return

        try:
            with open(self._model_path, "rb") as f:
                self._model = pickle.load(f)  # nosec B301

            if METADATA_PATH.exists():
                with open(METADATA_PATH) as f:
                    self._metadata = json.load(f)

            self._loaded = True
            logger.info(
                "ML risk model loaded: %s v%s (%.1f%% CV accuracy)",
                self._metadata.get("model_name", "rf_v1"),
                self._metadata.get("model_version", "1.0.0"),
                self._metadata.get("cv_accuracy_mean", 0.0) * 100,
            )
        except Exception as exc:
            logger.error("Failed to load ML risk model: %s — using heuristic fallback.", exc)
            self._model = None
            self._loaded = False

    @property
    def model_name(self) -> str:
        return self._metadata.get("model_name", "incident_risk_rf_v1")

    @property
    def model_version(self) -> str:
        return self._metadata.get("model_version", "1.0.0")

    def predict(
        self,
        *,
        incident: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> RiskPredictionResult:
        with tracer.start_as_current_span("risk_prediction_ml") as span:
            if self._loaded and self._model is not None:
                result = self._predict_ml(incident=incident, evidence=evidence)
            else:
                result = self._predict_heuristic_fallback(incident=incident, evidence=evidence)

            span.set_attribute("opspilot.risk.level", result.risk_level)
            span.set_attribute("opspilot.risk.model", result.model_name)

            RISK_PREDICTIONS_TOTAL.labels(
                risk_level=result.risk_level,
                model_name=result.model_name,
            ).inc()

            return result

    def _predict_ml(
        self,
        *,
        incident: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> RiskPredictionResult:
        """Run the trained model to produce a risk prediction."""
        features = extract_ml_features(incident=incident, evidence=evidence)
        X = features_to_array(features)

        try:
            proba = self._model.predict_proba(X)[0]  # shape: (3,)
        except Exception as exc:
            logger.warning("ML model inference error: %s — using heuristic fallback.", exc)
            return self._predict_heuristic_fallback(incident=incident, evidence=evidence)

        # Composite risk score: weighted blend of class probabilities
        # Score = P(MEDIUM)×0.5 + P(HIGH)×1.0
        risk_score_float = float(proba[CLASS_MEDIUM_IDX] * 0.5 + proba[CLASS_HIGH_IDX] * 1.0)
        risk_score_float = max(0.0, min(1.0, risk_score_float))

        # Predicted class label
        predicted_class_idx = int(proba.argmax())
        risk_level = CLASSES[predicted_class_idx]

        # Overrides: if score is high but argmax says MEDIUM, bump to HIGH
        if risk_score_float >= 0.70 and risk_level != "HIGH":
            risk_level = "HIGH"
        elif risk_score_float < 0.35 and risk_level != "LOW":
            risk_level = "LOW"

        # Build explanation from top contributing features
        explanation = self._build_explanation(features, proba, risk_level)

        return RiskPredictionResult(
            risk_score=Decimal(str(round(risk_score_float, 4))),
            risk_level=risk_level,
            model_name=self.model_name,
            model_version=self.model_version,
            features={
                **features,
                "ml_proba_low": float(proba[CLASS_LOW_IDX]),
                "ml_proba_medium": float(proba[CLASS_MEDIUM_IDX]),
                "ml_proba_high": float(proba[CLASS_HIGH_IDX]),
            },
            explanation=explanation,
        )

    def _build_explanation(
        self,
        features: dict[str, float],
        proba: "np.ndarray",
        risk_level: str,
    ) -> str:
        reasons: list[str] = []

        if features["severity_score"] >= 0.75:
            reasons.append(f"Critical/high severity incident (score={features['severity_score']:.2f}).")
        if features["timeout_count"] >= 2:
            reasons.append(f"{int(features['timeout_count'])} timeout-related events detected.")
        elif features["timeout_count"] == 1:
            reasons.append("A timeout event was observed.")
        if features["max_error_rate"] >= 20:
            reasons.append(f"Error rate peaked at {features['max_error_rate']:.1f}%.")
        elif features["max_error_rate"] >= 10:
            reasons.append(f"Elevated error rate at {features['max_error_rate']:.1f}%.")
        if features["db_failure_count"] >= 1:
            reasons.append("Database failure events correlated with incident.")
        if features["has_recent_deployment"] > 0:
            reasons.append("A recent deployment was detected in the incident timeline.")
        if features["affected_service_count"] >= 2:
            reasons.append(f"{int(features['affected_service_count'])} services affected.")

        high_conf = float(proba[CLASS_HIGH_IDX])
        if not reasons:
            if risk_level == "LOW":
                return "No elevated risk indicators detected — incident risk is low."
            return f"ML model assessed {risk_level} risk (high confidence: {high_conf:.0%})."

        return " ".join(reasons)

    def _predict_heuristic_fallback(
        self,
        *,
        incident: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> RiskPredictionResult:
        """Fallback to heuristic when model is unavailable."""
        from app.ai.risk.heuristic import HeuristicRiskPredictor
        return HeuristicRiskPredictor().predict(incident=incident, evidence=evidence)
