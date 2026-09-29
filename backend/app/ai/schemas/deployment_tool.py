from datetime import datetime

from pydantic import BaseModel, Field


class GetRecentDeploymentsInput(BaseModel):
    service_id: int = Field(
        ...,
        gt=0,
        description="Numeric ID of the affected service.",
    )

    before_time: datetime = Field(
        ...,
        description=(
            "Only deployments that started at or before "
            "this timestamp are returned."
        ),
    )

    environment: str = Field(
        default="production",
        min_length=1,
        max_length=30,
        description="Deployment environment to search.",
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of deployments to return.",
    )