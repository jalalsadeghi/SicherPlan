"""HTTP API for notice authoring, publishing, and acknowledgement flows."""

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
from app.modules.platform_services.info_repository import SqlAlchemyNoticeRepository
from app.modules.platform_services.info_schemas import (
    NoticeAcknowledgeRequest,
    NoticeCreate,
    NoticeListItem,
    NoticePublishRequest,
    NoticeRead,
    NoticeReadEvidenceRead,
)
from app.modules.platform_services.info_service import NoticeService
from app.modules.platform_services.storage import build_object_storage_adapter


router = APIRouter(prefix="/api/platform/tenants/{tenant_id}/info/notices", tags=["platform-notices"])


def get_notice_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> NoticeService:
    document_service = DocumentService(
        SqlAlchemyDocumentRepository(session),
        storage=build_object_storage_adapter(settings),
        bucket_name=settings.object_storage_bucket,
    )
    return NoticeService(SqlAlchemyNoticeRepository(session), document_service=document_service)


@router.post("", response_model=NoticeRead, status_code=status.HTTP_201_CREATED)
def create_notice(
    tenant_id: UUID,
    payload: NoticeCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.info.write", scope="tenant")),
    ],
    service: Annotated[NoticeService, Depends(get_notice_service)],
) -> NoticeRead:
    return service.create_notice(str(tenant_id), payload, context)


@router.get("", response_model=list[NoticeListItem])
def list_admin_notices(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.info.write", scope="tenant")),
    ],
    service: Annotated[NoticeService, Depends(get_notice_service)],
) -> list[NoticeListItem]:
    return service.list_admin_notices(str(tenant_id), context)


@router.get("/my/feed", response_model=list[NoticeListItem])
def list_visible_notices(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.info.read", scope="tenant")),
    ],
    service: Annotated[NoticeService, Depends(get_notice_service)],
) -> list[NoticeListItem]:
    return service.list_visible_notices(str(tenant_id), context)


@router.get("/{notice_id}", response_model=NoticeRead)
def get_notice_admin(
    tenant_id: UUID,
    notice_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.info.write", scope="tenant")),
    ],
    service: Annotated[NoticeService, Depends(get_notice_service)],
) -> NoticeRead:
    return service.get_notice_admin(str(tenant_id), str(notice_id), context)


@router.post("/{notice_id}/publish", response_model=NoticeRead)
def publish_notice(
    tenant_id: UUID,
    notice_id: UUID,
    payload: NoticePublishRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.info.write", scope="tenant")),
    ],
    service: Annotated[NoticeService, Depends(get_notice_service)],
) -> NoticeRead:
    return service.publish_notice(str(tenant_id), str(notice_id), payload, context)


@router.post("/{notice_id}/unpublish", response_model=NoticeRead)
def unpublish_notice(
    tenant_id: UUID,
    notice_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.info.write", scope="tenant")),
    ],
    service: Annotated[NoticeService, Depends(get_notice_service)],
) -> NoticeRead:
    return service.unpublish_notice(str(tenant_id), str(notice_id), context)


@router.post("/{notice_id}/open", response_model=NoticeReadEvidenceRead)
def open_notice(
    tenant_id: UUID,
    notice_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.info.read", scope="tenant")),
    ],
    service: Annotated[NoticeService, Depends(get_notice_service)],
) -> NoticeReadEvidenceRead:
    return service.open_notice(str(tenant_id), str(notice_id), context)


@router.post("/{notice_id}/acknowledge", response_model=NoticeReadEvidenceRead)
def acknowledge_notice(
    tenant_id: UUID,
    notice_id: UUID,
    payload: NoticeAcknowledgeRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.info.read", scope="tenant")),
    ],
    service: Annotated[NoticeService, Depends(get_notice_service)],
) -> NoticeReadEvidenceRead:
    return service.acknowledge_notice(str(tenant_id), str(notice_id), payload, context)
