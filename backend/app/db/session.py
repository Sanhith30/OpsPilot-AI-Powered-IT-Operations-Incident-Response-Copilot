from collections.abc import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings

database_url = URL.create(drivername="postgresql+psycopg", username=settings.db_user, password=settings.db_password, host=settings.db_host, port=settings.db_port, database=settings.db_name)
engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        print(f"Database connection failed: {exc}")
        return False
