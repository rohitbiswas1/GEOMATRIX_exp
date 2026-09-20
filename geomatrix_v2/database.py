"""Database configuration for Geomatrix v2.

Uses DATABASE_URL when provided (recommended for production), with a local
SQLite fallback for development only.
"""
import os
import logging
from urllib.parse import urlparse, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

logger = logging.getLogger(__name__)

DEFAULT_SQLITE_PATH = os.path.join(os.path.dirname(__file__), "geomatrix.db")
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL).strip()


def _normalize_database_url(url: str) -> str:
    """Normalize common hosted-Postgres URLs for SQLAlchemy/psycopg2/psycopg3."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and urlparse(url).scheme == "postgresql":
        return url
    return url


def _build_engine(url: str):
    url = _normalize_database_url(url)
    kwargs = {"echo": False, "pool_pre_ping": True}
    if url.startswith("sqlite://"):
        kwargs.update({
            "connect_args": {"check_same_thread": False},
        })
    else:
        kwargs.update({
            "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "5")),
        })
    return create_engine(url, **kwargs)


engine = _build_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create missing tables.

    Schema migrations are handled by the application model definitions for new
    deployments. Existing production databases should be migrated separately.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
