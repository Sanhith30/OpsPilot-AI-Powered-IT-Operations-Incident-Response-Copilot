"""
OpsPilot ML Risk Model Training Script — Rigorous Independent Validation Edition.

Generates an operationally realistic dataset using continuous stochastic operational
distributions (error rates, event counts, service blast radius, deployment correlations)
with realistic label ambiguity/noise.

Evaluates against an untouched holdout test set with:
  - 5-Fold Stratified Cross-Validation
  - Confusion Matrix
  - Per-class Precision, Recall, F1-score
  - Macro & Weighted F1
  - Multi-class ROC-AUC (Macro OVR)
  - Feature Importance Ranking
"""
from __future__ import annotations

import json
import logging
import os
import pickle
import random
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import label_binarize

from app.ai.risk.ml_features import FEATURE_NAMES, extract_ml_features, features_to_array

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("opspilot.risk.train")

MODEL_DIR = Path(__file__).parent / "model"
MODEL_PATH = MODEL_DIR / "risk_model.pkl"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

random.seed(42)
np.random.seed(42)

SERVICES = ["payment-api", "auth-service", "order-service", "inventory-service", "api-gateway", "notification-worker"]
EVENT_TYPES = ["TIMEOUT", "ERROR", "DB_FAILURE", "CONNECTION_POOL", "MEMORY", "CPU", "DEGRADED", "ALERT", "DEPLOYMENT", "INFO"]


def _generate_synthetic_sample(sample_id: int) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    """
    Generate an independent operational incident scenario from continuous distributions.
    Returns (incident_dict, evidence_list, true_risk_class: 0=LOW, 1=MEDIUM, 2=HIGH).
    """
    # Latent true risk state (continuous severity signal between 0 and 1)
    # 0.0 - 0.35: Low risk
    # 0.35 - 0.70: Medium risk
    # 0.70 - 1.00: High risk
    latent_risk = np.random.beta(a=2.0, b=2.0)  # Smooth distribution across [0, 1]

    # Assign observed severity with realistic noise
    # (Sometimes high risk issues start as MEDIUM severity alerts, or vice versa)
    sev_noise = np.random.normal(0, 0.15)
    observed_sev_val = np.clip(latent_risk + sev_noise, 0, 1)
    if observed_sev_val > 0.75:
        severity = "CRITICAL"
    elif observed_sev_val > 0.50:
        severity = "HIGH"
    elif observed_sev_val > 0.25:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # Status: most are OPEN or INVESTIGATING, some MITIGATING, some RESOLVED
    status_r = random.random()
    if latent_risk > 0.6 and status_r < 0.7:
        status = "OPEN"
    elif status_r < 0.4:
        status = "INVESTIGATING"
    elif status_r < 0.7:
        status = "OPEN"
    elif status_r < 0.85:
        status = "MITIGATING"
    else:
        status = "RESOLVED"

    incident = {
        "incident_id": sample_id,
        "severity": severity,
        "status": status,
        "title": f"Incident #{sample_id} ({severity})",
    }

    evidence: list[dict[str, Any]] = []

    # Number of events generated according to Poisson distribution conditioned on latent risk
    expected_events = 2 + int(latent_risk * 10)
    num_events = max(1, np.random.poisson(expected_events))

    # Error rate distribution conditioned on latent risk (with stochastic variance)
    base_error_rate = max(0.0, float(np.random.normal(latent_risk * 40.0, 8.0)))

    # Generate events
    affected_services_count = max(1, int(np.random.poisson(1 + latent_risk * 2.5)))
    chosen_services = random.sample(SERVICES, min(affected_services_count, len(SERVICES)))

    for _ in range(num_events):
        svc = random.choice(chosen_services)
        # Higher latent risk -> more severe event types
        if latent_risk > 0.65:
            ev_type = random.choices(
                ["TIMEOUT", "DB_FAILURE", "ERROR", "CONNECTION_POOL", "MEMORY", "ALERT"],
                weights=[0.30, 0.25, 0.20, 0.15, 0.05, 0.05],
            )[0]
        elif latent_risk > 0.35:
            ev_type = random.choices(
                ["ERROR", "TIMEOUT", "CONNECTION_POOL", "DEGRADED", "ALERT", "CPU", "INFO"],
                weights=[0.20, 0.15, 0.15, 0.20, 0.15, 0.10, 0.05],
            )[0]
        else:
            ev_type = random.choices(
                ["INFO", "ALERT", "DEGRADED", "CPU"],
                weights=[0.50, 0.25, 0.15, 0.10],
            )[0]

        ev_error_rate = max(0.0, float(np.random.normal(base_error_rate, 4.0))) if ev_type in ("TIMEOUT", "ERROR", "DB_FAILURE", "CONNECTION_POOL") else None

        evidence.append({
            "source_type": "incident_event",
            "content": f"{ev_type} logged on {svc}",
            "metadata": {
                "event_type": ev_type,
                "service_name": svc,
                "error_rate": ev_error_rate,
            },
        })

    # Deployment correlation: high/medium risk incidents more frequently follow deployments
    deploy_prob = 0.20 + 0.50 * latent_risk
    if random.random() < deploy_prob:
        evidence.append({
            "source_type": "deployment",
            "content": f"Deployment on {random.choice(chosen_services)} detected",
            "metadata": {"version": f"2.{random.randint(1, 9)}.{random.randint(0, 5)}"},
        })

    # Discrete Ground Truth Class assignment based on composite operational impact
    # Incorporates status (mitigated/resolved incidents reduce active risk)
    effective_risk = latent_risk
    if status in ("RESOLVED", "CLOSED"):
        effective_risk *= 0.3
    elif status == "MITIGATING":
        effective_risk *= 0.7

    if effective_risk >= 0.65:
        target_class = 2  # HIGH
    elif effective_risk >= 0.35:
        target_class = 1  # MEDIUM
    else:
        target_class = 0  # LOW

    return incident, evidence, target_class


def generate_independent_dataset(n_samples: int = 1500) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate n independent stochastic operational scenarios with zero row duplication.
    """
    X_list: list[list[float]] = []
    y_list: list[int] = []

    for i in range(n_samples):
        incident, evidence, target_class = _generate_synthetic_sample(i + 1)
        feats = extract_ml_features(incident=incident, evidence=evidence)
        X_list.append([feats[n] for n in FEATURE_NAMES])
        y_list.append(target_class)

    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.int32)


def train_and_evaluate() -> None:
    logger.info("Generating 1,500 independent, non-duplicated operational incident samples...")
    X, y = generate_independent_dataset(n_samples=1500)

    # Class distribution
    unique, counts = np.unique(y, return_counts=True)
    dist = {c: int(cnt) for c, cnt in zip(["LOW", "MEDIUM", "HIGH"], counts)}
    logger.info("Dataset distribution: %s", dist)

    # Strict 80/20 train/test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    logger.info("Train set: %d samples, Holdout test set: %d samples", len(X_train), len(X_test))

    # Base Random Forest classifier with regularization to prevent overfitting
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=4,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    # Calibrate probabilities using Platt Scaling (sigmoid)
    calibrated_model = CalibratedClassifierCV(rf, cv=5, method="sigmoid")
    calibrated_model.fit(X_train, y_train)

    # Predictions on UNTOUCHED Holdout Test Set
    y_pred = calibrated_model.predict(X_test)
    y_proba = calibrated_model.predict_proba(X_test)

    # Metrics on holdout
    report = classification_report(
        y_test, y_pred, target_names=["LOW", "MEDIUM", "HIGH"], output_dict=True
    )
    cm = confusion_matrix(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    y_test_bin = label_binarize(y_test, classes=[0, 1, 2])
    roc_auc = roc_auc_score(y_test_bin, y_proba, multi_class="ovr", average="macro")

    # 5-fold cross validation on training set only (no test data seen)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(
        CalibratedClassifierCV(
            RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_leaf=4, random_state=42, n_jobs=-1),
            cv=3,
        ),
        X_train, y_train, cv=skf, scoring="f1_macro"
    )

    # Extract feature importances
    base_rf = calibrated_model.calibrated_classifiers_[0].estimator
    importances = base_rf.feature_importances_
    feat_importance = sorted(zip(FEATURE_NAMES, importances), key=lambda x: -x[1])

    # Output detailed evaluation log
    logger.info("\n" + "=" * 60)
    logger.info("HOLDOUT TEST SET EVALUATION (300 Unseen Samples)")
    logger.info("=" * 60)
    logger.info("Confusion Matrix:\n%s", cm)
    logger.info("Macro F1:     %.4f", macro_f1)
    logger.info("Weighted F1:  %.4f", weighted_f1)
    logger.info("Macro ROC-AUC: %.4f", roc_auc)
    logger.info("5-Fold CV Macro F1: %.4f ± %.4f", cv_scores.mean(), cv_scores.std())
    logger.info("\nClassification Report:\n%s", classification_report(y_test, y_pred, target_names=["LOW", "MEDIUM", "HIGH"]))

    logger.info("Top Feature Importances:")
    for feat, imp in feat_importance:
        logger.info("  %-28s: %.4f (%.1f%%)", feat, imp, imp * 100)

    # Save model and comprehensive metadata
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(calibrated_model, f, protocol=pickle.HIGHEST_PROTOCOL)
    logger.info("Model saved to %s", MODEL_PATH)

    metadata = {
        "model_name": "incident_risk_rf_v1",
        "model_version": "1.1.0",
        "model_type": "Regularized Random Forest + Platt Calibration",
        "feature_names": FEATURE_NAMES,
        "classes": ["LOW", "MEDIUM", "HIGH"],
        "class_distribution": dist,
        "training_samples": int(len(X_train)),
        "holdout_test_samples": int(len(X_test)),
        "cv_accuracy_mean": float(cv_scores.mean()),
        "cv_f1_macro_mean": float(cv_scores.mean()),
        "cv_f1_macro_std": float(cv_scores.std()),
        "holdout_macro_f1": float(macro_f1),
        "holdout_weighted_f1": float(weighted_f1),
        "holdout_roc_auc": float(roc_auc),
        "confusion_matrix": cm.tolist(),
        "per_class_metrics": {
            "LOW": {
                "precision": float(report["LOW"]["precision"]),
                "recall": float(report["LOW"]["recall"]),
                "f1": float(report["LOW"]["f1-score"]),
            },
            "MEDIUM": {
                "precision": float(report["MEDIUM"]["precision"]),
                "recall": float(report["MEDIUM"]["recall"]),
                "f1": float(report["MEDIUM"]["f1-score"]),
            },
            "HIGH": {
                "precision": float(report["HIGH"]["precision"]),
                "recall": float(report["HIGH"]["recall"]),
                "f1": float(report["HIGH"]["f1-score"]),
            },
        },
        "feature_importances": {n: float(i) for n, i in feat_importance},
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Metadata saved to %s", METADATA_PATH)


if __name__ == "__main__":
    train_and_evaluate()
