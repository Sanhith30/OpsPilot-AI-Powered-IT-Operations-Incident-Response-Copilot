from decimal import Decimal

from app.ai.risk.schemas import RiskPredictionResult
from app.services.risk_prediction_service import RiskPredictionService


def make_service(db_session):
    from app.repositories.risk_prediction_repository import RiskPredictionRepository

    return RiskPredictionService(
        db=db_session,
        repository=RiskPredictionRepository(db_session),
    )


def test_create_from_prediction(db_session):
    prediction = RiskPredictionResult(
        risk_score=Decimal("0.70"),
        risk_level="HIGH",
        model_name="incident_risk_baseline",
        model_version="1.0.0",
        features={
            "severity": "HIGH",
            "status": "INVESTIGATING",
            "event_count": 5,
            "timeout_count": 1,
            "error_rate_percent": 13.7,
            "recent_deployment": True,
        },
        explanation="High incident severity. A timeout-related event was observed.",
    )

    service = make_service(db_session)

    saved = service.create_from_prediction(
        incident_id=1,
        investigation_id=1,
        prediction=prediction,
    )

    assert saved.prediction_id is not None
    assert saved.prediction_type == "INCIDENT_ESCALATION"
    assert saved.model_name == "incident_risk_baseline"
    assert saved.model_version == "1.0.0"
    assert saved.risk_score == Decimal("0.70")
    assert saved.risk_level == "HIGH"
    assert saved.prediction_metadata["severity"] == "HIGH"
    assert saved.prediction_metadata["recent_deployment"] is True
    assert saved.prediction_explanation.startswith("High incident severity")
