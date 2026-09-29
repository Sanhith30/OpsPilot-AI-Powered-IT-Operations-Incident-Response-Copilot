from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class ServiceDependency(Base):
    __tablename__ = "service_dependencies"
    service_dependency_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_service_id: Mapped[int] = mapped_column(ForeignKey("core.services.service_id", ondelete="CASCADE"), nullable=False)
    target_service_id: Mapped[int] = mapped_column(ForeignKey("core.services.service_id", ondelete="CASCADE"), nullable=False)
    dependency_type: Mapped[str] = mapped_column(String(100), nullable=False)
    criticality: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source_service: Mapped["Service"] = relationship(back_populates="dependencies", foreign_keys=[source_service_id])
    target_service: Mapped["Service"] = relationship(back_populates="dependents", foreign_keys=[target_service_id])
