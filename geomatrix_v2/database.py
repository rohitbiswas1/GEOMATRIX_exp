"""Database configuration for GEOMATRIX.

Production should use a managed PostgreSQL DATABASE_URL. For Vercel preview/demo
execution, a short-lived SQLite database under /tmp keeps the API bootable when
no database has been configured yet; it is intentionally non-persistent.
"""
import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

logger = logging.getLogger(__name__)

DEFAULT_SQLITE_PATH = os.path.join("/tmp", "geomatrix.db") if os.getenv("VERCEL") else os.path.join(os.path.dirname(__file__), "geomatrix.db")
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip() or DEFAULT_SQLITE_URL

def _build_engine(url: str):
    normalized = "postgresql://" + url[len("postgres://"):] if url.startswith("postgres://") else url
    kwargs = {"echo": False, "pool_pre_ping": True}
    if normalized.startswith("sqlite://"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "5")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
        )
    return create_engine(normalized, **kwargs)

engine = _build_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    if DATABASE_URL.startswith("sqlite:///") and os.getenv("VERCEL"):
        logger.warning("No DATABASE_URL configured on Vercel; using ephemeral /tmp SQLite. Configure PostgreSQL for persistent data.")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
