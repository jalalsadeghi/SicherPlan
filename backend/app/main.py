"""Minimal FastAPI application baseline for platform smoke checks."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.config import settings
from app.errors import ApiException, api_exception_handler, unhandled_exception_handler
from app.health import router as health_router
from app.logging_utils import configure_logging
from app.middleware import RequestContextMiddleware
from app.modules.core.admin_router import router as core_admin_router
from app.modules.iam.auth_router import router as auth_router
from app.modules.platform_services.comm_router import router as comm_router
from app.modules.platform_services.docs_router import router as docs_router
from app.modules.platform_services.info_router import router as info_router
from app.modules.platform_services.integration_router import router as integration_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health_router)
    app.include_router(core_admin_router)
    app.include_router(auth_router)
    app.include_router(docs_router)
    app.include_router(comm_router)
    app.include_router(info_router)
    app.include_router(integration_router)

    app.add_exception_handler(ApiException, api_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get("/demo/error")
    async def demo_error() -> None:
        raise ApiException(
            status_code=400,
            code="platform.validation_error",
            message_key="errors.platform.validation",
            details={"field": "demo"},
        )

    @app.on_event("startup")
    async def log_startup() -> None:
        logger.info("backend.startup")

    return app


app = create_app()
