"""Database configuration for GEOMATRIX."""
import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

logger = logging.getLogger(__name__)

DEFAULT_SQLITE_PATH = os.path.join(os.path.dirname(__file__), "geomatrix.db")
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL).strip()

if not DATABASE_URL:
    DATABASE_URL = DEFAULT_SQLITE_URL

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
    if (
        os.getenv("APP_ENV", "development").lower() == "production"
        and DATABASE_URL.startswith("sqlite://")
        and os.getenv("ALLOW_PRODUCTION_SQLITE", "false").lower() != "true"
    ):
        raise RuntimeError("Production deployments require a persistent PostgreSQL DATABASE_URL.")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
