from typing import Any


def extract_risk_features(
    *,
    incident: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:

    severity = str(
        incident.get("severity", "")
    ).upper()

    status = str(
        incident.get("status", "")
    ).upper()

    event_count = 0
    timeout_count = 0
    error_rate = None

    for item in evidence:

        if item.get("source_type") != "incident_event":
            continue

        metadata = item.get("metadata") or {}

        event_count += 1

        event_type = str(
            metadata.get("event_type", "")
        ).upper()

        content = str(
            item.get("content", "")
        ).upper()

        if (
            "TIMEOUT" in event_type
            or "TIMEOUT" in content
        ):
            timeout_count += 1

        possible_error_rate = metadata.get(
            "error_rate"
        )

        if possible_error_rate is not None:
            try:
                value = float(possible_error_rate)

                if 0 <= value <= 100:
                    error_rate = value

            except (TypeError, ValueError):
                pass

    recent_deployment = any(
        item.get("source_type") == "deployment"
        for item in evidence
    )

    return {
        "severity": severity,
        "status": status,
        "event_count": event_count,
        "timeout_count": timeout_count,
        "error_rate_percent": error_rate,
        "recent_deployment": recent_deployment,
    }
