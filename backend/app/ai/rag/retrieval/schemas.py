from typing import Any

from pydantic import BaseModel, Field


class RetrievalFilters(BaseModel):
    source_type: str | None = None
    source_name: str | None = None
    document_id: str | None = None
    version_number: int | None = Field(
        default=None,
        ge=1,
    )


class RetrievalQuery(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=4000,
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
    )

    score_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    filters: RetrievalFilters = Field(
        default_factory=RetrievalFilters
    )


class RetrievalResponse(BaseModel):
    query: str

    results: list[Any] = Field(
        default_factory=list
    )

    result_count: int

    applied_filters: RetrievalFilters
