"""Minimal FastAPI application baseline for platform smoke checks."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errors import ApiException, api_exception_handler, unhandled_exception_handler
from app.health import router as health_router
from app.logging_utils import configure_logging
from app.middleware import RequestContextMiddleware
from app.modules.assistant.router import router as assistant_router
from app.modules.core.admin_router import router as core_admin_router
from app.modules.customers.router import router as customers_router
from app.modules.customers.portal_access_router import router as customer_portal_access_router
from app.modules.customers.portal_router import router as customer_portal_router
from app.modules.employees.router import router as employees_router
from app.modules.employees.self_service_router import router as employee_self_service_router
from app.modules.finance.router import router as finance_router
from app.modules.finance.billing_router import router as finance_billing_router
from app.modules.finance.payroll_router import router as finance_payroll_router
from app.modules.finance.subcontractor_check_router import router as finance_subcontractor_check_router
from app.modules.field_execution.attendance_router import router as field_execution_attendance_router
from app.modules.field_execution.patrol_router import router as field_execution_patrol_router
from app.modules.field_execution.router import router as field_execution_router
from app.modules.field_execution.time_capture_router import router as field_execution_time_capture_router
from app.modules.iam.admin_router import router as iam_admin_router
from app.modules.iam.auth_router import router as auth_router
from app.modules.platform_services.comm_router import router as comm_router
from app.modules.platform_services.docs_router import router as docs_router
from app.modules.platform_services.info_router import router as info_router
from app.modules.platform_services.integration_router import router as integration_router
from app.modules.planning.router import router as planning_router
from app.modules.reporting.router import router as reporting_router
from app.modules.recruiting.router import router as recruiting_router
from app.modules.recruiting.public_router import router as recruiting_public_router
from app.modules.subcontractors.router import router as subcontractors_router
from app.modules.subcontractors.portal_router import router as subcontractor_portal_router
from app.modules.subcontractors.read_model_router import router as subcontractor_read_model_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(_app: FastAPI):
    logger.info(
        "backend.startup",
        extra={
            "env": settings.env,
            "database_host": settings.db_host,
            "database_name": settings.db_name,
            "env_files_loaded": list(settings.loaded_env_files),
        },
    )
    yield


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=app_lifespan,
    )
    if settings.allowed_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.allowed_origins_list),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health_router)
    app.include_router(assistant_router)
    app.include_router(core_admin_router)
    app.include_router(customers_router)
    app.include_router(customer_portal_access_router)
    app.include_router(customer_portal_router)
    app.include_router(employees_router)
    app.include_router(employee_self_service_router)
    app.include_router(finance_router)
    app.include_router(finance_billing_router)
    app.include_router(finance_payroll_router)
    app.include_router(finance_subcontractor_check_router)
    app.include_router(field_execution_attendance_router)
    app.include_router(field_execution_router)
    app.include_router(field_execution_patrol_router)
    app.include_router(field_execution_time_capture_router)
    app.include_router(iam_admin_router)
    app.include_router(auth_router)
    app.include_router(docs_router)
    app.include_router(comm_router)
    app.include_router(info_router)
    app.include_router(integration_router)
    app.include_router(planning_router)
    app.include_router(reporting_router)
    app.include_router(recruiting_router)
    app.include_router(recruiting_public_router)
    app.include_router(subcontractors_router)
    app.include_router(subcontractor_portal_router)
    app.include_router(subcontractor_read_model_router)

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

    return app


app = create_app()
