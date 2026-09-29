from __future__ import annotations

from pydantic import BaseModel, Field


class ScoreDistributionSummary(BaseModel):
    min_score: float | None = None
    max_score: float | None = None
    mean_score: float | None = None
    sample_count: int = 0


class ThresholdSweepPoint(BaseModel):
    threshold: float = Field(ge=0.0, le=1.0)

    positive_case_count: int
    positive_recall_at_k: float
    positive_precision_at_k: float
    positive_mrr: float

    negative_case_count: int
    unwanted_retrieval_rate: float
    clean_rejection_rate: float

    authorization_case_count: int
    authorization_accuracy: float
    unauthorized_leakage_rate: float

    grounding_rate: float

    positive_score_distribution: ScoreDistributionSummary = Field(
        default_factory=ScoreDistributionSummary
    )
    negative_score_distribution: ScoreDistributionSummary = Field(
        default_factory=ScoreDistributionSummary
    )
    category_retrieval_counts: dict[str, int] = Field(default_factory=dict)


class ThresholdSweepReport(BaseModel):
    dataset_version: str
    top_k: int
    embedding_model: str
    embedding_dimensions: int

    thresholds: list[ThresholdSweepPoint]

    selected_threshold: float | None = None
    selection_reason: str | None = None
