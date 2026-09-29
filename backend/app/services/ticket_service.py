from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.ticket import Ticket
from app.models.ticket_comment import TicketComment

VALID_STATUSES = {"OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"}
VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


class TicketService:
    """
    Full ticket lifecycle management.
    Supports create, status transitions, closure, assignment, and commenting.
    """

    def __init__(
        self,
        db,
        ticket_repository,
        incident_repository,
        team_repository,
        user_repository,
        ticket_comment_repository,
        audit_log_service,
    ):
        self.db = db
        self.repository = ticket_repository
        self.incident_repository = incident_repository
        self.team_repository = team_repository
        self.user_repository = user_repository
        self.ticket_comment_repository = ticket_comment_repository
        self.audit_log_service = audit_log_service

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    def get_all_tickets(self) -> list[Ticket]:
        return self.repository.get_all()

    def get_ticket_by_id(self, ticket_id: int) -> Ticket:
        ticket = self.repository.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError("Ticket not found.")
        return ticket

    def get_tickets_by_incident(self, incident_id: int) -> list[Ticket]:
        if self.incident_repository.get_by_id(incident_id) is None:
            raise NotFoundError("Incident not found.")
        return self.repository.get_by_incident(incident_id)

    def get_tickets_by_status(self, status: str) -> list[Ticket]:
        return self.repository.get_by_status(status.upper())

    # ------------------------------------------------------------------ #
    # Create                                                               #
    # ------------------------------------------------------------------ #

    def create_ticket(
        self,
        *,
        ticket_number: str,
        title: str,
        priority: str,
        incident_id: int,
        assigned_team_id: Optional[int],
        assigned_user_id: Optional[int],
        actor_user_id: int,
        description: Optional[str] = None,
        status: str = "OPEN",
        comment_text: Optional[str] = None,
    ) -> Ticket:
        try:
            if self.repository.get_by_number(ticket_number) is not None:
                raise ConflictError("Ticket number already exists.")
            if self.incident_repository.get_by_id(incident_id) is None:
                raise NotFoundError("Incident not found.")
            if assigned_team_id is not None and self.team_repository.get_by_id(assigned_team_id) is None:
                raise NotFoundError("Assigned team not found.")
            if assigned_user_id is not None:
                u = self.user_repository.get_by_id(assigned_user_id)
                if u is None:
                    raise NotFoundError("Assigned user not found.")
                if not u.is_active:
                    raise ValidationError("Assigned user is inactive.")
            actor = self.user_repository.get_by_id(actor_user_id)
            if actor is None:
                raise NotFoundError("Creator user not found.")
            if not actor.is_active:
                raise ValidationError("Creator user is inactive.")

            t = Ticket(
                ticket_number=ticket_number,
                incident_id=incident_id,
                title=title,
                description=description,
                priority=priority.upper(),
                status=status.upper(),
                assigned_team_id=assigned_team_id,
                assigned_user_id=assigned_user_id,
                created_by=actor_user_id,
            )
            self.repository.add(t)
            self.db.flush()

            if comment_text and comment_text.strip():
                self.ticket_comment_repository.add(
                    TicketComment(
                        ticket_id=t.ticket_id,
                        author_id=actor_user_id,
                        comment_text=comment_text.strip(),
                    )
                )

            self.audit_log_service.add_to_transaction(
                action="CREATE_TICKET",
                user_id=actor_user_id,
                resource_type="TICKET",
                resource_id=t.ticket_id,
                details={
                    "ticket_number": t.ticket_number,
                    "incident_id": t.incident_id,
                    "title": t.title,
                },
            )
            self.db.commit()
            return t
        except Exception:
            self.db.rollback()
            raise

    # ------------------------------------------------------------------ #
    # Status Lifecycle                                                     #
    # ------------------------------------------------------------------ #

    def update_status(
        self,
        *,
        ticket_id: int,
        new_status: str,
        actor_user_id: int,
        comment_text: Optional[str] = None,
    ) -> Ticket:
        """Transition a ticket to a new status: OPEN → IN_PROGRESS → RESOLVED → CLOSED."""
        try:
            ticket = self.get_ticket_by_id(ticket_id)
            normalized = new_status.upper()
            if normalized not in VALID_STATUSES:
                raise ValidationError(
                    f"Invalid status '{new_status}'. Must be one of {sorted(VALID_STATUSES)}."
                )
            old_status = ticket.status
            ticket.status = normalized
            ticket.updated_at = datetime.now(timezone.utc)

            if comment_text and comment_text.strip():
                self.ticket_comment_repository.add(
                    TicketComment(
                        ticket_id=ticket.ticket_id,
                        author_id=actor_user_id,
                        comment_text=comment_text.strip(),
                    )
                )

            self.audit_log_service.add_to_transaction(
                action="UPDATE_TICKET_STATUS",
                user_id=actor_user_id,
                resource_type="TICKET",
                resource_id=ticket.ticket_id,
                details={
                    "ticket_number": ticket.ticket_number,
                    "old_status": old_status,
                    "new_status": normalized,
                },
            )
            self.db.commit()
            return ticket
        except Exception:
            self.db.rollback()
            raise

    def close_ticket(
        self,
        *,
        ticket_id: int,
        actor_user_id: int,
        resolution_note: Optional[str] = None,
    ) -> Ticket:
        """Close a ticket with an optional resolution note."""
        return self.update_status(
            ticket_id=ticket_id,
            new_status="CLOSED",
            actor_user_id=actor_user_id,
            comment_text=resolution_note,
        )

    def resolve_ticket(
        self,
        *,
        ticket_id: int,
        actor_user_id: int,
        resolution_note: Optional[str] = None,
    ) -> Ticket:
        """Mark a ticket as RESOLVED pending verification before closure."""
        return self.update_status(
            ticket_id=ticket_id,
            new_status="RESOLVED",
            actor_user_id=actor_user_id,
            comment_text=resolution_note,
        )

    def assign_ticket(
        self,
        *,
        ticket_id: int,
        assigned_user_id: Optional[int],
        assigned_team_id: Optional[int],
        actor_user_id: int,
        comment_text: Optional[str] = None,
    ) -> Ticket:
        """Reassign a ticket to a different user or team."""
        try:
            ticket = self.get_ticket_by_id(ticket_id)

            if assigned_user_id is not None:
                u = self.user_repository.get_by_id(assigned_user_id)
                if u is None:
                    raise NotFoundError("Assigned user not found.")
                if not u.is_active:
                    raise ValidationError("Assigned user is inactive.")

            if assigned_team_id is not None and self.team_repository.get_by_id(assigned_team_id) is None:
                raise NotFoundError("Assigned team not found.")

            ticket.assigned_user_id = assigned_user_id
            ticket.assigned_team_id = assigned_team_id
            ticket.updated_at = datetime.now(timezone.utc)

            if comment_text and comment_text.strip():
                self.ticket_comment_repository.add(
                    TicketComment(
                        ticket_id=ticket.ticket_id,
                        author_id=actor_user_id,
                        comment_text=comment_text.strip(),
                    )
                )

            self.audit_log_service.add_to_transaction(
                action="ASSIGN_TICKET",
                user_id=actor_user_id,
                resource_type="TICKET",
                resource_id=ticket.ticket_id,
                details={
                    "ticket_number": ticket.ticket_number,
                    "assigned_user_id": assigned_user_id,
                    "assigned_team_id": assigned_team_id,
                },
            )
            self.db.commit()
            return ticket
        except Exception:
            self.db.rollback()
            raise

    # ------------------------------------------------------------------ #
    # Comments                                                             #
    # ------------------------------------------------------------------ #

    def add_comment(
        self,
        *,
        ticket_id: int,
        author_id: int,
        comment_text: str,
    ) -> TicketComment:
        """Add a comment to an existing ticket."""
        try:
            ticket = self.get_ticket_by_id(ticket_id)
            if not comment_text or not comment_text.strip():
                raise ValidationError("Comment text cannot be empty.")

            comment = TicketComment(
                ticket_id=ticket.ticket_id,
                author_id=author_id,
                comment_text=comment_text.strip(),
            )
            self.ticket_comment_repository.add(comment)
            ticket.updated_at = datetime.now(timezone.utc)

            self.audit_log_service.add_to_transaction(
                action="ADD_TICKET_COMMENT",
                user_id=author_id,
                resource_type="TICKET",
                resource_id=ticket.ticket_id,
                details={"ticket_number": ticket.ticket_number},
            )
            self.db.commit()
            return comment
        except Exception:
            self.db.rollback()
            raise
