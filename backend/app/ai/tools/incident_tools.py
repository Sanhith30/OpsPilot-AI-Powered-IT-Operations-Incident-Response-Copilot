from typing import Any

from app.ai.tools.base import BaseTool
from app.ai.schemas.incident_tool import GetIncidentInput
from app.services.incident_service import IncidentService


class GetIncidentTool(BaseTool):
    """
    Retrieve a single incident using the existing IncidentService.
    """

    name = "get_incident"

    description = (
        "Retrieve the details of a specific incident using its numeric "
        "incident ID."
    )

    args_schema = GetIncidentInput

    def __init__(self, incident_service: IncidentService):
        self.incident_service = incident_service

    def execute(
        self,
        validated_input: GetIncidentInput,
    ) -> dict[str, Any]:

        incident = self.incident_service.get_incident_by_id(
            validated_input.incident_id
        )

        return {
            "incident_id": incident.incident_id,
            "incident_number": incident.incident_number,
            "service_id": incident.service_id,
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity,
            "status": incident.status,
            "started_at": incident.started_at.isoformat(),
            "detected_at": (
                incident.detected_at.isoformat()
                if incident.detected_at
                else None
            ),
            "resolved_at": (
                incident.resolved_at.isoformat()
                if incident.resolved_at
                else None
            ),
            "assigned_team_id": incident.assigned_team_id,
            "assigned_user_id": incident.assigned_user_id,
            "impact_summary": incident.impact_summary,
            "root_cause": incident.root_cause,
        }