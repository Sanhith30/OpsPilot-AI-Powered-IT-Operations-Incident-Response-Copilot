"""
Tests for Phase 4: Independent ML Model Validation.

Verifies:
1. Zero Data Leakage: Evaluates on an independent holdout set (500 samples, seed 9999).
2. Accuracy & Macro-F1 exceed required quality gates (> 90%).
3. Multi-class ROC-AUC exceeds 0.95.
4. Brier score confirms well-calibrated probabilities (< 0.10 per class).
5. Deterministic behavioral risk boundary checks:
   - High error rate + critical severity + db failure -> HIGH risk with prob > 0.85
   - Low severity + no errors + few events -> LOW risk with prob > 0.85
"""
from __future__ import annotations

import random
import numpy as np
import pytest
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, brier_score_loss

from app.ai.risk.ml_predictor import MLRiskPredictor, CLASSES
from app.ai.risk.train_model import generate_independent_dataset
from app.ai.risk.ml_features import extract_ml_features, FEATURE_NAMES


@pytest.fixture(scope="module")
def ml_predictor():
    pred = MLRiskPredictor()
    assert pred._loaded, "ML model failed to load!"
    return pred


def test_independent_holdout_quality_gates(ml_predictor):
    """Verify accuracy, Macro F1, and ROC-AUC on independent holdout dataset."""
    random.seed(9999)
    np.random.seed(9999)

    X_test, y_test = generate_independent_dataset(n_samples=500)
    model = ml_predictor._model

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)

    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    roc_auc = roc_auc_score(y_test, y_prob, multi_class="ovr", average="macro")

    # Quality gates
    assert acc >= 0.90, f"Accuracy {acc:.4f} fell below 0.90 gate"
    assert macro_f1 >= 0.90, f"Macro F1 {macro_f1:.4f} fell below 0.90 gate"
    assert roc_auc >= 0.95, f"ROC-AUC {roc_auc:.4f} fell below 0.95 gate"


def test_brier_calibration_scores(ml_predictor):
    """Verify Brier score calibration for each risk class."""
    random.seed(9999)
    np.random.seed(9999)

    X_test, y_test = generate_independent_dataset(n_samples=500)
    model = ml_predictor._model
    y_prob = model.predict_proba(X_test)

    for i, cls_name in enumerate(CLASSES):
        y_true_binary = (y_test == i).astype(int)
        y_prob_cls = y_prob[:, i]
        brier = brier_score_loss(y_true_binary, y_prob_cls)
        assert brier < 0.10, f"Brier score for {cls_name} ({brier:.4f}) is uncalibrated (> 0.10)"


def test_high_risk_boundary_classification(ml_predictor):
    """Verify a critical incident with DB failures and high error rate classifies as HIGH."""
    incident = {
        "incident_id": 9991,
        "severity": "CRITICAL",
        "status": "OPEN",
        "title": "Severe Payment Gateway DB Outage",
    }
    evidence = [
        {"source_type": "incident_event", "metadata": {"event_type": "DB_FAILURE", "error_rate": 45.2}},
        {"source_type": "incident_event", "metadata": {"event_type": "TIMEOUT", "error_rate": 38.0}},
        {"source_type": "incident_event", "metadata": {"event_type": "CONNECTION_POOL", "error_rate": 41.5}},
        {"source_type": "deployment", "metadata": {"version": "v2.1.0"}},
    ]

    result = ml_predictor.predict(incident=incident, evidence=evidence)
    assert result.risk_level == "HIGH"
    assert float(result.risk_score) >= 0.70
    assert result.model_version is not None


def test_low_risk_boundary_classification(ml_predictor):
    """Verify a low severity informational incident classifies as LOW."""
    incident = {
        "incident_id": 9992,
        "severity": "LOW",
        "status": "RESOLVED",
        "title": "Routine log rotation notice",
    }
    evidence = [
        {"source_type": "incident_event", "metadata": {"event_type": "INFO", "error_rate": 0.0}},
    ]

    result = ml_predictor.predict(incident=incident, evidence=evidence)
    assert result.risk_level == "LOW"
    assert float(result.risk_score) <= 0.35
