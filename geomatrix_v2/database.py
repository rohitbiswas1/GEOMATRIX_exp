"""Database configuration for GEOMATRIX."""
import logging
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

logger = logging.getLogger(__name__)

IS_VERCEL = os.getenv("VERCEL", "").lower() == "1"
DEFAULT_SQLITE_PATH = os.getenv(
    "GEOMATRIX_SQLITE_PATH",
    str(Path("/tmp") / "geomatrix.db") if IS_VERCEL else str(Path(__file__).with_name("geomatrix.db")),
)
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
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialised using %s", "PostgreSQL" if DATABASE_URL.startswith("postgres") else "SQLite")
    except Exception:
        logger.exception("Database initialisation failed; API will boot but readiness will report not_ready.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
