from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService
from app.services.investigation_service import InvestigationService


def make_service(db_session):
    inv_repo = InvestigationRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    user_repo = UserRepository(db_session)
    audit_repo = AuditLogRepository(db_session)
    audit_service = AuditLogService(db_session, audit_repo, user_repo)
    return InvestigationService(db_session, inv_repo, inc_repo, audit_service)


def test_mark_running(db_session):
    service = make_service(db_session)
    inv = service.create_investigation(
        incident_id=1,
        investigation_type="ASSISTED",
        question="Testing running state transition",
        actor_user_id=1,
    )
    assert inv.status == "STARTED"

    running_inv = service.mark_running(investigation_id=inv.investigation_id)
    assert running_inv.status == "RUNNING"


def test_mark_completed(db_session):
    service = make_service(db_session)
    inv = service.create_investigation(
        incident_id=1,
        investigation_type="ASSISTED",
        question="Testing completed state transition",
        actor_user_id=1,
    )

    completed_inv = service.mark_completed(
        investigation_id=inv.investigation_id,
        final_summary="Analysis completed successfully.",
    )
    assert completed_inv.status == "COMPLETED"
    assert completed_inv.completed_at is not None
    assert completed_inv.final_summary == "Analysis completed successfully."


def test_mark_failed(db_session):
    service = make_service(db_session)
    inv = service.create_investigation(
        incident_id=1,
        investigation_type="ASSISTED",
        question="Testing failed state transition",
        actor_user_id=1,
    )

    failed_inv = service.mark_failed(
        investigation_id=inv.investigation_id,
        error_message="Simulation error occurred.",
    )
    assert failed_inv.status == "FAILED"
    assert failed_inv.completed_at is not None
    assert "Simulation error occurred" in failed_inv.final_summary


def test_get_investigation_audit(db_session):
    service = make_service(db_session)
    inv = service.create_investigation(
        incident_id=1,
        investigation_type="ASSISTED",
        question="Testing audit retrieval",
        actor_user_id=1,
    )

    rows = service.get_investigation_audit(inv.investigation_id)
    assert isinstance(rows, list)
    assert len(rows) >= 1
    for row in rows:
        assert row.resource_type == "INVESTIGATION"
        assert row.resource_id == str(inv.investigation_id)


def test_get_investigation_audit_missing(db_session):
    import pytest
    from app.core.exceptions import NotFoundError

    service = make_service(db_session)

    with pytest.raises(NotFoundError):
        service.get_investigation_audit(999999)

