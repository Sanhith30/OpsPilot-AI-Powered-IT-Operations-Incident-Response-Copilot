from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Double, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ServiceMetric(Base):
    """
    Time-series operational metric snapshot for a service instance.
    Examples: cpu_usage_percent, error_rate, p99_latency_ms.
    """

    __tablename__ = "service_metrics"
    __table_args__ = (
        Index("idx_svc_metrics_name_time", "service_id", "metric_name", "recorded_at"),
        {"schema": "core"},
    )

    metric_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("core.services.service_id", ondelete="CASCADE"), nullable=False
    )
    service_name: Mapped[str] = mapped_column(String(120), nullable=False)
    instance_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    environment: Mapped[str] = mapped_column(String(50), default="Production")
    metric_name: Mapped[str] = mapped_column(String(120), nullable=False)
    metric_value: Mapped[float] = mapped_column(Double, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    dimensions: Mapped[dict] = mapped_column(JSONB, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    service: Mapped["Service"] = relationship("Service", lazy="select", foreign_keys=[service_id])  # noqa: F821
