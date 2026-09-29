from decimal import Decimal
from sqlalchemy import select

from app.models.investigation import Investigation
from app.models.risk_prediction import RiskPrediction
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.risk_prediction_repository import RiskPredictionRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService
from app.services.investigation_service import InvestigationService
from app.services.risk_prediction_service import RiskPredictionService


class FakeInvestigationGraph:
    class GraphWrapper:
        def invoke(self, state):
            return {
                "status": "COMPLETED",
                "current_stage": "risk_predicted",
                "final_summary": "Payment API incident analyzed with high risk.",
                "tool_results": [
                    {
                        "tool_name": "get_incident",
                        "status": "SUCCESS",
                        "data": {"incident_number": "INC-1042"},
                    }
                ],
                "evidence": [
                    {
                        "source_type": "deployment",
                        "source_id": "3",
                        "title": "Deployment 2.8.1",
                        "content": "Deployment completed",
                        "metadata": {"version": "2.8.1"},
                    }
                ],
                "findings": [
                    {
                        "finding": "Deployment 2.8.1 occurred right before the incident.",
                        "confidence": "HIGH",
                        "evidence_refs": [{"source_type": "deployment", "source_id": "3"}],
                    }
                ],
                "risk_prediction": {
                    "model_name": "incident_risk_baseline",
                    "model_version": "1.0.0",
                    "risk_score": Decimal("0.70"),
                    "risk_level": "HIGH",
                    "features": {
                        "severity": "HIGH",
                        "status": "INVESTIGATING",
                        "event_count": 5,
                        "timeout_count": 1,
                        "error_rate_percent": 13.7,
                        "recent_deployment": True,
                    },
                    "explanation": "High incident severity. A timeout-related event was observed.",
                },
            }

    graph = GraphWrapper()


class FailingGraph:
    class GraphWrapper:
        def invoke(self, state):
            raise RuntimeError("Gemini LLM invocation timed out or failed.")

    graph = GraphWrapper()


def test_full_investigation_persists_risk(db_session):
    inv_repo = InvestigationRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    user_repo = UserRepository(db_session)
    audit_repo = AuditLogRepository(db_session)
    audit_service = AuditLogService(db_session, audit_repo, user_repo)
    risk_repo = RiskPredictionRepository(db_session)
    risk_service = RiskPredictionService(db_session, risk_repo)

    service = InvestigationService(
        db=db_session,
        repository=inv_repo,
        incident_repository=inc_repo,
        audit_log_service=audit_service,
        risk_prediction_service=risk_service,
    )

    investigation = service.run_investigation(
        incident_id=1,
        question="Why is the Payment API failing?",
        actor_user_id=1,
        investigation_type="ASSISTED",
        graph=FakeInvestigationGraph(),
    )

    assert investigation is not None
    assert investigation.status == "COMPLETED"
    assert investigation.completed_at is not None

    prediction = risk_repo.get_latest_by_investigation(investigation.investigation_id)

    assert prediction is not None
    assert prediction.prediction_type == "INCIDENT_ESCALATION"
    assert prediction.model_name == "incident_risk_baseline"
    assert prediction.model_version == "1.0.0"
    assert prediction.risk_score == Decimal("0.7000")
    assert prediction.risk_level == "HIGH"
    assert prediction.prediction_metadata["severity"] == "HIGH"
    assert prediction.prediction_explanation.startswith("High incident severity")


def test_investigation_failure_is_persisted_as_failed(db_session):
    inv_repo = InvestigationRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    user_repo = UserRepository(db_session)
    audit_repo = AuditLogRepository(db_session)
    audit_service = AuditLogService(db_session, audit_repo, user_repo)
    risk_repo = RiskPredictionRepository(db_session)
    risk_service = RiskPredictionService(db_session, risk_repo)

    service = InvestigationService(
        db=db_session,
        repository=inv_repo,
        incident_repository=inc_repo,
        audit_log_service=audit_service,
        risk_prediction_service=risk_service,
    )

    failed_caught = False
    try:
        service.run_investigation(
            incident_id=1,
            question="Why is Payment API failing?",
            actor_user_id=1,
            graph=FailingGraph(),
        )
    except Exception:
        failed_caught = True

    assert failed_caught is True

    latest_inv = db_session.scalars(
        select(Investigation)
        .where(Investigation.incident_id == 1)
        .order_by(Investigation.investigation_id.desc())
    ).first()

    assert latest_inv is not None
    assert latest_inv.status == "FAILED"
    assert latest_inv.completed_at is not None
    assert "Gemini LLM invocation timed out" in latest_inv.final_summary
