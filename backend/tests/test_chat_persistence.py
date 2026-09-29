from __future__ import annotations
import pytest
from app.repositories.chat_repository import ChatRepository


def test_chat_session_creation_and_retrieval(db_session):
    repo = ChatRepository(db_session)
    
    session = repo.create_session(user_id=1, incident_id=1, title="Test Investigation")
    assert session.session_id.startswith("chat-")
    assert session.user_id == 1
    assert session.incident_id == 1
    assert session.title == "Test Investigation"

    retrieved = repo.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == session.session_id
    assert retrieved.user_id == 1


def test_chat_message_flow_and_auto_titling(db_session):
    repo = ChatRepository(db_session)
    session = repo.create_session(user_id=2, title="New Conversation")

    # Add user message -> triggers auto-titling from content
    user_msg = repo.add_message(
        session_id=session.session_id,
        role="user",
        content="Why is the payment API failing with 500 errors?",
    )
    assert user_msg.message_id is not None
    assert user_msg.role == "user"

    # Verify session title updated
    refreshed = repo.get_session(session.session_id)
    assert "payment API" in refreshed.title

    # Add assistant response with tool traces and citations
    assistant_msg = repo.add_message(
        session_id=session.session_id,
        role="assistant",
        content="Database connection timeout detected.",
        tool_trace=[{"tool_name": "get_incident", "status": "SUCCESS"}],
        citations=[{"document_id": "doc-runbook-001", "similarity": 0.88}],
        risk={"score": 0.85, "level": "HIGH"},
    )
    assert assistant_msg.message_id is not None
    assert len(assistant_msg.tool_trace) == 1
    assert len(assistant_msg.citations) == 1
    assert assistant_msg.risk["level"] == "HIGH"

    # Verify message list
    messages = repo.get_messages(session.session_id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


def test_list_sessions_for_user(db_session):
    repo = ChatRepository(db_session)
    s1 = repo.create_session(user_id=1, title="Session 1")
    s2 = repo.create_session(user_id=1, title="Session 2")
    s3 = repo.create_session(user_id=2, title="Other User Session")

    user1_sessions = repo.list_sessions_for_user(user_id=1)
    session_ids = [s.session_id for s in user1_sessions]
    assert s1.session_id in session_ids
    assert s2.session_id in session_ids
    assert s3.session_id not in session_ids
