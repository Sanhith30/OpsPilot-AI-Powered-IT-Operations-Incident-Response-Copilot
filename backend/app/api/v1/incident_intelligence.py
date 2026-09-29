from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Request

from app.ai.intelligence.schemas import IncidentIntelligenceResult
from app.api.dependencies import (
    get_incident_intelligence_service,
    get_investigation_service,
    require_permission,
)
from app.core.exceptions import NotFoundError
from app.services.incident_intelligence_service import IncidentIntelligenceService
from app.services.investigation_service import InvestigationService

router = APIRouter(tags=["Incident Intelligence"])


@router.post(
    "/incidents/{incident_id}/intelligence",
    response_model=IncidentIntelligenceResult,
)
def generate_incident_intelligence(
    incident_id: int,
    investigation_id: int | None = Query(default=None),
    request: Request = None,
    current_user=Depends(require_permission("INCIDENT_ANALYZE")),
    intelligence_service: IncidentIntelligenceService = Depends(
        get_incident_intelligence_service
    ),
    investigation_service: InvestigationService = Depends(
        get_investigation_service
    ),
):
    """
    Generate complete incident intelligence & operational decision
    for an incident's investigation.
    """
    # If investigation_id is not provided, look up the latest investigation for this incident
    if investigation_id is None:
        investigations = investigation_service.get_investigations_by_incident(incident_id)
        if not investigations:
            raise NotFoundError(
                f"No active investigation found for incident {incident_id}. Please create an investigation first."
            )
        investigation_id = investigations[-1].investigation_id

    request_id = getattr(request.state, "request_id", None) if request and hasattr(request, "state") else None

    return intelligence_service.generate(
        incident_id=incident_id,
        investigation_id=investigation_id,
        user_id=current_user.user_id,
        request_id=request_id,
    )


@router.get(
    "/incidents/{incident_id}/intelligence",
    response_model=IncidentIntelligenceResult,
)
def get_incident_intelligence(
    incident_id: int,
    current_user=Depends(require_permission("INCIDENT_READ")),
    intelligence_service: IncidentIntelligenceService = Depends(
        get_incident_intelligence_service
    ),
):
    """
    Retrieve latest persisted incident intelligence result for an incident.
    """
    result = intelligence_service.get_latest_by_incident(incident_id)
    if result is None:
        raise NotFoundError(f"No intelligence result found for incident {incident_id}.")
    return result


@router.get(
    "/investigations/{investigation_id}/intelligence",
    response_model=IncidentIntelligenceResult,
)
def get_investigation_intelligence(
    investigation_id: int,
    current_user=Depends(require_permission("INCIDENT_READ")),
    intelligence_service: IncidentIntelligenceService = Depends(
        get_incident_intelligence_service
    ),
):
    """
    Retrieve latest persisted incident intelligence result for a specific investigation.
    """
    result = intelligence_service.get_latest_by_investigation(investigation_id)
    if result is None:
        raise NotFoundError(f"No intelligence result found for investigation {investigation_id}.")
    return result
