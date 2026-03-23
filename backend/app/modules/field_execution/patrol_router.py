"""Employee-facing patrol round API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db_session
from app.modules.field_execution.patrol_service import PatrolService
from app.modules.field_execution.repository import SqlAlchemyWatchbookRepository
from app.modules.field_execution.schemas import (
    PatrolAvailableRouteRead,
    PatrolEvaluationRead,
    PatrolRoundAbortRequest,
    PatrolRoundCaptureRequest,
    PatrolRoundCompleteRequest,
    PatrolRoundRead,
    PatrolRoundStartRequest,
    PatrolSyncEnvelope,
)
from app.modules.field_execution.watchbook_service import WatchbookService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import build_object_storage_adapter


router = APIRouter(prefix="/api/field/patrol", tags=["field-patrol"])


def get_patrol_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> PatrolService:
    repository = SqlAlchemyWatchbookRepository(session)
    document_service = DocumentService(
        SqlAlchemyDocumentRepository(session),
        storage=build_object_storage_adapter(settings),
        bucket_name=settings.object_storage_bucket,
    )
    return PatrolService(
        repository=repository,
        document_service=document_service,
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
        watchbook_service=WatchbookService(
            repository=repository,
            document_service=document_service,
            audit_service=AuditService(SqlAlchemyAuditRepository(session)),
        ),
    )


@router.get("/routes", response_model=list[PatrolAvailableRouteRead])
def list_available_patrol_routes(
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[PatrolService, Depends(get_patrol_service)],
) -> list[PatrolAvailableRouteRead]:
    return service.list_available_routes(actor)


@router.get("/rounds/active", response_model=PatrolRoundRead | None)
def get_active_patrol_round(
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[PatrolService, Depends(get_patrol_service)],
) -> PatrolRoundRead | None:
    return service.get_active_round(actor)


@router.post("/rounds/start", response_model=PatrolRoundRead, status_code=status.HTTP_201_CREATED)
def start_patrol_round(
    payload: PatrolRoundStartRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[PatrolService, Depends(get_patrol_service)],
) -> PatrolRoundRead:
    return service.start_round(actor, payload)


@router.get("/rounds/{patrol_round_id}", response_model=PatrolRoundRead)
def get_patrol_round(
    patrol_round_id: str,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[PatrolService, Depends(get_patrol_service)],
) -> PatrolRoundRead:
    return service.get_round(actor, patrol_round_id)


@router.post("/rounds/{patrol_round_id}/capture", response_model=PatrolRoundRead)
def capture_patrol_checkpoint(
    patrol_round_id: str,
    payload: PatrolRoundCaptureRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[PatrolService, Depends(get_patrol_service)],
) -> PatrolRoundRead:
    return service.capture_checkpoint(actor, patrol_round_id, payload)


@router.post("/rounds/{patrol_round_id}/complete", response_model=PatrolRoundRead)
def complete_patrol_round(
    patrol_round_id: str,
    payload: PatrolRoundCompleteRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[PatrolService, Depends(get_patrol_service)],
) -> PatrolRoundRead:
    return service.complete_round(actor, patrol_round_id, payload)


@router.post("/rounds/{patrol_round_id}/abort", response_model=PatrolRoundRead)
def abort_patrol_round(
    patrol_round_id: str,
    payload: PatrolRoundAbortRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[PatrolService, Depends(get_patrol_service)],
) -> PatrolRoundRead:
    return service.abort_round(actor, patrol_round_id, payload)


@router.post("/sync", response_model=PatrolRoundRead)
def sync_patrol_round(
    payload: PatrolSyncEnvelope,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[PatrolService, Depends(get_patrol_service)],
) -> PatrolRoundRead:
    return service.sync_round(actor, payload)


@router.get("/rounds/{patrol_round_id}/evaluation", response_model=PatrolEvaluationRead)
def get_patrol_evaluation(
    patrol_round_id: str,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[PatrolService, Depends(get_patrol_service)],
) -> PatrolEvaluationRead:
    return service.get_evaluation(actor, patrol_round_id)
