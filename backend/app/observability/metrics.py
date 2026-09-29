from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "opspilot_http_requests_total",
    "Total HTTP requests handled by OpsPilot",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "opspilot_http_request_duration_seconds",
    "HTTP request processing duration",
    ["method", "path"],
)

INVESTIGATIONS_TOTAL = Counter(
    "opspilot_investigations_total",
    "Total investigations processed",
    ["status"],
)

AI_TOOL_CALLS_TOTAL = Counter(
    "opspilot_ai_tool_calls_total",
    "Total AI tool executions",
    ["tool_name", "status"],
)

LLM_REQUESTS_TOTAL = Counter(
    "opspilot_llm_requests_total",
    "Total LLM requests",
    ["provider", "model", "status"],
)

LLM_REQUEST_DURATION_SECONDS = Histogram(
    "opspilot_llm_request_duration_seconds",
    "LLM request duration",
    ["provider", "model"],
)

RISK_PREDICTIONS_TOTAL = Counter(
    "opspilot_risk_predictions_total",
    "Total risk predictions generated",
    ["risk_level", "model_name"],
)

RAG_RETRIEVALS_TOTAL = Counter(
    "opspilot_rag_retrievals_total",
    "Total number of RAG retrieval operations",
    ["status"],
)

RAG_RETRIEVAL_RESULTS_TOTAL = Counter(
    "opspilot_rag_retrieval_results_total",
    "Total number of chunks returned by RAG retrieval",
)

RAG_CITATION_VALIDATIONS_TOTAL = Counter(
    "opspilot_rag_citation_validations_total",
    "Total RAG citation validations",
    ["status"],
)

RAG_INVALID_CITATIONS_TOTAL = Counter(
    "opspilot_rag_invalid_citations_total",
    "Total invalid RAG citations",
)

INCIDENT_INTELLIGENCE_TOTAL = Counter(
    "opspilot_incident_intelligence_total",
    "Total incident intelligence operations",
    ["status"],
)

INCIDENT_INTELLIGENCE_DURATION_SECONDS = Histogram(
    "opspilot_incident_intelligence_duration_seconds",
    "Duration of incident intelligence operations in seconds",
)

ROOT_CAUSE_CANDIDATES_TOTAL = Counter(
    "opspilot_root_cause_candidates_total",
    "Total root cause candidates generated",
    ["cause"],
)

INTELLIGENCE_DECISIONS_TOTAL = Counter(
    "opspilot_intelligence_decisions_total",
    "Total operational decisions generated",
    ["decision"],
)

INTELLIGENCE_SAFETY_REJECTIONS_TOTAL = Counter(
    "opspilot_intelligence_safety_rejections_total",
    "Total intelligence safety gate rejections",
    ["reason"],
)

REMEDIATIONS_TOTAL = Counter(
    "opspilot_remediations_total",
    "Total remediation requests created",
    ["action_type", "status"],
)

REMEDIATION_DURATION_SECONDS = Histogram(
    "opspilot_remediation_duration_seconds",
    "Remediation execution duration in seconds",
    ["action_type", "status"],
)

REMEDIATION_APPROVALS_TOTAL = Counter(
    "opspilot_remediation_approvals_total",
    "Total remediation approval reviews",
    ["decision"],
)

REMEDIATION_EXECUTIONS_TOTAL = Counter(
    "opspilot_remediation_executions_total",
    "Total remediation action executions",
    ["action_type", "result"],
)


