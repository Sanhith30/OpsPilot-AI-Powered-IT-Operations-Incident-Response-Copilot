from pydantic import BaseModel, Field


class GetIncidentInput(BaseModel):
    incident_id: int = Field(
        ...,
        gt=0,
        description="Numeric ID of the incident to retrieve.",
    )