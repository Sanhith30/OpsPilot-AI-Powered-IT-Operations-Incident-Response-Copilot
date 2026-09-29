from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, Field

from app.ai.tools.base import BaseTool
from app.repositories.ticket_repository import TicketRepository


class QueryTicketsInput(BaseModel):
    """Input schema for the query_tickets tool."""

    incident_id: Optional[int] = Field(
        None,
        description="Filter tickets belonging to a specific incident ID.",
    )
    status: Optional[str] = Field(
        None,
        description="Filter by ticket status: OPEN, IN_PROGRESS, RESOLVED, CLOSED.",
    )
    priority: Optional[str] = Field(
        None,
        description="Filter by ticket priority: LOW, MEDIUM, HIGH, CRITICAL.",
    )
    ticket_number: Optional[str] = Field(
        None,
        description="Lookup a specific ticket by its human-readable number (e.g. 'TKT-001').",
    )
    limit: int = Field(
        20,
        ge=1,
        le=100,
        description="Maximum number of tickets to return.",
    )


class QueryTicketsTool(BaseTool):
    """
    Queries the ticketing system for operational tickets.

    Use this tool to look up tickets associated with an incident, check the
    status of remediation tasks, find open work items, or retrieve a specific
    ticket by number. Returns ticket details including assignees and priority.
    """

    name: ClassVar[str] = "query_tickets"
    description: ClassVar[str] = (
        "Query the operations ticketing system. Filter by incident ID, status "
        "(OPEN/IN_PROGRESS/RESOLVED/CLOSED), priority (LOW/MEDIUM/HIGH/CRITICAL), "
        "or look up a specific ticket by ticket number. "
        "Returns title, status, priority, assignee, and description."
    )
    args_schema: ClassVar[type[BaseModel]] = QueryTicketsInput

    def __init__(self, *, ticket_repository: TicketRepository) -> None:
        self._repo = ticket_repository

    def execute(self, validated_input: QueryTicketsInput) -> Dict[str, Any]:
        # Specific ticket lookup by number
        if validated_input.ticket_number:
            ticket = self._repo.get_by_number(validated_input.ticket_number)
            if ticket:
                return {
                    "total": 1,
                    "tickets": [self._serialize(ticket)],
                }
            return {"total": 0, "tickets": [], "message": f"Ticket {validated_input.ticket_number} not found."}

        # Incident-scoped query
        if validated_input.incident_id:
            tickets = self._repo.get_by_incident(validated_input.incident_id)
            if validated_input.status:
                tickets = [t for t in tickets if t.status == validated_input.status.upper()]
            if validated_input.priority:
                tickets = [t for t in tickets if t.priority == validated_input.priority.upper()]
            tickets = tickets[: validated_input.limit]
            return {
                "total": len(tickets),
                "tickets": [self._serialize(t) for t in tickets],
            }

        # Status-based global query
        if validated_input.status:
            tickets = self._repo.get_by_status(validated_input.status.upper())
            if validated_input.priority:
                tickets = [t for t in tickets if t.priority == validated_input.priority.upper()]
            tickets = tickets[: validated_input.limit]
            return {
                "total": len(tickets),
                "tickets": [self._serialize(t) for t in tickets],
            }

        # Default: return all (up to limit)
        tickets = self._repo.get_all()[: validated_input.limit]
        return {
            "total": len(tickets),
            "tickets": [self._serialize(t) for t in tickets],
        }

    @staticmethod
    def _serialize(ticket) -> Dict[str, Any]:
        return {
            "ticket_id": ticket.ticket_id,
            "ticket_number": ticket.ticket_number,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority,
            "incident_id": ticket.incident_id,
            "assigned_team_id": ticket.assigned_team_id,
            "assigned_user_id": ticket.assigned_user_id,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        }
