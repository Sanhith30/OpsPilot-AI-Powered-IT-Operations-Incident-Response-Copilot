from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Deployment(Base):
    __tablename__ = "deployments"

    deployment_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    service_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.services.service_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    environment: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    commit_hash: Mapped[str | None] = mapped_column(
        String(100),
    )

    deployment_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    trigger_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    deployed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "core.users.user_id",
            ondelete="SET NULL",
        ),
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    service: Mapped["Service"] = relationship(
        back_populates="deployments"
    )

    deployed_by_user: Mapped["User | None"] = relationship(
        back_populates="deployments"
    )