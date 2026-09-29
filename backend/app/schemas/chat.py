from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User question or follow-up prompt")
    session_id: Optional[str] = Field(None, description="Existing session ID, or null to auto-generate")
    incident_id: Optional[int] = Field(None, description="Optional incident ID context for the chat")


class ChatCitation(BaseModel):
    document_id: str
    title: str
    similarity: float
    snippet: str


class ChatToolExecution(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result_summary: str
    status: str = "SUCCESS"


class ChatMessageRead(BaseModel):
    message_id: int
    session_id: str
    role: str
    content: str
    tool_trace: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    risk: Optional[Dict[str, Any]] = None
    investigation_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionSummary(BaseModel):
    session_id: str
    user_id: int
    incident_id: Optional[int] = None
    title: str
    message_count: int = 0
    last_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionRead(BaseModel):
    session_id: str
    user_id: int
    incident_id: Optional[int] = None
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    investigation_id: Optional[int] = None
    risk: Optional[Dict[str, Any]] = None
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    tool_trace: List[Dict[str, Any]] = Field(default_factory=list)
