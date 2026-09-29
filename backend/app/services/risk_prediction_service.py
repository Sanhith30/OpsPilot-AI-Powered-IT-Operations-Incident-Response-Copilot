from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.ai.risk.schemas import RiskPredictionResult
from app.core.exceptions import NotFoundError, ValidationError
from app.models.risk_prediction import RiskPrediction


class RiskPredictionService:
    VALID_RISK_LEVELS = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }

    DEFAULT_PREDICTION_TYPE = "INCIDENT_ESCALATION"

    def __init__(
        self,
        db,
        repository,
        incident_repository=None,
        investigation_repository=None,
    ):
        self.db = db
        self.repository = repository
        self.incident_repository = incident_repository
        self.investigation_repository = investigation_repository

    def get_by_id(self, prediction_id):
        prediction = self.repository.get_by_id(prediction_id)

        if prediction is None:
            raise NotFoundError("Risk prediction not found.")

        return prediction

    def get_by_investigation(self, investigation_id):
        if self.investigation_repository.get_by_id(investigation_id) is None:
            raise NotFoundError("Investigation not found.")

        return self.repository.get_by_investigation(
            investigation_id
        )

    def get_by_incident(self, incident_id):
        if self.incident_repository.get_by_id(incident_id) is None:
            raise NotFoundError("Incident not found.")

        return self.repository.get_by_incident(
            incident_id
        )

    def create_from_prediction(
        self,
        *,
        incident_id: int,
        investigation_id: int,
        prediction: Any,
    ) -> RiskPrediction:
        """
        Persist a prediction result produced by RiskPredictor or LangGraph.
        Accepts either a RiskPredictionResult instance or a dictionary.
        """
        if isinstance(prediction, dict):
            model_name = prediction.get("model_name", "incident_risk_baseline")
            model_version = prediction.get("model_version", "1.0.0")
            risk_score = prediction.get("risk_score", Decimal("0.50"))
            risk_level = prediction.get("risk_level", "MEDIUM")
            features = (
                prediction.get("features")
                if prediction.get("features") is not None
                else prediction.get("factors")
            )
            explanation = (
                prediction.get("explanation")
                if prediction.get("explanation") is not None
                else prediction.get("prediction_explanation")
            )
        else:
            model_name = getattr(prediction, "model_name", "incident_risk_baseline")
            model_version = getattr(prediction, "model_version", "1.0.0")
            risk_score = getattr(prediction, "risk_score", Decimal("0.50"))
            risk_level = getattr(prediction, "risk_level", "MEDIUM")
            features = getattr(prediction, "features", {})
            explanation = getattr(prediction, "explanation", "")

        return self.create_prediction(
            incident_id=incident_id,
            investigation_id=investigation_id,
            model_name=model_name,
            model_version=model_version,
            prediction_type="INCIDENT_ESCALATION",
            risk_score=Decimal(str(risk_score)),
            risk_level=risk_level,
            metadata=features,
            explanation=explanation,
        )

    def create_prediction(
        self,
        *,
        incident_id,
        model_name,
        model_version,
        risk_score,
        risk_level,
        investigation_id=None,
        prediction_type=DEFAULT_PREDICTION_TYPE,
        metadata=None,
        prediction_explanation=None,
        explanation=None,
        predicted_at=None,
    ):
        final_explanation = (
            prediction_explanation
            if prediction_explanation is not None
            else explanation
        )
        try:
            # -----------------------------
            # Basic validation
            # -----------------------------
            if not model_name or not model_name.strip():
                raise ValidationError(
                    "Model name cannot be empty."
                )

            if not model_version or not model_version.strip():
                raise ValidationError(
                    "Model version cannot be empty."
                )

            if not prediction_type or not prediction_type.strip():
                raise ValidationError(
                    "Prediction type cannot be empty."
                )

            if risk_level not in self.VALID_RISK_LEVELS:
                raise ValidationError(
                    f"Invalid risk level: {risk_level}"
                )

            # -----------------------------
            # Validate risk score
            # -----------------------------
            try:
                score = Decimal(str(risk_score))
            except Exception:
                raise ValidationError(
                    "risk_score must be a valid number."
                )

            if score < Decimal("0") or score > Decimal("1"):
                raise ValidationError(
                    "risk_score must be between 0 and 1."
                )

            # -----------------------------
            # Validate incident
            # -----------------------------
            if self.incident_repository is not None:
                incident = self.incident_repository.get_by_id(
                    incident_id
                )

                if incident is None:
                    raise NotFoundError(
                        "Incident not found."
                    )

            # -----------------------------
            # Validate investigation
            # -----------------------------
            if investigation_id is not None and self.investigation_repository is not None:
                investigation = (
                    self.investigation_repository.get_by_id(
                        investigation_id
                    )
                )

                if investigation is None:
                    raise NotFoundError(
                        "Investigation not found."
                    )

                if investigation.incident_id != incident_id:
                    raise ValidationError(
                        "Investigation does not belong to the incident."
                    )

            # -----------------------------
            # Create prediction
            # -----------------------------
            prediction = RiskPrediction(
                incident_id=incident_id,
                investigation_id=investigation_id,
                model_name=model_name.strip(),
                model_version=model_version.strip(),
                prediction_type=prediction_type.strip(),
                risk_score=score,
                risk_level=risk_level,
                prediction_metadata=metadata,
                prediction_explanation=final_explanation,
                predicted_at=(
                    predicted_at
                    or datetime.now(timezone.utc)
                ),
            )

            self.repository.add(prediction)

            self.db.flush()
            self.db.commit()

            return prediction

        except Exception:
            self.db.rollback()
            raise