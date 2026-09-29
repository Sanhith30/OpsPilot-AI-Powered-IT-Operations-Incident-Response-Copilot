from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
class TicketRepository:
    def __init__(self, db: Session): self.db=db
    def get_all(self): return list(self.db.scalars(select(Ticket).order_by(Ticket.ticket_id)).all())
    def get_by_id(self, ticket_id): return self.db.scalars(select(Ticket).where(Ticket.ticket_id==ticket_id)).one_or_none()
    def get_by_number(self, ticket_number): return self.db.scalars(select(Ticket).where(Ticket.ticket_number==ticket_number)).one_or_none()
    def get_by_incident(self, incident_id): return list(self.db.scalars(select(Ticket).where(Ticket.incident_id==incident_id).order_by(Ticket.ticket_id)).all())
    def get_by_status(self, status): return list(self.db.scalars(select(Ticket).where(Ticket.status==status).order_by(Ticket.ticket_id)).all())
    def add(self, ticket): self.db.add(ticket); return ticket
