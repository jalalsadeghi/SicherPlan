"""HTTP API for integration endpoints, jobs, and outbox processing."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db_session
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.integration_repository import SqlAlchemyIntegrationRepository
from app.modules.platform_services.integration_schemas import (
    ImportExportJobCreate,
    ImportExportJobRead,
    IntegrationEndpointCreate,
    IntegrationEndpointRead,
    OutboxEventRead,
    OutboxProcessRequest,
)
from app.modules.platform_services.integration_security import IntegrationSecretBox
from app.modules.platform_services.integration_service import IntegrationService
from app.modules.platform_services.storage import build_object_storage_adapter


router = APIRouter(prefix="/api/platform/tenants/{tenant_id}/integration", tags=["platform-integration"])


def get_integration_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> IntegrationService:
    document_service = DocumentService(
        SqlAlchemyDocumentRepository(session),
        storage=build_object_storage_adapter(settings),
        bucket_name=settings.object_storage_bucket,
    )
    return IntegrationService(
        SqlAlchemyIntegrationRepository(session),
        document_service=document_service,
        secret_box=IntegrationSecretBox(settings.integration_secret_key),
        retry_delay_seconds=settings.integration_outbox_retry_delay_seconds,
        max_attempts=settings.integration_outbox_max_attempts,
    )


@router.post("/endpoints", response_model=IntegrationEndpointRead, status_code=status.HTTP_201_CREATED)
def create_endpoint(
    tenant_id: UUID,
    payload: IntegrationEndpointCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.integration.write", scope="tenant")),
    ],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> IntegrationEndpointRead:
    return service.register_endpoint(str(tenant_id), payload, context)


@router.get("/endpoints", response_model=list[IntegrationEndpointRead])
def list_endpoints(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.integration.read", scope="tenant")),
    ],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> list[IntegrationEndpointRead]:
    return service.list_endpoints(str(tenant_id), context)


@router.post("/jobs", response_model=ImportExportJobRead, status_code=status.HTTP_201_CREATED)
def request_job(
    tenant_id: UUID,
    payload: ImportExportJobCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.integration.write", scope="tenant")),
    ],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> ImportExportJobRead:
    return service.request_job(str(tenant_id), payload, context)


@router.get("/jobs/{job_id}", response_model=ImportExportJobRead)
def get_job(
    tenant_id: UUID,
    job_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.integration.read", scope="tenant")),
    ],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> ImportExportJobRead:
    return service.get_job(str(tenant_id), str(job_id), context)


@router.post("/outbox/process", response_model=list[OutboxEventRead])
def process_outbox(
    tenant_id: UUID,
    payload: OutboxProcessRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.integration.write", scope="tenant")),
    ],
    service: Annotated[IntegrationService, Depends(get_integration_service)],
) -> list[OutboxEventRead]:
    _ = context
    return service.process_outbox(tenant_id=str(tenant_id), worker_name=payload.worker_name, limit=payload.limit)
