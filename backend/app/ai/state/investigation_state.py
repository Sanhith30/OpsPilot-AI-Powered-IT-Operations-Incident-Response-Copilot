from operator import add
from typing import Annotated, Any, Literal, TypedDict


InvestigationStatus = Literal[
    "INITIALIZED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
]

RAGGroundingStatus = Literal[
    "NOT_APPLICABLE",
    "VALID",
    "INVALID",
]



class InvestigationState(TypedDict, total=False):
    """
    Working state for a single OpsPilot AI investigation.

    Durable investigation data remains in PostgreSQL.
    This state is used by the AI orchestration layer.
    """

    # --------------------------------------------------------
    # Investigation identity
    # --------------------------------------------------------

    investigation_id: int | None
    incident_id: int

    investigation_type: str
    user_question: str

    # --------------------------------------------------------
    # Execution state
    # --------------------------------------------------------

    status: InvestigationStatus
    current_stage: str

    # --------------------------------------------------------
    # AI tool execution
    # --------------------------------------------------------

    tool_results: Annotated[
        list[dict[str, Any]],
        add,
    ]

    # --------------------------------------------------------
    # Investigation knowledge
    # --------------------------------------------------------

    evidence: Annotated[
        list[dict[str, Any]],
        add,
    ]

    findings: Annotated[
        list[dict[str, Any]],
        add,
    ]

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    risk_prediction: dict[str, Any] | None

    # --------------------------------------------------------
    # RAG knowledge context
    # --------------------------------------------------------

    # Query issued against the vector store.
    rag_query: str | None

    # LLM-ready formatted context string produced by RAGContextBuilder.
    rag_context: str | None

    # Serialised RAGContextItem dicts (KB-1 … KB-N).
    # Stored for later citation persistence (Step 17.10).
    rag_citations: list[dict[str, Any]]

    # Grounding validation status (Step 17.12).
    rag_grounding_status: RAGGroundingStatus | None


    # --------------------------------------------------------
    # Incident Intelligence & Decision Engine (Step 18)
    # --------------------------------------------------------

    incident_intelligence: Any | None

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    final_summary: str | None

    # --------------------------------------------------------
    # Error tracking
    # --------------------------------------------------------

    errors: Annotated[
        list[dict[str, Any]],
        add,
    ]