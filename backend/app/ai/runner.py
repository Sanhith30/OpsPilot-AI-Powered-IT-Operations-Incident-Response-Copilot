from typing import Any

from app.ai.state.factory import create_initial_investigation_state
from app.ai.state.investigation_state import InvestigationState
from app.ai.tools.registry import ToolRegistry


class InvestigationRunner:
    """
    Deterministic investigation runner.

    This is the first orchestration layer for OpsPilot.
    It executes investigation steps using the ToolRegistry
    and updates the InvestigationState.

    LangGraph will eventually replace/extend this orchestration.
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.tool_registry = tool_registry

    def run(
        self,
        *,
        incident_id: int,
        user_question: str,
        investigation_type: str = "ASSISTED",
        investigation_id: int | None = None,
    ) -> InvestigationState:
        """
        Start an investigation and execute the first step:
        retrieve the incident.
        """

        state = create_initial_investigation_state(
            incident_id=incident_id,
            user_question=user_question,
            investigation_type=investigation_type,
            investigation_id=investigation_id,
        )

        state["status"] = "RUNNING"
        state["current_stage"] = "loading_incident"

        result = self.tool_registry.execute(
            "get_incident",
            {
                "incident_id": incident_id,
            },
        )

        state["tool_results"].append(
            result.model_dump(mode="json")
        )

        if result.status != "SUCCESS":
            state["status"] = "FAILED"
            state["current_stage"] = "incident_load_failed"

            state["errors"].append(
                {
                    "stage": "loading_incident",
                    "tool_name": result.tool_name,
                    "error_code": result.error_code,
                    "error_message": result.error_message,
                }
            )

            return state

        state["current_stage"] = "incident_loaded"

        return state