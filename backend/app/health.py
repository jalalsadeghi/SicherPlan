"""Health, readiness, and version endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.db.session import build_engine

router = APIRouter(tags=["health"])


def _database_readiness() -> dict[str, Any]:
    try:
        engine = build_engine(settings.database_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
        return {"status": "ok"}
    except SQLAlchemyError as exc:
        return {"status": "error", "reason": exc.__class__.__name__}


def _object_storage_readiness() -> dict[str, Any]:
    if settings.object_storage_endpoint and settings.object_storage_bucket:
        return {"status": "configured"}
    return {"status": "missing_config"}


@router.get("/health/live")
async def live() -> dict[str, Any]:
    return {"status": "live", "service": settings.app_name, "env": settings.env}


@router.get("/health/version")
async def version() -> dict[str, Any]:
    return {"name": settings.app_name, "version": settings.app_version, "env": settings.env}


@router.get("/health/ready")
async def ready() -> JSONResponse:
    checks = {
        "database": _database_readiness(),
        "object_storage": _object_storage_readiness(),
    }
    ready_state = checks["database"]["status"] == "ok"
    payload = {
        "status": "ready" if ready_state else "not_ready",
        "service": settings.app_name,
        "checks": checks,
    }
    status_code = status.HTTP_200_OK if ready_state else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=payload)
