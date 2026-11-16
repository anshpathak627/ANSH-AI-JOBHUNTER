"""
database/__init__.py
Exports the SQLAlchemy engine, session factory, declarative base, and
the FastAPI dependency `get_db` for use across the application.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config.settings import get_settings
from database.models import Base

# ── Engine ────────────────────────────────────────────────────────────────────
_settings = get_settings()

engine = create_engine(
    _settings.database_url,
    # SQLite-specific: allow the connection to be shared across threads
    # (FastAPI runs handlers in a thread pool).
    connect_args={"check_same_thread": False}
    if _settings.database_url.startswith("sqlite")
    else {},
    echo=False,
)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session and ensure it is closed after each request.

    Usage in a FastAPI route::

        from fastapi import Depends
        from sqlalchemy.orm import Session
        from database import get_db

        @app.get("/jobs")
        def list_jobs(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["engine", "SessionLocal", "Base", "get_db"]
