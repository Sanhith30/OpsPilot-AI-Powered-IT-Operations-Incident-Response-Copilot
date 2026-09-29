from app.core.security import create_access_token
def headers(user_id): return {"Authorization":f"Bearer {create_access_token(user_id)}"}
def test_root(client):
    r=client.get("/"); assert r.status_code==200; assert r.json()["message"]=="OpsPilot API is running"
def test_health(client): assert client.get("/health").json()=={"status":"healthy"}
def test_db_health(client): assert client.get("/db-health").json()["result"]==1
def test_incidents_require_auth(client): assert client.get("/api/v1/incidents").status_code in {401,403}
