from datetime import datetime, timezone

from app.ai.tools.deployment_tools import (
    GetRecentDeploymentsTool,
)


class FakeDeployment:
    deployment_id = 3
    service_id = 1
    version = "2.8.1"
    environment = "production"
    commit_hash = "abc123"
    deployment_type = "STANDARD"
    trigger_type = "MANUAL"
    status = "SUCCESS"

    started_at = datetime(
        2026,
        9,
        26,
        14,
        45,
        tzinfo=timezone.utc,
    )

    completed_at = datetime(
        2026,
        9,
        26,
        14,
        50,
        tzinfo=timezone.utc,
    )

    deployed_by = 4


class FakeDeploymentService:

    def get_recent_deployments(
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
            FakeDeployment()
        ]


def test_get_recent_deployments_tool():

    tool = GetRecentDeploymentsTool(
        deployment_service=FakeDeploymentService()
    )

    result = tool.run(
        {
            "service_id": 1,
            "environment": "production",
            "before_time": "2026-09-26T09:20:00+00:00",
            "limit": 5,
        }
    )

    assert result.tool_name == "get_recent_deployments"
    assert result.status == "SUCCESS"

    assert result.data["service_id"] == 1

    assert (
        len(result.data["deployments"])
        == 1
    )

    deployment = result.data["deployments"][0]

    assert deployment["deployment_id"] == 3
    assert deployment["version"] == "2.8.1"
    assert deployment["status"] == "SUCCESS"