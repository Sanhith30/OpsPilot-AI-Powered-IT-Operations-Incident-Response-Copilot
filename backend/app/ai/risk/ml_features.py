"""
ML Risk Feature Engineering for OpsPilot Incident Risk Prediction.

Extends the base extract_risk_features function with richer numerical
features suitable for a trained ML model (Random Forest / XGBoost).
"""
from __future__ import annotations

from typing import Any

import numpy as np


# ------------------------------------------------------------------ #
# Severity / Status encoding                                           #
# ------------------------------------------------------------------ #

SEVERITY_SCORES = {
    "CRITICAL": 1.0,
    "HIGH": 0.75,
    "MEDIUM": 0.50,
    "LOW": 0.25,
    "UNKNOWN": 0.0,
}

STATUS_SCORES = {
    "OPEN": 1.0,
    "INVESTIGATING": 0.85,
    "MITIGATING": 0.60,
    "RESOLVED": 0.20,
    "CLOSED": 0.05,
    "UNKNOWN": 0.5,
}

EVENT_TYPE_WEIGHTS = {
    "TIMEOUT": 1.0,
    "ERROR": 0.9,
    "DB_FAILURE": 0.95,
    "CONNECTION_POOL": 0.9,
    "MEMORY": 0.7,
    "CPU": 0.6,
    "DEGRADED": 0.5,
    "ALERT": 0.5,
    "DEPLOYMENT": 0.4,
    "INFO": 0.1,
}


def extract_ml_features(
    *,
    incident: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> dict[str, float]:
    """
    Extract a rich numerical feature vector from incident + evidence.

    Returns a dict of named float features that maps 1-to-1 to the
    FEATURE_NAMES constant below (order must match).
    """
    # ---- Incident features ----
    severity = str(incident.get("severity", "UNKNOWN")).upper()
    status = str(incident.get("status", "UNKNOWN")).upper()
    severity_score = SEVERITY_SCORES.get(severity, 0.0)
    status_score = STATUS_SCORES.get(status, 0.5)

    # ---- Event-based features ----
    event_count = 0
    timeout_count = 0
    error_count = 0
    db_failure_count = 0
    deployment_event_count = 0
    total_event_weight = 0.0
    error_rate_values: list[float] = []
    affected_services: set[str] = set()

    for item in evidence:
        source_type = item.get("source_type", "")
        metadata = item.get("metadata") or {}
        content = str(item.get("content", "")).upper()

        if source_type == "incident_event":
            event_count += 1
            event_type = str(metadata.get("event_type", "")).upper()

            # Map event type to weight
            matched_weight = 0.2  # default
            for key, weight in EVENT_TYPE_WEIGHTS.items():
                if key in event_type or key in content:
                    matched_weight = max(matched_weight, weight)
                    # Specific counters
                    if key == "TIMEOUT":
                        timeout_count += 1
                    elif key in ("ERROR", "DB_FAILURE", "CONNECTION_POOL"):
                        error_count += 1
                    if key == "DB_FAILURE":
                        db_failure_count += 1
                    if key == "DEPLOYMENT":
                        deployment_event_count += 1

            total_event_weight += matched_weight

            # Error rate
            possible_rate = metadata.get("error_rate")
            if possible_rate is not None:
                try:
                    val = float(possible_rate)
                    if 0 <= val <= 100:
                        error_rate_values.append(val)
                except (TypeError, ValueError):
                    pass

            # Affected services
            svc = metadata.get("service_name") or metadata.get("service")
            if svc:
                affected_services.add(str(svc))

        elif source_type == "deployment":
            deployment_event_count += 1

    # ---- Derived features ----
    has_recent_deployment = float(
        any(item.get("source_type") == "deployment" for item in evidence)
        or deployment_event_count > 0
    )
    avg_error_rate = float(np.mean(error_rate_values)) if error_rate_values else 0.0
    max_error_rate = float(max(error_rate_values)) if error_rate_values else 0.0
    affected_service_count = float(len(affected_services))
    avg_event_weight = float(total_event_weight / event_count) if event_count > 0 else 0.0

    # Composite signal: severity × status interaction
    severity_status_signal = severity_score * status_score

    return {
        "severity_score": severity_score,
        "status_score": status_score,
        "severity_status_signal": severity_status_signal,
        "event_count": float(event_count),
        "timeout_count": float(timeout_count),
        "error_count": float(error_count),
        "db_failure_count": float(db_failure_count),
        "deployment_event_count": float(deployment_event_count),
        "has_recent_deployment": has_recent_deployment,
        "avg_error_rate": avg_error_rate,
        "max_error_rate": max_error_rate,
        "affected_service_count": affected_service_count,
        "avg_event_weight": avg_event_weight,
        "total_event_weight": total_event_weight,
    }


# Ordered list matching the numpy feature vector
FEATURE_NAMES = [
    "severity_score",
    "status_score",
    "severity_status_signal",
    "event_count",
    "timeout_count",
    "error_count",
    "db_failure_count",
    "deployment_event_count",
    "has_recent_deployment",
    "avg_error_rate",
    "max_error_rate",
    "affected_service_count",
    "avg_event_weight",
    "total_event_weight",
]


def features_to_array(feature_dict: dict[str, float]) -> np.ndarray:
    """Convert the feature dict to a 1×N numpy array for model inference."""
    return np.array(
        [[feature_dict[name] for name in FEATURE_NAMES]],
        dtype=np.float32,
    )
