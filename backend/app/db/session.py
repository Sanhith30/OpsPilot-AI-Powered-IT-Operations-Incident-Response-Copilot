from collections.abc import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings


def _get_safe_database_url() -> str | URL:
    # If explicit credentials are provided, URL.create handles special characters (e.g. '@') safely
    if settings.db_host and settings.db_user and settings.db_password:
        return URL.create(
            drivername="postgresql+psycopg",
            username=settings.db_user,
            password=settings.db_password,
            host=settings.db_host,
            port=settings.db_port or 5432,
            database=settings.db_name,
        )

    raw_url = settings.database_url or ""
    if not raw_url:
        return raw_url

    try:
        parsed = make_url(raw_url)
        # If host contains '@', password had an unescaped '@' (e.g. '30@postgres')
        if parsed.host and "@" in parsed.host:
            pass_extra, real_host = parsed.host.split("@", 1)
            full_pass = f"{parsed.password or ''}@{pass_extra}"
            return URL.create(
                drivername=parsed.drivername,
                username=parsed.username,
                password=full_pass,
                host=real_host,
                port=parsed.port,
                database=parsed.database,
            )
        return raw_url
    except Exception:
        return raw_url


database_url = _get_safe_database_url()
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
