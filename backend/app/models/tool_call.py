from __future__ import annotations
from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class ToolCall(Base):
    __tablename__="tool_calls"
    tool_call_id:Mapped[int]=mapped_column(Integer,primary_key=True)
    investigation_id:Mapped[int]=mapped_column(ForeignKey("core.investigations.investigation_id",ondelete="CASCADE"),nullable=False)
    step_id:Mapped[int|None]=mapped_column(ForeignKey("core.investigation_steps.step_id",ondelete="SET NULL"))
    tool_name:Mapped[str]=mapped_column(String(150),nullable=False)
    tool_type:Mapped[str]=mapped_column(String(50),nullable=False)
    status:Mapped[str]=mapped_column(String(30),nullable=False)
    input_payload:Mapped[dict[str,Any]|None]=mapped_column(JSONB)
    output_payload:Mapped[dict[str,Any]|None]=mapped_column(JSONB)
    error_message:Mapped[str|None]=mapped_column(Text)
    started_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    investigation:Mapped["Investigation"]=relationship(back_populates="tool_calls")
    step:Mapped["InvestigationStep|None"]=relationship(back_populates="tool_calls")
    evidence:Mapped[list["InvestigationEvidence"]]=relationship(back_populates="tool_call")
