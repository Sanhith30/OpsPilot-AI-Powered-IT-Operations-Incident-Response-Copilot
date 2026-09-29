from __future__ import annotations
import pytest
from fastapi.testclient import TestClient

from app.ai.providers.mock import MockLLMProvider
from app.api.dependencies import get_llm_provider
from app.core.security import create_access_token
from app.main import app


@pytest.fixture(autouse=True)
def mock_llm_dependency():
    app.dependency_overrides[get_llm_provider] = lambda: MockLLMProvider()
    yield
    app.dependency_overrides.pop(get_llm_provider, None)


def _auth_headers(user_id: int = 1) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}" }


def test_chat_unauthenticated_rejected(client: TestClient):
    """Unauthenticated requests to /api/v1/chat must be rejected with 401."""
    resp = client.post("/api/v1/chat", json={"message": "Why is the API down?"})
    assert resp.status_code == 401


def test_chat_send_message_and_follow_up(client: TestClient):
    """Test full conversational journey: initial question, tool dispatch, followed by multi-turn follow-up."""
    # 1. Ask initial question about Incident #1
    req1 = {
        "message": "Why is the payment API failing? Please investigate incident #1.",
        "incident_id": 1,
    }
    resp1 = client.post("/api/v1/chat", json=req1, headers=_auth_headers(user_id=1))
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert "session_id" in data1
    session_id = data1["session_id"]
    assert len(data1["answer"]) > 20
    assert len(data1["tool_trace"]) >= 1

    # 2. Ask follow-up in the same session
    req2 = {
        "session_id": session_id,
        "message": "Did the latest deployment cause it?",
    }
    resp2 = client.post("/api/v1/chat", json=req2, headers=_auth_headers(user_id=1))
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["session_id"] == session_id
    assert "deployment" in data2["answer"].lower()

    # 3. Retrieve session details
    resp_details = client.get(f"/api/v1/chat/sessions/{session_id}", headers=_auth_headers(user_id=1))
    assert resp_details.status_code == 200
    details = resp_details.json()
    assert details["session_id"] == session_id
    assert len(details["messages"]) == 4  # user1, assistant1, user2, assistant2
    assert details["messages"][0]["role"] == "user"
    assert details["messages"][1]["role"] == "assistant"
    assert details["messages"][2]["role"] == "user"
    assert details["messages"][3]["role"] == "assistant"


def test_list_chat_sessions(client: TestClient):
    """Test user can list their own chat sessions with summaries."""
    # Create a session
    client.post(
        "/api/v1/chat",
        json={"message": "Checking system error rates."},
        headers=_auth_headers(user_id=1),
    )

    resp = client.get("/api/v1/chat/sessions", headers=_auth_headers(user_id=1))
    assert resp.status_code == 200
    sessions = resp.json()
    assert isinstance(sessions, list)
    assert len(sessions) >= 1
    assert "session_id" in sessions[0]
    assert "title" in sessions[0]
    assert "message_count" in sessions[0]


def test_cross_user_session_isolation(client: TestClient):
    """User 2 must NOT be able to view or post into User 1's chat session."""
    # User 1 creates session
    resp1 = client.post(
        "/api/v1/chat",
        json={"message": "User 1 private query."},
        headers=_auth_headers(user_id=1),
    )
    session_id = resp1.json()["session_id"]

    # User 2 attempts to read User 1's session -> 403 Forbidden
    resp2 = client.get(f"/api/v1/chat/sessions/{session_id}", headers=_auth_headers(user_id=2))
    assert resp2.status_code == 403

    # User 2 attempts to post into User 1's session -> 403 Forbidden
    resp3 = client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "User 2 intruding."},
        headers=_auth_headers(user_id=2),
    )
    assert resp3.status_code == 403
