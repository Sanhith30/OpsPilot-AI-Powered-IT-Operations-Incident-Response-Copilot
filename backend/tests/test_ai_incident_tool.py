from datetime import datetime, timezone

from app.ai.tools.incident_tools import GetIncidentTool


class FakeIncident:
    incident_id = 1
    incident_number = "INC-1042"
    service_id = 1
    title = "Payment API elevated error rate"
    description = "Payment API is experiencing elevated errors."
    severity = "HIGH"
    status = "INVESTIGATING"
    started_at = datetime(
        2026,
        9,
        26,
        9,
        20,
        tzinfo=timezone.utc,
    )
    detected_at = datetime(
        2026,
        9,
        26,
        9,
        24,
        tzinfo=timezone.utc,
    )
    resolved_at = None
    assigned_team_id = 1
    assigned_user_id = 2
    impact_summary = "Payment failures affecting customers."
    root_cause = None


class FakeIncidentService:
    def get_incident_by_id(self, incident_id):
        assert incident_id == 1
        return FakeIncident()


def test_get_incident_tool_success():
    tool = GetIncidentTool(
        FakeIncidentService()
    )

    result = tool.run(
        {
            "incident_id": 1,
        }
    )

    assert result.tool_name == "get_incident"
    assert result.status == "SUCCESS"
    assert result.data["incident_number"] == "INC-1042"
    assert result.data["severity"] == "HIGH"
    assert result.data["status"] == "INVESTIGATING"
    assert result.data["root_cause"] is None
    assert result.execution_time_ms is not None