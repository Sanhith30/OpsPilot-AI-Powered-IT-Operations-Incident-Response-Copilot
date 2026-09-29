"""
Phase C Tests — Trained ML Risk Model
Tests verify:
  1. Feature extraction produces correct numerical vector
  2. FEATURE_NAMES matches extract_ml_features output keys
  3. features_to_array produces correct numpy shape
  4. MLRiskPredictor loads model artifact successfully
  5. MLRiskPredictor predicts HIGH for critical + timeout + high error rate
  6. MLRiskPredictor predicts LOW for low severity + no evidence
  7. MLRiskPredictor predicts MEDIUM for moderate signals
  8. MLRiskPredictor falls back to heuristic if model missing
  9. Risk score is in [0, 1]
  10. Risk level matches risk score thresholds
  11. Factory returns MLRiskPredictor by default
  12. Factory returns HeuristicRiskPredictor when explicitly requested
  13. ML features: severity encoding correctness
  14. ML features: deployment detection
  15. ML features: multi-service count
  16. ML predictor: explanation is non-empty
  17. ML predictor: features dict includes probability values
  18. RiskPredictionResult schema validates correctly
  19. Backward compatibility: heuristic still passes existing tests
  20. Model metadata JSON is valid
"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ------------------------------------------------------------------ #
# Helper builders                                                      #
# ------------------------------------------------------------------ #

def make_incident(severity: str, status: str = "OPEN") -> dict[str, Any]:
    return {"severity": severity, "status": status}


def make_event(event_type: str, error_rate: float | None = None, service: str | None = None) -> dict[str, Any]:
    meta: dict[str, Any] = {"event_type": event_type}
    if error_rate is not None:
        meta["error_rate"] = error_rate
    if service:
        meta["service_name"] = service
    return {"source_type": "incident_event", "content": f"{event_type} observed", "metadata": meta}


def make_deployment() -> dict[str, Any]:
    return {"source_type": "deployment", "content": "Deployment detected", "metadata": {}}


# ------------------------------------------------------------------ #
# 1-3. Feature extraction                                              #
# ------------------------------------------------------------------ #

def test_extract_ml_features_keys():
    from app.ai.risk.ml_features import FEATURE_NAMES, extract_ml_features
    features = extract_ml_features(
        incident=make_incident("CRITICAL"),
        evidence=[make_event("TIMEOUT"), make_deployment()],
    )
    for name in FEATURE_NAMES:
        assert name in features, f"Feature '{name}' missing from extract_ml_features output"


def test_extract_ml_features_severity_encoding():
    from app.ai.risk.ml_features import extract_ml_features
    f_critical = extract_ml_features(incident=make_incident("CRITICAL"), evidence=[])
    f_low = extract_ml_features(incident=make_incident("LOW"), evidence=[])
    assert f_critical["severity_score"] > f_low["severity_score"]
    assert f_critical["severity_score"] == 1.0
    assert f_low["severity_score"] == 0.25


def test_extract_ml_features_deployment_flag():
    from app.ai.risk.ml_features import extract_ml_features
    f_with = extract_ml_features(incident=make_incident("HIGH"), evidence=[make_deployment()])
    f_without = extract_ml_features(incident=make_incident("HIGH"), evidence=[])
    assert f_with["has_recent_deployment"] == 1.0
    assert f_without["has_recent_deployment"] == 0.0


def test_extract_ml_features_multi_service_count():
    from app.ai.risk.ml_features import extract_ml_features
    evidence = [
        make_event("TIMEOUT", service="payment-api"),
        make_event("ERROR", service="auth-service"),
        make_event("DB_FAILURE", service="order-service"),
    ]
    features = extract_ml_features(incident=make_incident("CRITICAL"), evidence=evidence)
    assert features["affected_service_count"] == 3.0


def test_extract_ml_features_error_rate_stats():
    from app.ai.risk.ml_features import extract_ml_features
    evidence = [
        make_event("TIMEOUT", error_rate=15.0),
        make_event("ERROR", error_rate=35.0),
    ]
    features = extract_ml_features(incident=make_incident("HIGH"), evidence=evidence)
    assert features["max_error_rate"] == 35.0
    assert abs(features["avg_error_rate"] - 25.0) < 0.01


def test_features_to_array_shape():
    from app.ai.risk.ml_features import FEATURE_NAMES, extract_ml_features, features_to_array
    features = extract_ml_features(incident=make_incident("HIGH"), evidence=[])
    arr = features_to_array(features)
    assert arr.shape == (1, len(FEATURE_NAMES))
    assert arr.dtype.name == "float32"


# ------------------------------------------------------------------ #
# 4-10. MLRiskPredictor behavior                                       #
# ------------------------------------------------------------------ #

def test_ml_predictor_loads_model():
    from app.ai.risk.ml_predictor import MODEL_PATH, MLRiskPredictor
    predictor = MLRiskPredictor()
    if MODEL_PATH.exists():
        assert predictor._loaded is True
    else:
        assert predictor._loaded is False  # graceful fallback


def test_ml_predictor_predicts_high_risk():
    """Critical incident + multiple timeouts + high error rate = HIGH."""
    from app.ai.risk.ml_predictor import MLRiskPredictor
    predictor = MLRiskPredictor()

    evidence = [
        make_event("TIMEOUT", error_rate=35.0, service="payment-api"),
        make_event("TIMEOUT", error_rate=30.0),
        make_event("DB_FAILURE"),
        make_deployment(),
    ]
    result = predictor.predict(incident=make_incident("CRITICAL"), evidence=evidence)

    assert result.risk_level == "HIGH"
    assert result.risk_score >= Decimal("0.70")
    assert 0.0 <= float(result.risk_score) <= 1.0


def test_ml_predictor_predicts_low_risk():
    """Low severity + no evidence = LOW."""
    from app.ai.risk.ml_predictor import MLRiskPredictor
    predictor = MLRiskPredictor()

    result = predictor.predict(incident=make_incident("LOW"), evidence=[])

    assert result.risk_level == "LOW"
    assert float(result.risk_score) < 0.50


def test_ml_predictor_predicts_medium_risk():
    """High incident + single timeout + moderate error rate = MEDIUM."""
    from app.ai.risk.ml_predictor import MLRiskPredictor
    predictor = MLRiskPredictor()

    evidence = [
        make_event("TIMEOUT", error_rate=12.0),
        make_event("ALERT"),
    ]
    result = predictor.predict(incident=make_incident("HIGH"), evidence=evidence)

    # MEDIUM or HIGH — not LOW
    assert result.risk_level in ("MEDIUM", "HIGH")
    assert float(result.risk_score) >= 0.35


def test_ml_predictor_risk_score_in_range():
    """Risk score must always be in [0, 1]."""
    from app.ai.risk.ml_predictor import MLRiskPredictor
    predictor = MLRiskPredictor()

    for severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        for evidence in [[], [make_event("TIMEOUT")], [make_event("TIMEOUT"), make_deployment()]]:
            result = predictor.predict(incident=make_incident(severity), evidence=evidence)
            assert Decimal("0.00") <= result.risk_score <= Decimal("1.00"), \
                f"Risk score out of range for {severity}: {result.risk_score}"


def test_ml_predictor_explanation_non_empty():
    from app.ai.risk.ml_predictor import MLRiskPredictor
    predictor = MLRiskPredictor()
    result = predictor.predict(
        incident=make_incident("CRITICAL"),
        evidence=[make_event("TIMEOUT", error_rate=25.0), make_deployment()],
    )
    assert isinstance(result.explanation, str)
    assert len(result.explanation) > 10


def test_ml_predictor_features_include_proba():
    """Features dict must include ML probability values when loaded."""
    from app.ai.risk.ml_predictor import MLRiskPredictor
    predictor = MLRiskPredictor()
    if not predictor._loaded:
        pytest.skip("ML model not loaded — skipping probability keys test")

    result = predictor.predict(
        incident=make_incident("HIGH"),
        evidence=[make_event("TIMEOUT")],
    )
    assert "ml_proba_low" in result.features
    assert "ml_proba_medium" in result.features
    assert "ml_proba_high" in result.features
    assert abs(
        result.features["ml_proba_low"]
        + result.features["ml_proba_medium"]
        + result.features["ml_proba_high"] - 1.0
    ) < 0.01


def test_ml_predictor_heuristic_fallback(tmp_path):
    """When model file doesn't exist, MLRiskPredictor falls back to heuristic."""
    from app.ai.risk.ml_predictor import MLRiskPredictor

    missing_path = tmp_path / "nonexistent_model.pkl"
    predictor = MLRiskPredictor(model_path=missing_path)

    assert predictor._loaded is False

    # Should still produce a result via heuristic fallback
    result = predictor.predict(
        incident=make_incident("CRITICAL"),
        evidence=[make_event("TIMEOUT", error_rate=25.0)],
    )
    assert result.risk_level in ("LOW", "MEDIUM", "HIGH")
    assert Decimal("0.00") <= result.risk_score <= Decimal("1.00")


# ------------------------------------------------------------------ #
# 11-12. Factory                                                        #
# ------------------------------------------------------------------ #

def test_factory_default_returns_ml():
    from app.ai.risk.factory import create_risk_predictor
    from app.ai.risk.ml_predictor import MLRiskPredictor
    predictor = create_risk_predictor()
    assert isinstance(predictor, MLRiskPredictor)


def test_factory_heuristic_explicit():
    from app.ai.risk.factory import create_risk_predictor
    from app.ai.risk.heuristic import HeuristicRiskPredictor
    predictor = create_risk_predictor("heuristic")
    assert isinstance(predictor, HeuristicRiskPredictor)


def test_factory_invalid_raises():
    from app.ai.risk.factory import create_risk_predictor
    with pytest.raises(ValueError, match="Unsupported risk predictor"):
        create_risk_predictor("bogus")


# ------------------------------------------------------------------ #
# 13. Model metadata validity                                          #
# ------------------------------------------------------------------ #

def test_model_metadata_valid():
    from app.ai.risk.ml_predictor import METADATA_PATH
    if not METADATA_PATH.exists():
        pytest.skip("Model not trained yet — metadata not available")

    with open(METADATA_PATH) as f:
        meta = json.load(f)

    assert "model_name" in meta
    assert "model_version" in meta
    assert "feature_names" in meta
    assert "classes" in meta
    assert meta["classes"] == ["LOW", "MEDIUM", "HIGH"]
    assert "cv_accuracy_mean" in meta
    assert meta["cv_accuracy_mean"] >= 0.80, "CV accuracy should be at least 80%"
    assert len(meta["feature_names"]) == 14


# ------------------------------------------------------------------ #
# 14. Backward compatibility: heuristic produces valid result          #
# ------------------------------------------------------------------ #

def test_heuristic_still_works():
    from app.ai.risk.heuristic import HeuristicRiskPredictor
    predictor = HeuristicRiskPredictor()
    result = predictor.predict(
        incident=make_incident("CRITICAL"),
        evidence=[
            make_event("TIMEOUT", error_rate=25.0),
            make_deployment(),
        ],
    )
    assert result.risk_level == "HIGH"
    assert Decimal("0.00") <= result.risk_score <= Decimal("1.00")
    assert result.model_name == "incident_risk_baseline"


def test_heuristic_low_severity():
    from app.ai.risk.heuristic import HeuristicRiskPredictor
    predictor = HeuristicRiskPredictor()
    result = predictor.predict(incident=make_incident("LOW"), evidence=[])
    assert result.risk_level == "LOW"


# ------------------------------------------------------------------ #
# 15. RiskPredictionResult schema                                      #
# ------------------------------------------------------------------ #

def test_risk_prediction_result_schema():
    from app.ai.risk.schemas import RiskPredictionResult
    r = RiskPredictionResult(
        risk_score=Decimal("0.82"),
        risk_level="HIGH",
        model_name="test_model",
        model_version="1.0.0",
        features={"severity_score": 1.0},
        explanation="Critical severity with timeout events.",
    )
    assert r.risk_level == "HIGH"
    assert r.risk_score == Decimal("0.82")


def test_risk_prediction_result_invalid_level():
    from app.ai.risk.schemas import RiskPredictionResult
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        RiskPredictionResult(
            risk_score=Decimal("0.5"),
            risk_level="EXTREME",  # invalid
            model_name="test",
            model_version="1.0.0",
            features={},
            explanation="",
        )


# ------------------------------------------------------------------ #
# 16. Integration: dependencies.py still works with ML predictor      #
# ------------------------------------------------------------------ #

def test_dependency_get_risk_predictor():
    from app.api.dependencies import get_risk_predictor
    from app.ai.risk.ml_predictor import MLRiskPredictor
    predictor = get_risk_predictor()
    assert isinstance(predictor, MLRiskPredictor)
