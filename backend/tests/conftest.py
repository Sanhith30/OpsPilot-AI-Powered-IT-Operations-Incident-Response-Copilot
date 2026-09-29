import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from app.db.session import SessionLocal,engine,get_db
from app.main import app
@pytest.fixture
def db_session() -> Session:
    connection:Connection=engine.connect(); transaction=connection.begin(); session=SessionLocal(bind=connection,join_transaction_mode="create_savepoint")
    try: yield session
    finally: session.close(); transaction.rollback(); connection.close()
@pytest.fixture
def client(db_session):
    def override_get_db(): yield db_session
    app.dependency_overrides[get_db]=override_get_db
    with TestClient(app) as c: yield c
    app.dependency_overrides.clear()
