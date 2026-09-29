from datetime import datetime

from pydantic import BaseModel, Field


class SearchIncidentEventsInput(BaseModel):
    incident_id: int = Field(
        ...,
        gt=0,
        description="Numeric ID of the incident whose events should be retrieved.",
    )

    before_time: datetime | None = Field(
        default=None,
        description="Return only events that occurred at or before this timestamp.",
    )

    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of incident events to retrieve.",
    )