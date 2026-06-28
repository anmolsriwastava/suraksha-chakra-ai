"""
Database connection setup.
Provides a session factory and a FastAPI dependency for getting DB sessions.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from backend.core.config import get_settings

settings = get_settings()

# SQLite needs special handling (no pool, check_same_thread=False)
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=(settings.app_env == "development"),
    )
else:
    engine = create_engine(
        settings.database_url,
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
