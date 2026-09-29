from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class Permission(Base):
    __tablename__ = "permissions"
    permission_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    permission_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    role_links: Mapped[list["RolePermission"]] = relationship(back_populates="permission")
