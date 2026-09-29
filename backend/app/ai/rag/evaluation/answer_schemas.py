from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class RAGAnswerEvalCase(BaseModel):
    case_id: str
    category: str
    question: str
    incident: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    expected_facts: list[str] = Field(default_factory=list)
    expected_citations: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
    user_id: int = 1
    team_id: int | None = 1


class AnswerGroundingTrace(BaseModel):
    case_id: str
    used_citations: list[str] = Field(default_factory=list)
    invalid_citations: list[str] = Field(default_factory=list)
    expected_facts_covered: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    answer_summary: str | None = None
    findings_count: int = 0


class RAGAnswerEvalResult(BaseModel):
    case_id: str
    category: str
    citation_valid: bool
    expected_facts_covered: int
    expected_fact_count: int
    completeness_score: float
    unsupported_claim_count: int
    grounding_score: float
    passed: bool
    trace: AnswerGroundingTrace


class RAGAnswerCategoryMetric(BaseModel):
    case_count: int
    citation_validity_rate: float
    average_completeness: float
    grounding_rate: float
    unsupported_claim_rate: float
    pass_rate: float


class RAGAnswerEvalReport(BaseModel):
    dataset_version: str
    total_cases: int
    pipeline_name: str = "production"
    citation_validity_rate: float
    average_completeness: float
    grounding_rate: float
    unsupported_claim_rate: float
    category_metrics: dict[str, RAGAnswerCategoryMetric] = Field(default_factory=dict)
    results: list[RAGAnswerEvalResult] = Field(default_factory=list)
