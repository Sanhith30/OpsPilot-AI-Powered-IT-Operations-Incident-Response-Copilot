from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        incident_id: Optional[int] = None,
        title: str = "New Conversation",
    ) -> ChatSession:
        if not session_id:
            session_id = f"chat-{uuid.uuid4().hex[:12]}"
        
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            incident_id=incident_id,
            title=title,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.session_id == session_id)
            .options(selectinload(ChatSession.messages))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_sessions_for_user(self, user_id: int, limit: int = 50) -> List[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
            .options(selectinload(ChatSession.messages))
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        incident_id: Optional[int] = None,
    ) -> Optional[ChatSession]:
        session = self.get_session(session_id)
        if not session:
            return None
        if title is not None:
            session.title = title
        if incident_id is not None:
            session.incident_id = incident_id
        session.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(session)
        return session

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_trace: Optional[List[Dict[str, Any]]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        risk: Optional[Dict[str, Any]] = None,
        investigation_id: Optional[int] = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            tool_trace=tool_trace or [],
            citations=citations or [],
            risk=risk,
            investigation_id=investigation_id,
        )
        self.db.add(msg)
        
        # Touch session updated_at
        session = self.db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        ).scalar_one_or_none()
        if session:
            session.updated_at = datetime.now(timezone.utc)
            # Auto-title session from first user message if still default
            if role == "user" and session.title == "New Conversation":
                clean_title = content.strip().split("\n")[0][:40]
                session.title = clean_title if clean_title else "New Conversation"

        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_messages(self, session_id: str, limit: int = 100) -> List[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.message_id.asc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
