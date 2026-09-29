from datetime import datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel,ConfigDict
class InvestigationCreate(BaseModel):
    model_config=ConfigDict(extra="forbid")
    incident_id:int
    investigation_type:str="ASSISTED"
    question:str
class InvestigationStepResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    step_id:int; investigation_id:int; step_number:int; step_type:str; title:str; description:str|None; status:str; started_at:datetime|None; completed_at:datetime|None
class ToolCallResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    tool_call_id:int; investigation_id:int; step_id:int|None; tool_name:str; tool_type:str; status:str; input_payload:dict[str,Any]|None; output_payload:dict[str,Any]|None; error_message:str|None; started_at:datetime|None; completed_at:datetime|None
class InvestigationEvidenceResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    evidence_id:int; investigation_id:int; tool_call_id:int|None; evidence_type:str; source:str; source_reference:str|None; content:str; evidence_metadata:dict[str,Any]|None; collected_at:datetime|None
class FindingEvidenceLinkResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    finding_id:int; evidence_id:int; relationship_type:str; citation_id:str|None=None
class InvestigationFindingResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    finding_id:int; investigation_id:int; finding_type:str; finding_text:str; evidence_links:list[FindingEvidenceLinkResponse]=[]; evidence_refs:list[dict[str,Any]]=[]
class KnowledgeEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    evidence_id: int
    citation_id: str | None = None
    chunk_id: str
    document_id: str
    source_name: str
    source_type: str
    version_number: int
    score: float
    title: str
    content: str
class RiskPredictionResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    prediction_id:int; incident_id:int; investigation_id:int|None; model_name:str; model_version:str; risk_score:Decimal; risk_level:str; prediction_metadata:dict[str,Any]|None; predicted_at:datetime
class InvestigationFeedbackResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    feedback_id:int; investigation_id:int; user_id:int; rating:int; feedback_text:str|None; created_at:datetime
class InvestigationResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    investigation_id:int; incident_id:int; started_by:int|None; investigation_type:str; question:str; status:str; started_at:datetime; completed_at:datetime|None
class InvestigationDetailResponse(InvestigationResponse):
    steps:list[InvestigationStepResponse]=[]
    tool_calls:list[ToolCallResponse]=[]
    evidence:list[InvestigationEvidenceResponse]=[]
    findings:list[InvestigationFindingResponse]=[]
    risk_predictions:list[RiskPredictionResponse]=[]
    feedback:list[InvestigationFeedbackResponse]=[]
    knowledge_evidence:list[KnowledgeEvidenceResponse]=[]


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: int
    actor_user_id: int | None = None
    actor_type: str
    action: str
    resource_type: str | None = None
    resource_id: str | None = None

    incident_id: int | None = None
    investigation_id: int | None = None
    ticket_id: int | None = None

    action_result: str
    request_id: str | None = None
    ip_address: Any | None = None
    user_agent: str | None = None
    details: dict[str, Any] | None = None

    created_at: datetime
