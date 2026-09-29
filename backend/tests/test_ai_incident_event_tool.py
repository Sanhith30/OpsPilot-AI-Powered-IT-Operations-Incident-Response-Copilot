from datetime import datetime, timezone

from app.ai.tools.incident_event_tools import (
    SearchIncidentEventsTool,
)


class FakeIncidentEvent:
    incident_event_id = 10
    incident_id = 1
    event_type = "ERROR"
    event_time = datetime(
        2026,
        9,
        26,
        9,
        10,
        tzinfo=timezone.utc,
    )
    description = "Payment database timeout detected"
    created_by = 4
    event_metadata = {
        "source": "monitoring",
    }


class FakeIncidentEventService:
    def get_events_by_incident(
        self,
        *,
        incident_id,
        before_time=None,
        limit=50,
    ):
        assert incident_id == 1
        assert limit == 10

        return [FakeIncidentEvent()]


def test_search_incident_events_tool():
    tool = SearchIncidentEventsTool(
        incident_event_service=FakeIncidentEventService()
    )

    result = tool.run(
        {
            "incident_id": 1,
            "limit": 10,
        }
    )

    assert result.status == "SUCCESS"
    assert result.tool_name == "search_incident_events"

    assert result.data["incident_id"] == 1
    assert result.data["event_count"] == 1

    event = result.data["events"][0]

    assert event["event_id"] == 10
    assert event["event_type"] == "ERROR"
    assert event["description"] == "Payment database timeout detected"
    assert event["metadata"]["source"] == "monitoring"