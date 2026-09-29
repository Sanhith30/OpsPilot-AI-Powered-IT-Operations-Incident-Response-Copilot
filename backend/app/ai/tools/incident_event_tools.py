from __future__ import annotations

from app.ai.schemas.incident_event_tool import (
    SearchIncidentEventsInput,
)
from app.ai.tools.base import BaseTool


class SearchIncidentEventsTool(BaseTool):
    name = "search_incident_events"

    description = (
        "Retrieve timeline events associated with a specific incident, "
        "optionally limited to events occurring before a given timestamp."
    )

    args_schema = SearchIncidentEventsInput

    def __init__(self, incident_event_service):
        self.incident_event_service = incident_event_service

    def execute(self, validated_input: SearchIncidentEventsInput):
        events = self.incident_event_service.get_events_by_incident(
            incident_id=validated_input.incident_id,
            before_time=validated_input.before_time,
            limit=validated_input.limit,
        )

        return {
            "incident_id": validated_input.incident_id,
            "event_count": len(events),
            "events": [
                {
                    "event_id": event.incident_event_id,
                    "incident_id": event.incident_id,
                    "event_type": event.event_type,
                    "event_time": (
                        event.event_time.isoformat()
                        if event.event_time is not None
                        else None
                    ),
                    "description": event.description,
                    "created_by": event.created_by,
                    "metadata": event.event_metadata,
                }
                for event in events
            ],
        }