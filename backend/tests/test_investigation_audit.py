from decimal import Decimal

from app.models.investigation import Investigation
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.risk_prediction_repository import RiskPredictionRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService
from app.services.investigation_service import InvestigationService
from app.services.risk_prediction_service import RiskPredictionService


class FakeSuccessGraph:
    class GraphWrapper:
        def invoke(self, state):
            return {
                "status": "COMPLETED",
                "current_stage": "risk_predicted",
                "final_summary": "Payment API incident completed successfully.",
                "tool_results": [],
                "evidence": [],
                "findings": [],
                "risk_prediction": {
                    "model_name": "incident_risk_baseline",
                    "model_version": "1.0.0",
                    "risk_score": Decimal("0.70"),
                    "risk_level": "HIGH",
                    "features": {"severity": "HIGH"},
                    "explanation": "High incident severity.",
                },
            }

    graph = GraphWrapper()


class FakeFailingGraph:
    class GraphWrapper:
        def invoke(self, state):
            raise RuntimeError("LangGraph LLM inference failure simulation")

    graph = GraphWrapper()


def make_service(db_session):
    inv_repo = InvestigationRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    user_repo = UserRepository(db_session)
    audit_repo = AuditLogRepository(db_session)
    audit_service = AuditLogService(db_session, audit_repo, user_repo)
    risk_repo = RiskPredictionRepository(db_session)
    risk_service = RiskPredictionService(db_session, risk_repo)

    return (
        InvestigationService(
            db=db_session,
            repository=inv_repo,
            incident_repository=inc_repo,
            audit_log_service=audit_service,
            risk_prediction_service=risk_service,
        ),
        audit_repo,
    )


def test_investigation_completed_creates_audit_trail(db_session):
    service, audit_repo = make_service(db_session)

    inv = service.create_investigation(
        incident_id=1,
        investigation_type="ASSISTED",
        question="Audit trail test for completed investigation",
        actor_user_id=1,
    )

    detail = service.run_investigation(
        incident_id=1,
        question="Audit trail test for completed investigation",
        actor_user_id=1,
        investigation_id=inv.investigation_id,
        graph=FakeSuccessGraph(),
    )

    assert detail.status == "COMPLETED"

    # Query audit logs for this investigation
    audit_records = audit_repo.get_by_resource(
        resource_type="INVESTIGATION",
        resource_id=str(inv.investigation_id),
    )

    actions = {r.action for r in audit_records}
    assert "CREATE_INVESTIGATION" in actions
    assert "EXECUTE_INVESTIGATION" in actions
    assert "INVESTIGATION_COMPLETED" in actions

    completed_entry = next(
        r for r in audit_records if r.action == "INVESTIGATION_COMPLETED"
    )
    assert completed_entry.action_result == "SUCCESS"
    assert completed_entry.investigation_id == inv.investigation_id
    assert completed_entry.details["status"] == "COMPLETED"


def test_investigation_failed_creates_failure_audit_trail(db_session):
    service, audit_repo = make_service(db_session)

    inv = service.create_investigation(
        incident_id=1,
        investigation_type="ASSISTED",
        question="Audit trail test for failed investigation",
        actor_user_id=1,
    )

    try:
        service.run_investigation(
            incident_id=1,
            question="Audit trail test for failed investigation",
            actor_user_id=1,
            investigation_id=inv.investigation_id,
            graph=FakeFailingGraph(),
        )
    except Exception:
        pass

    audit_records = audit_repo.get_by_resource(
        resource_type="INVESTIGATION",
        resource_id=str(inv.investigation_id),
    )

    actions = {r.action for r in audit_records}
    assert "CREATE_INVESTIGATION" in actions
    assert "INVESTIGATION_FAILED" in actions

    failed_entry = next(
        r for r in audit_records if r.action == "INVESTIGATION_FAILED"
    )
    assert failed_entry.action_result == "FAILURE"
    assert failed_entry.investigation_id == inv.investigation_id
    assert failed_entry.details["status"] == "FAILED"
    assert "LLM inference failure" in failed_entry.details["error_message"]
