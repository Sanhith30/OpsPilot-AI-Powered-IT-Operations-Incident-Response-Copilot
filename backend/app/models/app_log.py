from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AppLog(Base):
    """
    Structured application log entry from an instrumented service.
    Supports full-text search via GIN index created in the migration.
    """

    __tablename__ = "app_logs"
    __table_args__ = (
        Index("idx_app_logs_service_level", "service_id", "level", "logged_at"),
        {"schema": "core"},
    )

    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    service_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("core.services.service_id", ondelete="SET NULL"), nullable=True
    )
    service_name: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    logger_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    span_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    environment: Mapped[str] = mapped_column(String(50), default="Production")
    extra: Mapped[dict] = mapped_column(JSONB, default=dict)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    service: Mapped["Service | None"] = relationship("Service", lazy="select", foreign_keys=[service_id])  # noqa: F821
