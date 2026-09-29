from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class Ticket(Base):
    __tablename__="tickets"
    ticket_id:Mapped[int]=mapped_column(Integer,primary_key=True)
    ticket_number:Mapped[str]=mapped_column(String(50),unique=True,nullable=False)
    incident_id:Mapped[int]=mapped_column(ForeignKey("core.incidents.incident_id",ondelete="CASCADE"),nullable=False)
    title:Mapped[str]=mapped_column(String(255),nullable=False)
    description:Mapped[str|None]=mapped_column(Text)
    priority:Mapped[str]=mapped_column(String(30),nullable=False)
    status:Mapped[str]=mapped_column(String(30),nullable=False)
    assigned_team_id:Mapped[int|None]=mapped_column(ForeignKey("core.teams.team_id",ondelete="SET NULL"))
    assigned_user_id:Mapped[int|None]=mapped_column(ForeignKey("core.users.user_id",ondelete="SET NULL"))
    created_by:Mapped[int]=mapped_column(ForeignKey("core.users.user_id"),nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    incident:Mapped["Incident"]=relationship(back_populates="tickets")
    assigned_team:Mapped["Team|None"]=relationship(back_populates="assigned_tickets")
    assigned_user:Mapped["User|None"]=relationship(back_populates="assigned_tickets",foreign_keys=[assigned_user_id])
    creator:Mapped["User"]=relationship(back_populates="tickets_created",foreign_keys=[created_by])
    comments:Mapped[list["TicketComment"]]=relationship(back_populates="ticket",cascade="all, delete-orphan")
