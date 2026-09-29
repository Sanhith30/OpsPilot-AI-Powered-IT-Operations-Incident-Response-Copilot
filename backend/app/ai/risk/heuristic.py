from decimal import Decimal
from typing import Any

from app.ai.risk.base import RiskPredictor
from app.ai.risk.features import extract_risk_features
from app.ai.risk.schemas import RiskPredictionResult
from app.observability.metrics import RISK_PREDICTIONS_TOTAL
from app.observability.tracing import get_tracer

tracer = get_tracer("opspilot.risk")


class HeuristicRiskPredictor(RiskPredictor):

    model_name = "incident_risk_baseline"
    model_version = "1.0.0"

    def predict(
        self,
        *,
        incident: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> RiskPredictionResult:

        with tracer.start_as_current_span("risk_prediction") as span:
            features = extract_risk_features(
                incident=incident,
                evidence=evidence,
            )

            score = Decimal("0.00")
            reasons: list[str] = []

            severity = features["severity"]

            if severity == "CRITICAL":
                score += Decimal("0.40")
                reasons.append("Critical incident severity.")

            elif severity == "HIGH":
                score += Decimal("0.30")
                reasons.append("High incident severity.")

            elif severity == "MEDIUM":
                score += Decimal("0.15")
                reasons.append("Medium incident severity.")

            timeout_count = features["timeout_count"]

            if timeout_count >= 3:
                score += Decimal("0.30")
                reasons.append(
                    "Multiple timeout-related events were observed."
                )

            elif timeout_count >= 1:
                score += Decimal("0.15")
                reasons.append(
                    "A timeout-related event was observed."
                )

            error_rate = features["error_rate_percent"]

            if error_rate is not None:

                if error_rate >= 20:
                    score += Decimal("0.25")
                    reasons.append(
                        "Error rate exceeded 20%."
                    )

                elif error_rate >= 10:
                    score += Decimal("0.15")
                    reasons.append(
                        "Error rate exceeded 10%."
                    )

            if features["recent_deployment"]:
                score += Decimal("0.10")
                reasons.append(
                    "A recent deployment was associated with the incident timeline."
                )

            score = min(score, Decimal("1.00"))

            if score >= Decimal("0.70"):
                risk_level = "HIGH"

            elif score >= Decimal("0.40"):
                risk_level = "MEDIUM"

            else:
                risk_level = "LOW"

            explanation = (
                " ".join(reasons)
                if reasons
                else "No elevated-risk indicators were detected."
            )

            prediction = RiskPredictionResult(
                risk_score=score,
                risk_level=risk_level,
                model_name=self.model_name,
                model_version=self.model_version,
                features=features,
                explanation=explanation,
            )

            span.set_attribute(
                "opspilot.risk.level",
                prediction.risk_level,
            )
            span.set_attribute(
                "opspilot.risk.model",
                prediction.model_name,
            )

            RISK_PREDICTIONS_TOTAL.labels(
                risk_level=prediction.risk_level,
                model_name=prediction.model_name,
            ).inc()

            return prediction
