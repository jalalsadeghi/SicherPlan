"""Synchronous SQLAlchemy engine and session helpers."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.errors import ApiException


def _engine_connect_args(database_url: str) -> dict[str, int]:
    if database_url.startswith("postgresql"):
        return {"connect_timeout": settings.db_connect_timeout_seconds}
    return {}


def build_engine(database_url: str | None = None):
    resolved_url = database_url or settings.database_url
    return create_engine(
        resolved_url,
        future=True,
        echo=settings.db_echo,
        pool_pre_ping=True,
        connect_args=_engine_connect_args(resolved_url),
    )


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False, future=True)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    except OperationalError as exc:
        raise ApiException(
            503,
            "platform.database_unavailable",
            "errors.platform.database_unavailable",
        ) from exc
    finally:
        session.close()
