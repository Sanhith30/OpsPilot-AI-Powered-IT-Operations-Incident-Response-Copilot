from app.ai.rag.evaluation.metrics import (
    calculate_authorization_accuracy,
    calculate_grounding_rate,
    calculate_mrr,
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_reciprocal_rank,
    calculate_unauthorized_leakage_rate,
    calculate_unwanted_retrieval_rate,
)
from app.ai.rag.evaluation.runner import (
    RAGEvaluationRunner,
    load_eval_cases,
)
from app.ai.rag.evaluation.schemas import (
    AuthorizationMetrics,
    CategoryMetric,
    EvalCase,
    EvalCaseResult,
    EvaluationReport,
    GroundingMetrics,
    NegativeControlMetrics,
    PositiveRetrievalMetrics,
)

from app.ai.rag.evaluation.answer_runner import (
    RAGAnswerEvaluationRunner,
    load_answer_eval_cases,
)
from app.ai.rag.evaluation.answer_schemas import (
    AnswerGroundingTrace,
    RAGAnswerCategoryMetric,
    RAGAnswerEvalCase,
    RAGAnswerEvalReport,
    RAGAnswerEvalResult,
)
from app.ai.rag.evaluation.threshold_runner import RAGThresholdSweepRunner
from app.ai.rag.evaluation.threshold_schemas import (
    ScoreDistributionSummary,
    ThresholdSweepPoint,
    ThresholdSweepReport,
)

from app.ai.rag.evaluation.diagnostics import (
    AnswerFailureTrace,
    DocumentCompetition,
    FailureType,
    PrecisionAnalysis,
    RerankerShift,
    RetrievalFailureRecord,
    RetrievalFailureReport,
)
from app.ai.rag.evaluation.failure_analysis import RAGFailureAnalyzer

from app.ai.rag.evaluation.document_metrics import (
    AggregatedDocument,
    ChunkRetrievalMetrics,
    DocumentRankingDiagnostics,
    DocumentRetrievalMetrics,
    calculate_chunk_precision_at_k,
    calculate_chunk_recall_at_k,
    calculate_chunk_reciprocal_rank,
    calculate_document_mrr,
    calculate_document_precision_at_k,
    calculate_document_recall_at_k,
    calculate_document_reciprocal_rank,
    extract_document_diagnostics,
    unique_documents,
)

__all__ = [
    "EvalCase",
    "EvalCaseResult",
    "CategoryMetric",
    "EvaluationReport",
    "PositiveRetrievalMetrics",
    "NegativeControlMetrics",
    "AuthorizationMetrics",
    "GroundingMetrics",
    "ScoreDistributionSummary",
    "ThresholdSweepPoint",
    "ThresholdSweepReport",
    "RAGAnswerEvalCase",
    "AnswerGroundingTrace",
    "RAGAnswerEvalResult",
    "RAGAnswerCategoryMetric",
    "RAGAnswerEvalReport",
    "RAGEvaluationRunner",
    "RAGThresholdSweepRunner",
    "RAGAnswerEvaluationRunner",
    "load_eval_cases",
    "load_answer_eval_cases",
    "calculate_recall_at_k",
    "calculate_precision_at_k",
    "calculate_reciprocal_rank",
    "calculate_mrr",
    "calculate_unwanted_retrieval_rate",
    "calculate_authorization_accuracy",
    "calculate_unauthorized_leakage_rate",
    "calculate_grounding_rate",
    "FailureType",
    "DocumentCompetition",
    "RerankerShift",
    "RetrievalFailureRecord",
    "PrecisionAnalysis",
    "AnswerFailureTrace",
    "RetrievalFailureReport",
    "RAGFailureAnalyzer",
    "AggregatedDocument",
    "DocumentRankingDiagnostics",
    "DocumentRetrievalMetrics",
    "ChunkRetrievalMetrics",
    "unique_documents",
    "calculate_document_recall_at_k",
    "calculate_document_precision_at_k",
    "calculate_document_reciprocal_rank",
    "calculate_document_mrr",
    "calculate_chunk_recall_at_k",
    "calculate_chunk_precision_at_k",
    "calculate_chunk_reciprocal_rank",
    "extract_document_diagnostics",
]


