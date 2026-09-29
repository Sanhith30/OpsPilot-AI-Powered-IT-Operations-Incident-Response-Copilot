from datetime import datetime,timezone
from app.core.exceptions import NotFoundError,ValidationError
from app.models.tool_call import ToolCall
class ToolCallService:
    FINAL_STATUSES={"SUCCESS","FAILED","TIMEOUT"}
    def __init__(self,db,repository,investigation_repository,investigation_step_repository): self.db=db; self.repository=repository; self.investigation_repository=investigation_repository; self.investigation_step_repository=investigation_step_repository
    def get_by_id(self,tool_call_id):
        x=self.repository.get_by_id(tool_call_id)
        if x is None: raise NotFoundError("Tool call not found.")
        return x
    def get_by_investigation(self,investigation_id):
        if self.investigation_repository.get_by_id(investigation_id) is None: raise NotFoundError("Investigation not found.")
        return self.repository.get_by_investigation(investigation_id)
    def start_tool_call(self,*,investigation_id,tool_name,tool_type,input_payload=None,step_id=None):
        try:
            if self.investigation_repository.get_by_id(investigation_id) is None: raise NotFoundError("Investigation not found.")
            if step_id is not None:
                s=self.investigation_step_repository.get_by_id(step_id)
                if s is None: raise NotFoundError("Investigation step not found.")
                if s.investigation_id!=investigation_id: raise ValidationError("Investigation step does not belong to this investigation.")
            if not tool_name.strip(): raise ValidationError("Tool name cannot be empty.")
            x=ToolCall(investigation_id=investigation_id,step_id=step_id,tool_name=tool_name.strip(),tool_type=tool_type,status="RUNNING",input_payload=input_payload,started_at=datetime.now(timezone.utc)); self.repository.add(x); self.db.flush(); self.db.commit(); return x
        except Exception:
            self.db.rollback(); raise
    def complete_tool_call(self,*,tool_call_id,status,output_payload=None,error_message=None):
        try:
            if status not in self.FINAL_STATUSES: raise ValidationError(f"Invalid final tool call status: {status}")
            x=self.repository.get_for_update(tool_call_id)
            if x is None: raise NotFoundError("Tool call not found.")
            if x.status!="RUNNING": raise ValidationError("Only a RUNNING tool call can be completed.")
            if status in {"FAILED","TIMEOUT"} and not error_message: raise ValidationError("error_message is required for FAILED or TIMEOUT tool calls.")
            if status=="SUCCESS" and error_message: raise ValidationError("error_message must be empty for successful tool calls.")
            x.status=status; x.output_payload=output_payload; x.error_message=error_message; x.completed_at=datetime.now(timezone.utc); self.db.commit(); return x
        except Exception:
            self.db.rollback(); raise
    def mark_success(self,tool_call_id,output_payload=None): return self.complete_tool_call(tool_call_id=tool_call_id,status="SUCCESS",output_payload=output_payload)
    def mark_failed(self,tool_call_id,error_message): return self.complete_tool_call(tool_call_id=tool_call_id,status="FAILED",error_message=error_message)
    def mark_timeout(self,tool_call_id,error_message): return self.complete_tool_call(tool_call_id=tool_call_id,status="TIMEOUT",error_message=error_message)
