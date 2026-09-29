from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService


def make_audit_log_service(db_session):
    repo = AuditLogRepository(db_session)
    user_repo = UserRepository(db_session)
    return AuditLogService(db_session, repo, user_repo)


def test_get_by_resource(db_session):
    service = make_audit_log_service(db_session)
    service.add_to_transaction(
        action="TEST_SERVICE_AUDIT",
        user_id=1,
        resource_type="INVESTIGATION",
        resource_id=888,
        action_result="SUCCESS",
    )
    db_session.flush()

    rows = service.get_by_resource(
        resource_type="INVESTIGATION",
        resource_id=888,
    )

    assert isinstance(rows, list)
    assert len(rows) >= 1
    assert rows[0].resource_type == "INVESTIGATION"
    assert rows[0].resource_id == "888"
    assert rows[0].action == "TEST_SERVICE_AUDIT"
