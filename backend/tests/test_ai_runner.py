from app.ai.runner import InvestigationRunner


class FakeToolResult:
    tool_name = "get_incident"
    status = "SUCCESS"
    error_code = None
    error_message = None

    def model_dump(self, mode="python"):
        return {
            "tool_name": self.tool_name,
            "status": self.status,
            "data": {
                "incident_number": "INC-1042",
                "title": "Payment API elevated error rate",
            },
            "error_code": self.error_code,
            "error_message": self.error_message,
            "metadata": {},
            "execution_time_ms": 5,
        }


class FakeRegistry:
    def execute(self, tool_name, raw_input):
        assert tool_name == "get_incident"
        assert raw_input == {
            "incident_id": 1,
        }

        return FakeToolResult()


def test_investigation_runner_loads_incident():
    runner = InvestigationRunner(
        tool_registry=FakeRegistry()
    )

    state = runner.run(
        incident_id=1,
        user_question="Why is Payment API failing?",
    )

    assert state["incident_id"] == 1
    assert state["user_question"] == "Why is Payment API failing?"
    assert state["status"] == "RUNNING"
    assert state["current_stage"] == "incident_loaded"

    assert len(state["tool_results"]) == 1

    result = state["tool_results"][0]

    assert result["tool_name"] == "get_incident"
    assert result["status"] == "SUCCESS"
    assert result["data"]["incident_number"] == "INC-1042"


class FailingToolResult:
    tool_name = "get_incident"
    status = "FAILED"
    error_code = "TOOL_EXECUTION_ERROR"
    error_message = "Unable to retrieve incident."

    def model_dump(self, mode="python"):
        return {
            "tool_name": self.tool_name,
            "status": self.status,
            "data": {},
            "error_code": self.error_code,
            "error_message": self.error_message,
            "metadata": {},
            "execution_time_ms": 5,
        }


class FailingRegistry:
    def execute(self, tool_name, raw_input):
        return FailingToolResult()


def test_investigation_runner_handles_tool_failure():
    runner = InvestigationRunner(
        tool_registry=FailingRegistry()
    )

    state = runner.run(
        incident_id=1,
        user_question="Why is Payment API failing?",
    )

    assert state["status"] == "FAILED"
    assert state["current_stage"] == "incident_load_failed"

    assert len(state["tool_results"]) == 1
    assert len(state["errors"]) == 1

    assert state["errors"][0]["stage"] == "loading_incident"
    assert (
        state["errors"][0]["error_code"]
        == "TOOL_EXECUTION_ERROR"
    )