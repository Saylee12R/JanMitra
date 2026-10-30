"""
JanMitra Backend – Database connection and session management

Supports both PostgreSQL (production/Docker) and SQLite (local development).
Set DATABASE_URL in .env:
  - PostgreSQL: postgresql://user:pass@host:port/db
  - SQLite:     sqlite:///./janmitra.db
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import get_settings

settings = get_settings()

db_url = settings.database_url

# Fallback to SQLite if PostgreSQL is not available
if not db_url or db_url.startswith("postgresql"):
    try:
        import psycopg2
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    except (ImportError, Exception):
        # Fallback to SQLite for local dev without PostgreSQL
        db_url = "sqlite:///./janmitra.db"
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
        )
        # Enable JSON support for SQLite
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.close()
else:
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
