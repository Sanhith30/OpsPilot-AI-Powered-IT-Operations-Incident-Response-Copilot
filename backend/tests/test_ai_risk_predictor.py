from app.ai.risk.factory import create_risk_predictor
from app.ai.risk.heuristic import HeuristicRiskPredictor


def test_high_risk_incident_produces_high_risk():
    predictor = HeuristicRiskPredictor()

    incident = {
        "severity": "HIGH",
        "status": "INVESTIGATING",
    }

    evidence = [
        {
            "source_type": "incident_event",
            "source_id": "1",
            "title": "Error rate",
            "content": "Payment API error rate reached 14.2%",
            "metadata": {
                "error_rate": 14.2,
                "event_type": "METRIC_ALERT",
            },
        },
        {
            "source_type": "incident_event",
            "source_id": "2",
            "title": "Database timeout",
            "content": "DATABASE_CONNECTION_TIMEOUT",
            "metadata": {
                "event_type": "DATABASE_TIMEOUT",
            },
        },
        {
            "source_type": "incident_event",
            "source_id": "3",
            "title": "Database timeout",
            "content": "DATABASE_CONNECTION_TIMEOUT",
            "metadata": {
                "event_type": "DATABASE_TIMEOUT",
            },
        },
        {
            "source_type": "incident_event",
            "source_id": "4",
            "title": "Database timeout",
            "content": "DATABASE_CONNECTION_TIMEOUT",
            "metadata": {
                "event_type": "DATABASE_TIMEOUT",
            },
        },
        {
            "source_type": "deployment",
            "source_id": "2",
            "title": "Deployment 2.8.1",
            "content": "Payment API 2.8.1 deployed to production.",
            "metadata": {
                "version": "2.8.1",
            },
        },
    ]

    result = predictor.predict(
        incident=incident,
        evidence=evidence,
    )

    assert result.risk_level == "HIGH"
    assert result.risk_score >= 0.70
    assert result.model_name == "incident_risk_baseline"
    assert result.model_version == "1.0.0"


def test_low_risk_incident_produces_low_risk():
    predictor = create_risk_predictor("heuristic")

    incident = {
        "severity": "LOW",
        "status": "RESOLVED",
    }
    evidence = []

    result = predictor.predict(
        incident=incident,
        evidence=evidence,
    )

    assert result.risk_level == "LOW"
    assert result.risk_score <= 0.30
    assert result.model_name == "incident_risk_baseline"
