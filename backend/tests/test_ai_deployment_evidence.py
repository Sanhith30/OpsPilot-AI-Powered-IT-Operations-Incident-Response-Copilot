from datetime import datetime, timezone

from app.ai.state.evidence import add_evidence


def test_deployment_is_normalized_as_deployment_evidence():
    evidence = add_evidence(
        [],
        source_type="deployment",
        source_id="2",
        timestamp=datetime(
            2026,
            9,
            26,
            9,
            0,
            tzinfo=timezone.utc,
        ),
        title="Deployment 2.8.1 to production",
        content=(
            "Deployment ID 2 deployed version 2.8.1 "
            "to production with status SUCCESS."
        ),
        metadata={
            "deployment_id": 2,
            "version": "2.8.1",
            "environment": "production",
        },
    )

    assert len(evidence) == 1
    assert evidence[0]["source_type"] == "deployment"
    assert evidence[0]["source_id"] == "2"
    assert evidence[0]["metadata"]["version"] == "2.8.1"
