from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class FailureType(str, Enum):
    MISSING_VECTOR = "MISSING_VECTOR"
    BELOW_THRESHOLD = "BELOW_THRESHOLD"
    OUTRANKED_BY_COMPETITORS = "OUTRANKED_BY_COMPETITORS"
    AUTHORIZATION_BLOCKED = "AUTHORIZATION_BLOCKED"
    RERANKER_DEMOTION = "RERANKER_DEMOTION"
    QUERY_AMBIGUITY = "QUERY_AMBIGUITY"
    NONE = "NONE"


class RetrievedCandidate(BaseModel):
    rank: int
    source_name: str
    title: str | None = None
    vector_score: float
    lexical_score: float | None = None
    title_score: float | None = None
    final_score: float


class DocumentCompetition(BaseModel):
    expected_document: str
    expected_document_score: float | None = None
    expected_document_rank: int | None = None
    top_competitor_document: str | None = None
    top_competitor_score: float | None = None
    margin: float | None = None  # top_competitor_score - expected_score


class RerankerShift(BaseModel):
    case_id: str
    document: str
    vector_rank: int | None = None
    hybrid_rank: int | None = None
    rank_change: int | None = None  # positive means moved up, negative means moved down
    vector_score: float
    lexical_score: float
    title_score: float
    final_rerank_score: float
    effect: str  # "IMPROVED", "UNCHANGED", "DEMOTED"


class RetrievalFailureRecord(BaseModel):
    case_id: str
    query: str
    category: str
    expected_document: str
    retrieved_documents: list[str] = Field(default_factory=list)
    retrieved_scores: list[float] = Field(default_factory=list)
    expected_document_rank: int | None = None
    highest_score: float | None = None
    access_result: str = "ALLOWED"
    failure_type: FailureType = FailureType.NONE
    competition: DocumentCompetition | None = None
    root_cause_diagnosis: str | None = None


class PrecisionAnalysis(BaseModel):
    total_positive_cases: int
    top_k: int
    mean_chunks_retrieved_per_case: float
    mean_unique_docs_per_case: float
    mean_target_chunks_in_top_k: float
    theoretical_max_precision: float
    actual_precision_at_k: float
    precision_explanation: str


class AnswerFailureTrace(BaseModel):
    case_id: str
    question: str
    expected_citations: list[str] = Field(default_factory=list)
    retrieved_citations: list[str] = Field(default_factory=list)
    llm_cited: list[str] = Field(default_factory=list)
    citation_valid: bool
    grounded: bool
    failure_origin: str  # "RETRIEVAL_MISS", "LLM_SELECTION", "HALLUCINATION", "NONE"
    diagnostic_trace: str


class RetrievalFailureReport(BaseModel):
    dataset_version: str = "2.0"
    total_cases_evaluated: int = 0
    total_positive_cases: int = 0
    total_failed_positive_cases: int = 0
    threshold: float = 0.65
    candidate_k: int = 15
    final_k: int = 5
    failures: list[RetrievalFailureRecord] = Field(default_factory=list)
    borderline_competition_cases: list[DocumentCompetition] = Field(default_factory=list)
    reranker_shifts: list[RerankerShift] = Field(default_factory=list)
    precision_analysis: PrecisionAnalysis | None = None
    answer_failures: list[AnswerFailureTrace] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)

