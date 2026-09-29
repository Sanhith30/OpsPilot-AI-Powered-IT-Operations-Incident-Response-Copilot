from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


def test_get_by_resource(db_session):
    repo = AuditLogRepository(db_session)
    log = AuditLog(
        actor_user_id=1,
        actor_type="USER",
        action="TEST_ACTION",
        resource_type="INVESTIGATION",
        resource_id="999",
        action_result="SUCCESS",
    )
    repo.add(log)
    db_session.flush()

    rows = repo.get_by_resource(
        resource_type="INVESTIGATION",
        resource_id="999",
    )

    assert isinstance(rows, list)
    assert len(rows) >= 1
    assert rows[0].resource_type == "INVESTIGATION"
    assert rows[0].resource_id == "999"
    assert rows[0].action == "TEST_ACTION"
