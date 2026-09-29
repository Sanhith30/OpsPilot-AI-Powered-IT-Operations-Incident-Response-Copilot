from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: int
    incident_number: str
    service_id: int
    title: str
    description: str | None
    severity: str
    status: str
    started_at: datetime
    detected_at: datetime | None
    resolved_at: datetime | None
    assigned_team_id: int | None
    assigned_user_id: int | None
    impact_summary: str | None
    root_cause: str | None