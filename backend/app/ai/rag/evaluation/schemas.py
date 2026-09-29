from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    case_id: str
    query: str
    category: str
    expected_documents: list[str] = Field(default_factory=list)
    expected_keywords: list[str] = Field(default_factory=list)
    user_id: int = 1
    team_id: int | None = None
    expected_access: str = "ALLOWED"  # "ALLOWED" or "DENIED"
    notes: str | None = None

from app.ai.rag.evaluation.document_metrics import (
    ChunkRetrievalMetrics,
    DocumentRetrievalMetrics,
)


class EvalCaseResult(BaseModel):
    case_id: str
    query: str
    category: str
    expected_documents: list[str]
    retrieved_documents: list[str]
    retrieved_scores: list[float] = Field(default_factory=list)
    recall_at_k: float | None = None
    precision_at_k: float | None = None
    reciprocal_rank: float | None = None
    # Chunk-level explicit metrics
    retrieved_chunks: list[str] = Field(default_factory=list)
    chunk_recall_at_k: float | None = None
    chunk_precision_at_k: float | None = None
    chunk_reciprocal_rank: float | None = None
    # Document-level explicit metrics
    document_recall_at_k: float | None = None
    document_precision_at_k: float | None = None
    document_reciprocal_rank: float | None = None
    # Document-ranking diagnostics
    expected_document_rank: int | None = None
    best_chunk_rank: int | None = None
    unique_document_count: int | None = None
    target_document_present: bool | None = None
    unwanted_retrieval: bool | None = None
    expected_access: str
    access_passed: bool | None = None
    keywords_found: list[str] = Field(default_factory=list)


class PositiveRetrievalMetrics(BaseModel):
    count: int
    recall_at_k: float
    precision_at_k: float
    mrr: float


class NegativeControlMetrics(BaseModel):
    count: int
    unwanted_retrieval_rate: float
    clean_rejection_rate: float


class AuthorizationMetrics(BaseModel):
    count: int
    authorization_accuracy: float
    unauthorized_leakage_rate: float


class GroundingMetrics(BaseModel):
    citation_grounding_rate: float


class CategoryMetric(BaseModel):
    case_count: int
    recall_at_k: float | None = None
    precision_at_k: float | None = None
    mrr: float | None = None
    document_recall_at_k: float | None = None
    document_precision_at_k: float | None = None
    document_mrr: float | None = None
    chunk_recall_at_k: float | None = None
    chunk_precision_at_k: float | None = None
    chunk_mrr: float | None = None
    unwanted_retrieval_rate: float | None = None
    clean_rejection_rate: float | None = None
    authorization_accuracy: float | None = None
    unauthorized_leakage_rate: float | None = None


class EvaluationReport(BaseModel):
    evaluation_timestamp: str
    dataset_version: str
    total_cases: int
    top_k: int
    retrieval_threshold: float
    embedding_model: str
    embedding_dimensions: int
    positive_cases: PositiveRetrievalMetrics
    chunk_metrics: ChunkRetrievalMetrics | None = None
    document_metrics: DocumentRetrievalMetrics | None = None
    negative_controls: NegativeControlMetrics
    authorization_cases: AuthorizationMetrics
    grounding: GroundingMetrics
    category_metrics: dict[str, CategoryMetric]
    case_results: list[EvalCaseResult]

