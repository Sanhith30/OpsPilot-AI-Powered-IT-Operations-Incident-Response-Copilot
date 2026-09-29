from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.ai.schemas.evidence import EvidenceItem
from app.ai.state.evidence import add_evidence


def test_evidence_item():
    item = EvidenceItem(
        source_type="incident_event",
        source_id="10",
        timestamp=datetime(
            2026,
            9,
            26,
            9,
            10,
            tzinfo=timezone.utc,
        ),
        title="ERROR",
        content="Payment database timeout detected",
        metadata={"source": "monitoring"},
    )

    assert item.source_type == "incident_event"
    assert item.source_id == "10"
    assert item.title == "ERROR"
    assert item.metadata["source"] == "monitoring"


def test_add_evidence():
    result = add_evidence(
        [],
        source_type="deployment",
        source_id=3,
        timestamp=None,
        title="Version 2.8.1 deployment",
        content="Production deployment completed successfully",
    )

    assert len(result) == 1
    assert result[0]["source_type"] == "deployment"
    assert result[0]["source_id"] == "3"


def test_evidence_requires_content():
    with pytest.raises(ValidationError):
        EvidenceItem(
            source_type="incident_event",
            source_id="10",
            title="ERROR",
            content="",
        )
