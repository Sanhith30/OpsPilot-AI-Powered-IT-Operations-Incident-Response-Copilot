from __future__ import annotations

from typing import Any


class IncidentRiskPredictor:
    """
    Deterministic ML / feature-based incident escalation risk predictor.
    Calculates incident escalation risk from incident attributes and unified evidence features.
    """

    MODEL_NAME = "incident_escalation_model"
    MODEL_VERSION = "1.0.0"

    SEVERITY_WEIGHTS = {
        "CRITICAL": 0.40,
        "HIGH": 0.30,
        "MEDIUM": 0.20,
        "LOW": 0.10,
    }

    def predict(
        self,
        *,
        incident: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> dict[str, Any]:
        severity = str(incident.get("severity", "MEDIUM")).upper()
        base_score = self.SEVERITY_WEIGHTS.get(severity, 0.20)

        # Feature 1: Deployments temporally close to incident
        deployments = [e for e in evidence if e.get("source_type") == "deployment"]
        has_recent_deployment = len(deployments) > 0
        deployment_weight = 0.25 if has_recent_deployment else 0.0

        # Feature 2: Critical events / timeouts / errors in evidence
        events = [e for e in evidence if e.get("source_type") == "incident_event"]
        has_timeouts_or_errors = any(
            any(
                kw in str(e.get("content", "")).lower() or kw in str(e.get("title", "")).lower()
                for kw in ("timeout", "500", "error", "fail", "alert")
            )
            for e in events
        )
        error_weight = 0.25 if has_timeouts_or_errors else 0.0

        # Feature 3: Blast radius / active status
        active_status = incident.get("status") in ("OPEN", "INVESTIGATING")
        status_weight = 0.05 if active_status else 0.0

        calculated_score = min(
            0.98,
            max(0.05, base_score + deployment_weight + error_weight + status_weight),
        )
        calculated_score = round(calculated_score, 4)

        if calculated_score >= 0.85:
            risk_level = "CRITICAL"
        elif calculated_score >= 0.70:
            risk_level = "HIGH"
        elif calculated_score >= 0.40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        explanation = (
            f"Escalation risk assessed as {risk_level} (score: {calculated_score:.2f}) based on "
            f"{severity} severity, {len(deployments)} recent deployment(s), and "
            f"{len(events)} timeline event(s)."
        )

        return {
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
            "prediction_type": "INCIDENT_ESCALATION",
            "risk_score": calculated_score,
            "risk_level": risk_level,
            "prediction_explanation": explanation,
            "factors": {
                "incident_severity": severity,
                "has_recent_deployment": has_recent_deployment,
                "deployment_count": len(deployments),
                "has_timeouts_or_errors": has_timeouts_or_errors,
                "event_count": len(events),
            },
        }
