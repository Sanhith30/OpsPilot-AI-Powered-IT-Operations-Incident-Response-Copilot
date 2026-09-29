from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class Role(Base):
    __tablename__ = "roles"
    role_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    users: Mapped[list["User"]] = relationship(back_populates="role")
    permission_links: Mapped[list["RolePermission"]] = relationship(back_populates="role")
