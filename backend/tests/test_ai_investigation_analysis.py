from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.ai.graph.analysis_parser import (
    parse_investigation_analysis,
)
from app.ai.graph.prompts import (
    build_investigation_prompt,
)


def test_parse_valid_analysis():
    raw_response = """
    {
      "summary": "The incident followed a production deployment.",
      "findings": [
        {
          "finding": "Deployment 3 occurred before the incident event.",
          "confidence": "HIGH",
          "evidence_refs": [
            {
              "source_type": "deployment",
              "source_id": "3"
            },
            {
              "source_type": "incident_event",
              "source_id": "21"
            }
          ]
        }
      ],
      "probable_root_cause": "A deployment-related regression is possible.",
      "recommendations": [
        "Review deployment 3 changes."
      ]
    }
    """

    analysis = parse_investigation_analysis(raw_response)

    assert analysis.summary != ""
    assert len(analysis.findings) == 1

    finding = analysis.findings[0]

    assert finding.confidence == "HIGH"
    assert len(finding.evidence_refs) == 2
    assert finding.evidence_refs[0].source_type == "deployment"


def test_invalid_analysis_is_rejected():
    with pytest.raises(ValidationError):
        parse_investigation_analysis(
            '{"summary": ""}'
        )


def test_parse_markdown_wrapped_analysis():
    raw_response = """```json
    {
      "summary": "Markdown-wrapped investigation summary.",
      "findings": [
        {
          "finding": "Deployment caused latency spike.",
          "confidence": "MEDIUM",
          "evidence_refs": []
        }
      ],
      "probable_root_cause": "Config error",
      "recommendations": ["Rollback"]
    }
    ```"""

    analysis = parse_investigation_analysis(raw_response)

    assert analysis.summary == "Markdown-wrapped investigation summary."
    assert len(analysis.findings) == 1
    assert analysis.findings[0].confidence == "MEDIUM"



def test_build_investigation_prompt():
    incident = {
        "incident_id": 1,
        "incident_number": "INC-1042",
        "title": "Payment API failure",
    }

    evidence = [
        {
            "source_type": "deployment",
            "source_id": "3",
            "timestamp": datetime(
                2026,
                9,
                26,
                9,
                15,
                tzinfo=timezone.utc,
            ),
            "title": "Deployment 3",
            "content": "Production deployment completed.",
            "metadata": {},
        }
    ]

    prompt = build_investigation_prompt(
        incident=incident,
        evidence=evidence,
        user_question="Why did the incident occur?",
    )

    assert "INC-1042" in prompt
    assert "Why did the incident occur?" in prompt
    assert "deployment" in prompt
    assert "Do not invent facts" in prompt
