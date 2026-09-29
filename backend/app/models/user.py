from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("core.roles.role_id"), nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("core.teams.team_id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    role: Mapped["Role"] = relationship(back_populates="users")
    team: Mapped["Team | None"] = relationship(back_populates="users", foreign_keys=[team_id])
    managed_team: Mapped["Team | None"] = relationship(back_populates="manager", foreign_keys="Team.manager_user_id", uselist=False)
    incident_events_created: Mapped[list["IncidentEvent"]] = relationship(back_populates="created_by_user")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="deployed_by_user")
    assigned_tickets: Mapped[list["Ticket"]] = relationship(back_populates="assigned_user", foreign_keys="Ticket.assigned_user_id")
    tickets_created: Mapped[list["Ticket"]] = relationship(back_populates="creator", foreign_keys="Ticket.created_by")
    investigations_started: Mapped[list["Investigation"]] = relationship(back_populates="starter", foreign_keys="Investigation.started_by")
    ticket_comments: Mapped[list["TicketComment"]] = relationship(back_populates="author")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
    investigation_feedback: Mapped[list["InvestigationFeedback"]] = relationship(back_populates="user")
