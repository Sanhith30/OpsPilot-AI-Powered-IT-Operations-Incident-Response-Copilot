from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class Team(Base):
    __tablename__ = "teams"
    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    manager_user_id: Mapped[int | None] = mapped_column(ForeignKey("core.users.user_id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    users: Mapped[list["User"]] = relationship(back_populates="team", foreign_keys="User.team_id")
    manager: Mapped["User | None"] = relationship(back_populates="managed_team", foreign_keys=[manager_user_id], uselist=False)
    services: Mapped[list["Service"]] = relationship(back_populates="owner_team")
    assigned_tickets: Mapped[list["Ticket"]] = relationship(back_populates="assigned_team")
