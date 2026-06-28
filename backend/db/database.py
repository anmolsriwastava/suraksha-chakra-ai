"""
Database connection setup.
Provides a session factory and a FastAPI dependency for getting DB sessions.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    # keep a small pool — this is a prototype, not prod
    pool_size=5,
    max_overflow=10,
    echo=(settings.app_env == "development"),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db_session():
    """
    FastAPI dependency. Yields a DB session and closes it after the request,
    even if the request raises an exception.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
