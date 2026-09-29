from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class ServiceInstance(Base):
    __tablename__ = "service_instances"
    service_instance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("core.services.service_id", ondelete="CASCADE"), nullable=False)
    server_id: Mapped[int] = mapped_column(ForeignKey("core.servers.server_id", ondelete="CASCADE"), nullable=False)
    instance_name: Mapped[str] = mapped_column(String(150), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    service: Mapped["Service"] = relationship(back_populates="instances")
    server: Mapped["Server"] = relationship(back_populates="instances")
