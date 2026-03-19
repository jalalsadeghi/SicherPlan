"""HTTP API for tenant-scoped logical documents and immutable versions."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db_session
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_schemas import (
    DocumentCreate,
    DocumentLinkCreate,
    DocumentLinkRead,
    DocumentRead,
    DocumentVersionCreate,
    DocumentVersionRead,
)
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import build_object_storage_adapter


router = APIRouter(prefix="/api/platform/tenants/{tenant_id}/documents", tags=["platform-docs"])


def get_document_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> DocumentService:
    return DocumentService(
        SqlAlchemyDocumentRepository(session),
        storage=build_object_storage_adapter(settings),
        bucket_name=settings.object_storage_bucket,
    )


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(
    tenant_id: UUID,
    payload: DocumentCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.docs.write", scope="tenant")),
    ],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentRead:
    return service.create_document(str(tenant_id), payload, context)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    tenant_id: UUID,
    document_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.docs.read", scope="tenant")),
    ],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentRead:
    return service.get_document(str(tenant_id), str(document_id), context)


@router.post("/{document_id}/versions", response_model=DocumentVersionRead, status_code=status.HTTP_201_CREATED)
def add_document_version(
    tenant_id: UUID,
    document_id: UUID,
    payload: DocumentVersionCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.docs.write", scope="tenant")),
    ],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentVersionRead:
    return service.add_document_version(str(tenant_id), str(document_id), payload, context)


@router.get("/{document_id}/versions/{version_no}", response_model=DocumentVersionRead)
def get_document_version(
    tenant_id: UUID,
    document_id: UUID,
    version_no: int,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.docs.read", scope="tenant")),
    ],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentVersionRead:
    return service.get_document_version(str(tenant_id), str(document_id), version_no, context)


@router.get("/{document_id}/versions/{version_no}/download")
def download_document_version(
    tenant_id: UUID,
    document_id: UUID,
    version_no: int,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.docs.read", scope="tenant")),
    ],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> Response:
    download = service.download_document_version(str(tenant_id), str(document_id), version_no, context)
    headers = {"Content-Disposition": f'attachment; filename="{download.file_name}"'}
    return Response(content=download.content, media_type=download.content_type, headers=headers)


@router.post("/{document_id}/links", response_model=DocumentLinkRead, status_code=status.HTTP_201_CREATED)
def add_document_link(
    tenant_id: UUID,
    document_id: UUID,
    payload: DocumentLinkCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.docs.write", scope="tenant")),
    ],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentLinkRead:
    return service.add_document_link(str(tenant_id), str(document_id), payload, context)
