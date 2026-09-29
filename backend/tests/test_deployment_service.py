from datetime import datetime, timezone

from app.services.deployment_service import DeploymentService


class FakeDeploymentRepository:

    def get_recent_by_service(
        self,
        *,
        service_id,
        environment,
        before_time,
        limit,
    ):
        assert service_id == 1
        assert environment == "production"
        assert limit == 5

        return [
            {
                "version": "2.8.1",
            }
        ]


def test_get_recent_deployments():
    repository = FakeDeploymentRepository()

    service = DeploymentService(
        db=None,
        repository=repository,
    )

    result = service.get_recent_deployments(
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

    assert len(result) == 1
    assert result[0]["version"] == "2.8.1"