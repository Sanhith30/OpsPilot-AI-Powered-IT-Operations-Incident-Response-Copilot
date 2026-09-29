from app.core.security import create_access_token


def auth_headers(user_id: int = 1):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def test_get_investigations_list(client):
    response = client.get(
        "/api/v1/investigations",
        headers=auth_headers(1),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_investigations_unauthorized(client):
    response = client.get("/api/v1/investigations")
    assert response.status_code in {401, 403}


def test_get_investigation_by_incident(client):
    response = client.get(
        "/api/v1/investigations/incident/1",
        headers=auth_headers(1),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_investigation_by_status(client):
    response = client.get(
        "/api/v1/investigations/status/COMPLETED",
        headers=auth_headers(1),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_investigation_details(client):
    response = client.get(
        "/api/v1/investigations/1/details",
        headers=auth_headers(1),
    )
    assert response.status_code == 200
    data = response.json()
    assert "investigation_id" in data
    assert "findings" in data
    assert "evidence" in data
    assert "tool_calls" in data
    assert "risk_predictions" in data


def test_get_investigation_audit(client):
    response = client.get(
        "/api/v1/investigations/1/audit",
        headers=auth_headers(1),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_investigation_audit_unauthorized(client):
    response = client.get("/api/v1/investigations/1/audit")
    assert response.status_code in {401, 403}


def test_get_investigation_audit_missing(client):
    response = client.get(
        "/api/v1/investigations/999999/audit",
        headers=auth_headers(1),
    )
    assert response.status_code == 404
