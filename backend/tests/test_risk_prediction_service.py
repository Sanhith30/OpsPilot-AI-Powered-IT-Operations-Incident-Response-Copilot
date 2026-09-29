from decimal import Decimal
import pytest
from app.core.exceptions import ValidationError
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.risk_prediction_repository import RiskPredictionRepository
from app.services.risk_prediction_service import RiskPredictionService
def make_service(db): return RiskPredictionService(db,RiskPredictionRepository(db),IncidentRepository(db),InvestigationRepository(db))
def test_create_valid_prediction(db_session):
    x=make_service(db_session).create_prediction(incident_id=1,investigation_id=1,model_name="pytest_model",model_version="0.0.1",risk_score=Decimal("0.7500"),risk_level="HIGH",metadata={"test":True}); assert x.prediction_id is not None; assert x.risk_score==Decimal("0.7500")
def test_reject_bad_score(db_session):
    with pytest.raises(ValidationError): make_service(db_session).create_prediction(incident_id=1,model_name="pytest_model",model_version="0.0.1",risk_score=Decimal("1.5000"),risk_level="HIGH")
def test_reject_bad_level(db_session):
    with pytest.raises(ValidationError): make_service(db_session).create_prediction(incident_id=1,model_name="pytest_model",model_version="0.0.1",risk_score=Decimal("0.5"),risk_level="EXTREME")


def test_create_from_prediction_object(db_session):
    from app.ai.risk.schemas import RiskPredictionResult

    result = RiskPredictionResult(
        risk_score=Decimal("0.70"),
        risk_level="HIGH",
        model_name="incident_risk_baseline",
        model_version="1.0.0",
        features={"severity": "HIGH", "timeout_count": 1},
        explanation="High severity and database timeout.",
    )

    saved = make_service(db_session).create_from_prediction(
        incident_id=1,
        investigation_id=1,
        prediction=result,
    )

    assert saved.prediction_id is not None
    assert saved.model_name == "incident_risk_baseline"
    assert saved.risk_score == Decimal("0.70")
    assert saved.risk_level == "HIGH"
    assert saved.prediction_type == "INCIDENT_ESCALATION"
    assert saved.prediction_metadata == {"severity": "HIGH", "timeout_count": 1}
    assert saved.prediction_explanation == "High severity and database timeout."


def test_create_from_prediction_dict(db_session):
    pred_dict = {
        "risk_score": "0.40",
        "risk_level": "MEDIUM",
        "model_name": "incident_risk_baseline",
        "model_version": "1.0.0",
        "features": {"severity": "MEDIUM"},
        "explanation": "Medium incident severity.",
    }

    saved = make_service(db_session).create_from_prediction(
        incident_id=1,
        investigation_id=1,
        prediction=pred_dict,
    )

    assert saved.prediction_id is not None
    assert saved.risk_level == "MEDIUM"
    assert saved.prediction_type == "INCIDENT_ESCALATION"
