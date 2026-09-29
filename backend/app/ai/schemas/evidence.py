from datetime import datetime

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    source_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    timestamp: datetime | None = None

    title: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )

    content: str = Field(
        ...,
        min_length=1,
    )

    metadata: dict = Field(
        default_factory=dict,
    )
