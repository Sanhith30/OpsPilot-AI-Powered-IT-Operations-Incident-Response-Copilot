import pytest

from app.ai.state.factory import create_initial_investigation_state


def test_create_initial_investigation_state():
    state = create_initial_investigation_state(
        incident_id=1,
        user_question="Why is Payment API failing?",
    )

    assert state["incident_id"] == 1
    assert state["user_question"] == "Why is Payment API failing?"
    assert state["investigation_type"] == "ASSISTED"
    assert state["status"] == "INITIALIZED"
    assert state["current_stage"] == "initialization"

    assert state["tool_results"] == []
    assert state["evidence"] == []
    assert state["findings"] == []
    assert state["errors"] == []

    assert state["risk_prediction"] is None
    assert state["final_summary"] is None


def test_state_lists_are_independent():
    state_one = create_initial_investigation_state(
        incident_id=1,
        user_question="Question one",
    )

    state_two = create_initial_investigation_state(
        incident_id=2,
        user_question="Question two",
    )

    state_one["tool_results"].append(
        {
            "tool_name": "get_incident",
        }
    )

    assert len(state_one["tool_results"]) == 1
    assert len(state_two["tool_results"]) == 0


def test_invalid_incident_id():
    with pytest.raises(ValueError):
        create_initial_investigation_state(
            incident_id=0,
            user_question="Why is the service failing?",
        )


def test_empty_question():
    with pytest.raises(ValueError):
        create_initial_investigation_state(
            incident_id=1,
            user_question="   ",
        )