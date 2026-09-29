from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_incident_event_repository,
    get_incident_service,
    get_investigation_service,
    require_permission,
)
from app.schemas.incident import IncidentResponse
from app.schemas.investigation import InvestigationResponse

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


@router.get(
    "",
    response_model=list[IncidentResponse],
)
def get_incidents(
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_incident_service),
):
    return service.get_all_incidents()


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
def get_incident(
    incident_id: int,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_incident_service),
):
    return service.get_incident_by_id(incident_id)


@router.get(
    "/{incident_id}/investigations",
    response_model=list[InvestigationResponse],
)
def get_incident_investigations(
    incident_id: int,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_investigation_service),
):
    return service.get_investigations_by_incident(incident_id)


@router.get("/{incident_id}/events")
def get_incident_events(
    incident_id: int,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    event_repo=Depends(get_incident_event_repository),
):
    events = event_repo.get_by_incident(incident_id=incident_id)
    return [
        {
            "incident_event_id": e.incident_event_id,
            "incident_id": e.incident_id,
            "event_type": e.event_type,
            "description": e.description,
            "event_time": e.event_time.isoformat() if e.event_time else None,
            "created_by": e.created_by,
            "event_metadata": e.event_metadata,
        }
        for e in events
    ]