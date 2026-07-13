"""Shared SQLAlchemy engine/session for Web and Bot services."""

from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger(__name__)

_ENV_FILE = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(os.path.abspath(_ENV_FILE))

DEFAULT_SQLITE_URL = "sqlite:///./qadam.db"
_PLACEHOLDER_URLS = {"", "...", "changeme", "null", "none", "your-database-url"}


def is_production() -> bool:
    if os.getenv("RAILWAY_ENVIRONMENT"):
        return True
    env = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or "").strip().lower()
    return env in {"production", "prod"}


def normalize_database_url(url: str) -> str:
    """
    Railway often provides postgres:// or postgresql://.
    Sync SQLAlchemy + psycopg3 needs postgresql+psycopg://.
    """
    raw = url.strip()
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]
    if raw.startswith("postgresql://") and "+psycopg" not in raw.split("://", 1)[0]:
        raw = "postgresql+psycopg://" + raw[len("postgresql://") :]
    return raw


def resolve_database_url() -> str:
    raw = (os.getenv("DATABASE_URL") or "").strip()
    if raw.lower() in _PLACEHOLDER_URLS:
        raw = ""
    if raw:
        return normalize_database_url(raw)
    if is_production():
        raise RuntimeError(
            "DATABASE_URL is required in production "
            "(Railway PostgreSQL). SQLite is not shared across Web/Bot services."
        )
    return DEFAULT_SQLITE_URL


def database_log_info(url: str) -> dict[str, str]:
    """Safe connection summary for logs (no password)."""
    if url.startswith("sqlite"):
        # sqlite:///./qadam.db or sqlite:////abs/path
        path = url.split("sqlite:///", 1)[-1] if "sqlite:///" in url else url
        return {
            "backend": "sqlite",
            "host": "local-file",
            "database": path or "qadam.db",
        }

    parsed = urlparse(url)
    backend = parsed.scheme.split("+", 1)[0]  # postgresql
    host = parsed.hostname or "unknown"
    if parsed.port:
        host = f"{host}:{parsed.port}"
    db_name = (parsed.path or "/").lstrip("/") or "unknown"
    return {"backend": backend, "host": host, "database": db_name}


def create_db_engine(url: str | None = None) -> Engine:
    database_url = url or resolve_database_url()
    info = database_log_info(database_url)
    logger.info(
        "Database configured: backend=%s host=%s database=%s",
        info["backend"],
        info["host"],
        info["database"],
    )

    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(engine, "connect")
        def _sqlite_on_connect(dbapi_connection, _connection_record) -> None:  # noqa: ANN001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


SQLALCHEMY_DATABASE_URL = resolve_database_url()
engine = create_db_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema() -> None:
    """Create missing tables then run idempotent column/index migrations."""
    from app.services.migrate import migrate_db

    Base.metadata.create_all(bind=engine)
    migrate_db()
