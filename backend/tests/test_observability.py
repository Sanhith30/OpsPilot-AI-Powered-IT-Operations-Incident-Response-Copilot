from app.ai.risk.heuristic import HeuristicRiskPredictor
from app.ai.tools.base import BaseTool
from app.observability.metrics import (
    AI_TOOL_CALLS_TOTAL,
    RISK_PREDICTIONS_TOTAL,
)
from pydantic import BaseModel


class DummyInput(BaseModel):
    query: str


class DummyTool(BaseTool):
    name = "dummy_test_tool"
    description = "Dummy tool for metric verification"
    args_schema = DummyInput

    def execute(self, validated_input: DummyInput) -> dict:
        return {"result": f"processed {validated_input.query}"}


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "opspilot_http_requests_total" in response.text
    assert "opspilot_ai_tool_calls_total" in response.text


def test_request_id_header_present(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


def test_tool_execution_increments_metric():
    tool = DummyTool()
    initial = AI_TOOL_CALLS_TOTAL.labels(
        tool_name="dummy_test_tool",
        status="SUCCESS",
    )._value.get()

    result = tool.run({"query": "hello"})
    assert result.status == "SUCCESS"

    after = AI_TOOL_CALLS_TOTAL.labels(
        tool_name="dummy_test_tool",
        status="SUCCESS",
    )._value.get()

    assert after == initial + 1


def test_risk_predictor_increments_metric():
    predictor = HeuristicRiskPredictor()
    incident = {
        "incident_id": 1,
        "severity": "CRITICAL",
        "status": "OPEN",
    }
    evidence = []

    initial = RISK_PREDICTIONS_TOTAL.labels(
        risk_level="HIGH",
        model_name="incident_risk_baseline",
    )._value.get()

    pred = predictor.predict(incident=incident, evidence=evidence)
    assert pred.risk_level in {"HIGH", "MEDIUM", "LOW"}

    after = RISK_PREDICTIONS_TOTAL.labels(
        risk_level=pred.risk_level,
        model_name=pred.model_name,
    )._value.get()

    assert after >= initial + 1
