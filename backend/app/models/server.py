from datetime import datetime
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class Server(Base):
    __tablename__ = "servers"
    server_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hostname: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    ip_address = mapped_column(INET, nullable=False)
    environment: Mapped[str] = mapped_column(String(50), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    instance_type: Mapped[str | None] = mapped_column(String(100))
    os_version: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    instances: Mapped[list["ServiceInstance"]] = relationship(back_populates="server")
