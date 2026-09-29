from sqlalchemy import select
from app.models.tool_call import ToolCall
class ToolCallRepository:
    def __init__(self, db): self.db=db
    def get_by_id(self,tool_call_id): return self.db.scalars(select(ToolCall).where(ToolCall.tool_call_id==tool_call_id)).one_or_none()
    def get_for_update(self,tool_call_id): return self.db.scalars(select(ToolCall).where(ToolCall.tool_call_id==tool_call_id).with_for_update()).one_or_none()
    def get_by_investigation(self,investigation_id): return list(self.db.scalars(select(ToolCall).where(ToolCall.investigation_id==investigation_id).order_by(ToolCall.tool_call_id)).all())
    def add(self,tool_call): self.db.add(tool_call); return tool_call
