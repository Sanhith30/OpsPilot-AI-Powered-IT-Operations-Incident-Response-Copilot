from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_ticket_service,
    require_permission,
)
from app.schemas.ticket import TicketCreate, TicketResponse

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


@router.get(
    "",
    response_model=list[TicketResponse],
)
def get_tickets(
    current_user=Depends(require_permission("TICKET_VIEW")),
    service=Depends(get_ticket_service),
):
    return service.get_all_tickets()


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def get_ticket(
    ticket_id: int,
    current_user=Depends(require_permission("TICKET_VIEW")),
    service=Depends(get_ticket_service),
):
    return service.get_ticket_by_id(ticket_id)


@router.get(
    "/incident/{incident_id}",
    response_model=list[TicketResponse],
)
def get_incident_tickets(
    incident_id: int,
    current_user=Depends(require_permission("TICKET_VIEW")),
    service=Depends(get_ticket_service),
):
    return service.get_tickets_by_incident(incident_id)


@router.post(
    "",
    response_model=TicketResponse,
)
def create_ticket(
    request: TicketCreate,
    current_user=Depends(require_permission("TICKET_CREATE")),
    service=Depends(get_ticket_service),
):
    return service.create_ticket(
        ticket_number=request.ticket_number,
        title=request.title,
        priority=request.priority,
        incident_id=request.incident_id,
        assigned_team_id=request.assigned_team_id,
        assigned_user_id=request.assigned_user_id,
        description=request.description,
        comment_text=request.comment_text,
        actor_user_id=current_user.user_id,
    )