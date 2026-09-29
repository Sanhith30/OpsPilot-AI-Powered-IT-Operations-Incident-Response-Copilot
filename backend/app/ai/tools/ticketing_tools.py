"""
Ticket-mutation tools for OpsPilot.

CreateTicketTool — creates a new OPEN operational ticket, assigns a unique
TICK-XXXXXXXX number, and persists it via session.flush() so the caller can
commit or roll back as part of a larger unit of work.
"""
from __future__ import annotations

import uuid
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.tools.base import BaseTool
from app.models.ticket import Ticket


class CreateTicketInput(BaseModel):
    """Input schema for the create_ticket tool."""

    incident_id: int = Field(
        ...,
        description="Incident ID to associate the new ticket with.",
    )
    title: str = Field(
        ...,
        description="Short, descriptive title for the remediation ticket.",
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of the remediation task or finding.",
    )
    priority: str = Field(
        "MEDIUM",
        description="Ticket priority: LOW, MEDIUM, HIGH, or CRITICAL.",
    )
    created_by_user_id: int = Field(
        ...,
        description="User ID of the operator creating the ticket.",
    )
    assigned_user_id: Optional[int] = Field(
        None,
        description="Optional user ID to pre-assign the ticket to.",
    )
    assigned_team_id: Optional[int] = Field(
        None,
        description="Optional team ID to pre-assign the ticket to.",
    )


class CreateTicketTool(BaseTool):
    """
    Creates a new operational ticket in the ticketing system.

    Use this tool when investigation uncovers a remediation action that must
    be tracked.  The ticket is linked to the incident, receives a unique
    TICK-XXXXXXXX human-readable number, and starts in OPEN status.
    """

    name: ClassVar[str] = "create_ticket"
    description: ClassVar[str] = (
        "Create a new OPEN ticket in the operations ticketing system to track "
        "a remediation action found during investigation. Link it to an incident "
        "and optionally assign it to a user or team. Returns the ticket number "
        "(e.g. TICK-A3F2B9C1) for reference."
    )
    args_schema: ClassVar[type[BaseModel]] = CreateTicketInput

    def __init__(self, *, db: Session) -> None:
        self._db = db

    def execute(self, validated_input: CreateTicketInput) -> Dict[str, Any]:
        ticket_number = f"TICK-{uuid.uuid4().hex[:8].upper()}"

        ticket = Ticket(
            ticket_number=ticket_number,
            incident_id=validated_input.incident_id,
            title=validated_input.title,
            description=validated_input.description,
            priority=validated_input.priority.upper(),
            status="OPEN",
            created_by=validated_input.created_by_user_id,
            assigned_user_id=validated_input.assigned_user_id,
            assigned_team_id=validated_input.assigned_team_id,
        )

        try:
            self._db.add(ticket)
            self._db.flush()  # Push to DB within the current UoW; commit handled by caller.

            return {
                "status": "CREATED",
                "ticket_id": ticket_number,       # Human-readable ID (TICK-XXXXXXXX)
                "ticket_db_id": ticket.ticket_id,  # Integer PK
                "ticket_number": ticket_number,
                "incident_id": validated_input.incident_id,
                "title": validated_input.title,
                "priority": ticket.priority,
                "ticket_status": "OPEN",
                "message": f"Ticket {ticket_number} created successfully.",
            }

        except Exception as exc:  # pragma: no cover
            return {
                "status": "ERROR",
                "error": f"Failed to create ticket: {exc}",
            }
