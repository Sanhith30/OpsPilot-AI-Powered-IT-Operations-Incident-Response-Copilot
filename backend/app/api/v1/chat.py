from __future__ import annotations
from typing import List

from fastapi import APIRouter, Depends

from app.api.dependencies import get_chat_service
from app.core.security import get_current_user
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionRead,
    ChatSessionSummary,
)
from app.services.chat_service import ChatService

router = APIRouter(
    prefix="/chat",
    tags=["Chat & Conversational Copilot"],
)


@router.post("", response_model=ChatResponse)
def send_chat_message(
    request: ChatRequest,
    current_user=Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """
    Primary Conversational Copilot Interaction:
    Accepts natural-language queries, dynamically selects tools,
    gathers grounded operational evidence, and returns an evidence-based answer.
    """
    return service.send_message(user_id=current_user.user_id, request=request)


@router.get("/sessions", response_model=List[ChatSessionSummary])
def list_chat_sessions(
    limit: int = 50,
    current_user=Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> List[ChatSessionSummary]:
    """
    List all chat sessions belonging to the authenticated user.
    """
    return service.list_sessions(user_id=current_user.user_id, limit=limit)


@router.get("/sessions/{session_id}", response_model=ChatSessionRead)
def get_chat_session(
    session_id: str,
    current_user=Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatSessionRead:
    """
    Retrieve full multi-turn message history for a specific chat session.
    """
    return service.get_session_details(session_id=session_id, user_id=current_user.user_id)
