from __future__ import annotations

from app.ai.schemas.investigation_analysis import InvestigationAnalysis


def parse_investigation_analysis(
    raw_response: str,
) -> InvestigationAnalysis:
    text = raw_response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return InvestigationAnalysis.model_validate_json(text)

