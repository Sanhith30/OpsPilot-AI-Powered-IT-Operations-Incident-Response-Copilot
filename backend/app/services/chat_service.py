from __future__ import annotations

import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.ai.graph.chat_graph import ConversationalChatGraph
from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import (
    ChatMessageRead,
    ChatRequest,
    ChatResponse,
    ChatSessionRead,
    ChatSessionSummary,
)
from app.services.audit_log_service import AuditLogService

logger = logging.getLogger("opspilot.services.chat_service")


class ChatService:
    def __init__(
        self,
        db: Session,
        chat_repository: ChatRepository,
        chat_graph: ConversationalChatGraph,
        audit_log_service: Optional[AuditLogService] = None,
    ):
        self.db = db
        self.chat_repository = chat_repository
        self.chat_graph = chat_graph
        self.audit_log_service = audit_log_service

    def send_message(self, user_id: int, request: ChatRequest) -> ChatResponse:
        # 1. Get or create session
        session = None
        if request.session_id:
            session = self.chat_repository.get_session(request.session_id)
            if session and session.user_id != user_id:
                raise ForbiddenError("Cannot access another user's chat session.")

        if not session:
            session = self.chat_repository.create_session(
                user_id=user_id,
                session_id=request.session_id,
                incident_id=request.incident_id,
                title="New Conversation",
            )
        elif request.incident_id and not session.incident_id:
            self.chat_repository.update_session(
                session_id=session.session_id,
                incident_id=request.incident_id,
            )

        # 2. Persist user message
        self.chat_repository.add_message(
            session_id=session.session_id,
            role="user",
            content=request.message,
        )

        # 3. Fetch recent history for multi-turn context
        past_msgs = self.chat_repository.get_messages(session.session_id, limit=20)
        formatted_history = [
            {"role": m.role, "content": m.content}
            for m in past_msgs[:-1]  # Exclude current question just added
        ]

        # 4. Execute conversational graph
        result = self.chat_graph.run(
            session_id=session.session_id,
            user_id=user_id,
            query=request.message,
            incident_id=session.incident_id or request.incident_id,
            messages=formatted_history,
        )

        # 5. Persist assistant message
        self.chat_repository.add_message(
            session_id=session.session_id,
            role="assistant",
            content=result.get("answer", ""),
            tool_trace=result.get("tool_trace", []),
            citations=result.get("citations", []),
            risk=result.get("risk"),
            investigation_id=result.get("investigation_id"),
        )

        # 6. Optional audit log entry
        if self.audit_log_service:
            try:
                self.audit_log_service.add_to_transaction(
                    user_id=user_id,
                    action="CHAT_QUERY",
                    resource_type="CHAT_SESSION",
                    resource_id=session.session_id,
                    incident_id=session.incident_id,
                    details={
                        "query": request.message[:100],
                        "incident_id": session.incident_id,
                        "tools_called": [t.get("tool_name") for t in result.get("tool_trace", [])],
                    },
                )
                self.db.commit()
            except Exception as e:
                logger.warning("Failed to record chat audit log: %s", e)

        return ChatResponse(
            session_id=session.session_id,
            answer=result.get("answer", ""),
            investigation_id=result.get("investigation_id"),
            risk=result.get("risk"),
            citations=result.get("citations", []),
            tool_trace=result.get("tool_trace", []),
        )

    def list_sessions(self, user_id: int, limit: int = 50) -> List[ChatSessionSummary]:
        sessions = self.chat_repository.list_sessions_for_user(user_id=user_id, limit=limit)
        summaries = []
        for s in sessions:
            msgs = self.chat_repository.get_messages(s.session_id)
            last_msg = msgs[-1].content[:80] if msgs else None
            summaries.append(
                ChatSessionSummary(
                    session_id=s.session_id,
                    user_id=s.user_id,
                    incident_id=s.incident_id,
                    title=s.title,
                    message_count=len(msgs),
                    last_message=last_msg,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )
        return summaries

    def get_session_details(self, session_id: str, user_id: int) -> ChatSessionRead:
        session = self.chat_repository.get_session(session_id)
        if not session:
            raise NotFoundError(f"Chat session '{session_id}' not found.")
        if session.user_id != user_id:
            raise ForbiddenError("Cannot access another user's chat session.")

        raw_msgs = self.chat_repository.get_messages(session_id)
        msgs = [
            ChatMessageRead(
                message_id=m.message_id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                tool_trace=m.tool_trace or [],
                citations=m.citations or [],
                risk=m.risk,
                investigation_id=m.investigation_id,
                created_at=m.created_at,
            )
            for m in raw_msgs
        ]

        return ChatSessionRead(
            session_id=session.session_id,
            user_id=session.user_id,
            incident_id=session.incident_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=msgs,
        )
