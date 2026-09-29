from app.ai.state.investigation_state import InvestigationState


def create_initial_investigation_state(
    *,
    incident_id: int,
    user_question: str,
    investigation_type: str = "ASSISTED",
    investigation_id: int | None = None,
) -> InvestigationState:
    """
    Create a clean state for a new AI investigation.
    """

    if incident_id <= 0:
        raise ValueError("incident_id must be greater than zero.")

    if not user_question.strip():
        raise ValueError("user_question cannot be empty.")

    if not investigation_type.strip():
        raise ValueError("investigation_type cannot be empty.")

    return {
        "investigation_id": investigation_id,
        "incident_id": incident_id,
        "investigation_type": investigation_type,
        "user_question": user_question.strip(),
        "status": "INITIALIZED",
        "current_stage": "initialization",
        "tool_results": [],
        "evidence": [],
        "findings": [],
        "risk_prediction": None,
        "rag_query": None,
        "rag_context": None,
        "rag_citations": [],
        "rag_grounding_status": "NOT_APPLICABLE",
        "incident_intelligence": None,
        "final_summary": None,
        "errors": [],
    }