from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class Service(Base):
    __tablename__ = "services"
    service_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_name: Mapped[str] = mapped_column(String(150), nullable=False)
    service_key: Mapped[str] = mapped_column("service_code", String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    criticality: Mapped[str] = mapped_column(String(30), nullable=False)
    owner_team_id: Mapped[int | None] = mapped_column(ForeignKey("core.teams.team_id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    owner_team: Mapped["Team | None"] = relationship(back_populates="services")
    instances: Mapped[list["ServiceInstance"]] = relationship(back_populates="service")
    dependencies: Mapped[list["ServiceDependency"]] = relationship(back_populates="source_service", foreign_keys="ServiceDependency.source_service_id")
    dependents: Mapped[list["ServiceDependency"]] = relationship(back_populates="target_service", foreign_keys="ServiceDependency.target_service_id")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="service")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="service")
