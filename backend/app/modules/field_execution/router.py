"""HTTP API for watchbook maintenance and released reads."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db_session
from app.modules.field_execution.repository import SqlAlchemyWatchbookRepository
from app.modules.field_execution.schemas import (
    WatchbookEntryCreate,
    WatchbookEntryRead,
    WatchbookListFilter,
    WatchbookListItem,
    WatchbookOpenRequest,
    WatchbookPdfRead,
    WatchbookRead,
    WatchbookReviewRequest,
    WatchbookVisibilityUpdate,
)
from app.modules.field_execution.watchbook_service import WatchbookService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import build_object_storage_adapter


router = APIRouter(prefix="/api/field/tenants/{tenant_id}/watchbooks", tags=["field-watchbooks"])


def get_watchbook_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> WatchbookService:
    return WatchbookService(
        repository=SqlAlchemyWatchbookRepository(session),
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.get("", response_model=list[WatchbookListItem])
def list_watchbooks(
    tenant_id: UUID,
    filters: Annotated[WatchbookListFilter, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.watchbook.read", scope="tenant")),
    ],
    service: Annotated[WatchbookService, Depends(get_watchbook_service)],
) -> list[WatchbookListItem]:
    return service.list_watchbooks(str(tenant_id), filters, actor)


@router.post("/open", response_model=WatchbookRead, status_code=status.HTTP_201_CREATED)
def open_watchbook(
    tenant_id: UUID,
    payload: WatchbookOpenRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.watchbook.write", scope="tenant")),
    ],
    service: Annotated[WatchbookService, Depends(get_watchbook_service)],
) -> WatchbookRead:
    return service.open_or_create_watchbook(str(tenant_id), payload, actor)


@router.get("/{watchbook_id}", response_model=WatchbookRead)
def get_watchbook(
    tenant_id: UUID,
    watchbook_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.watchbook.read", scope="tenant")),
    ],
    service: Annotated[WatchbookService, Depends(get_watchbook_service)],
) -> WatchbookRead:
    return service.get_watchbook(str(tenant_id), str(watchbook_id), actor)


@router.post("/{watchbook_id}/entries", response_model=WatchbookEntryRead, status_code=status.HTTP_201_CREATED)
def create_watchbook_entry(
    tenant_id: UUID,
    watchbook_id: UUID,
    payload: WatchbookEntryCreate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.watchbook.write", scope="tenant")),
    ],
    service: Annotated[WatchbookService, Depends(get_watchbook_service)],
) -> WatchbookEntryRead:
    return service.create_entry(str(tenant_id), str(watchbook_id), payload, actor)


@router.post("/{watchbook_id}/review", response_model=WatchbookRead)
def review_watchbook(
    tenant_id: UUID,
    watchbook_id: UUID,
    payload: WatchbookReviewRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.watchbook.review", scope="tenant")),
    ],
    service: Annotated[WatchbookService, Depends(get_watchbook_service)],
) -> WatchbookRead:
    return service.review_watchbook(str(tenant_id), str(watchbook_id), payload, actor)


@router.post("/{watchbook_id}/close", response_model=WatchbookRead)
def close_watchbook(
    tenant_id: UUID,
    watchbook_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.watchbook.review", scope="tenant")),
    ],
    service: Annotated[WatchbookService, Depends(get_watchbook_service)],
) -> WatchbookRead:
    return service.close_watchbook(str(tenant_id), str(watchbook_id), actor)


@router.patch("/{watchbook_id}/visibility", response_model=WatchbookRead)
def update_watchbook_visibility(
    tenant_id: UUID,
    watchbook_id: UUID,
    payload: WatchbookVisibilityUpdate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.watchbook.review", scope="tenant")),
    ],
    service: Annotated[WatchbookService, Depends(get_watchbook_service)],
) -> WatchbookRead:
    return service.update_visibility(str(tenant_id), str(watchbook_id), payload, actor)


@router.post("/{watchbook_id}/pdf", response_model=WatchbookPdfRead)
def generate_watchbook_pdf(
    tenant_id: UUID,
    watchbook_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.watchbook.review", scope="tenant")),
    ],
    service: Annotated[WatchbookService, Depends(get_watchbook_service)],
) -> WatchbookPdfRead:
    return service.generate_pdf(str(tenant_id), str(watchbook_id), actor)
