from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("core.roles.role_id"),
        primary_key=True,
    )

    permission_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("core.permissions.permission_id"),
        primary_key=True,
    )

    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="permission_links",
    )

    permission: Mapped["Permission"] = relationship(
        "Permission",
        back_populates="role_links",
    )