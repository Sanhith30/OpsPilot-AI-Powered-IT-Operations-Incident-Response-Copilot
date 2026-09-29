from datetime import datetime, timezone

from app.repositories.deployment_repository import (
    DeploymentRepository,
)


def test_get_recent_by_service(db_session):
    repository = DeploymentRepository(
        db_session
    )

    deployments = repository.get_recent_by_service(
        service_id=1,
        environment="production",
        before_time=datetime(
            2026,
            9,
            26,
            9,
            20,
            tzinfo=timezone.utc,
        ),
        limit=5,
    )

    assert len(deployments) >= 1

    assert deployments[0].service_id == 1
    assert deployments[0].environment == "production"

    assert deployments[0].version == "2.8.1"