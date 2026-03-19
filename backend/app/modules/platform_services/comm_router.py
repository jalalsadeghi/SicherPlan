"""HTTP API for communication templates and outbound message history."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db_session
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization
from app.modules.platform_services.comm_repository import SqlAlchemyCommunicationRepository
from app.modules.platform_services.comm_schemas import (
    DeliveryAttemptCreate,
    DeliveryAttemptRead,
    MessageTemplateRead,
    MessageTemplateUpsert,
    OutboundMessageRead,
    RenderedMessageCreate,
)
from app.modules.platform_services.comm_service import CommunicationService
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import build_object_storage_adapter


router = APIRouter(prefix="/api/platform/tenants/{tenant_id}/communication", tags=["platform-communication"])


def get_communication_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> CommunicationService:
    document_service = DocumentService(
        SqlAlchemyDocumentRepository(session),
        storage=build_object_storage_adapter(settings),
        bucket_name=settings.object_storage_bucket,
    )
    return CommunicationService(
        SqlAlchemyCommunicationRepository(session),
        document_service=document_service,
    )


@router.put("/templates/{channel}/{template_key}/{language_code}", response_model=MessageTemplateRead)
def upsert_template(
    tenant_id: UUID,
    channel: str,
    template_key: str,
    language_code: str,
    payload: MessageTemplateUpsert,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.comm.write", scope="tenant")),
    ],
    service: Annotated[CommunicationService, Depends(get_communication_service)],
) -> MessageTemplateRead:
    normalized = payload.model_copy(
        update={
            "tenant_id": str(tenant_id),
            "channel": channel,
            "template_key": template_key,
            "language_code": language_code,
        }
    )
    return service.upsert_template(str(tenant_id), normalized, context)


@router.post("/messages/render", response_model=OutboundMessageRead, status_code=status.HTTP_201_CREATED)
def render_outbound_message(
    tenant_id: UUID,
    payload: RenderedMessageCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.comm.write", scope="tenant")),
    ],
    service: Annotated[CommunicationService, Depends(get_communication_service)],
) -> OutboundMessageRead:
    return service.render_outbound_message(str(tenant_id), payload, context)


@router.get("/messages/{message_id}", response_model=OutboundMessageRead)
def get_outbound_message(
    tenant_id: UUID,
    message_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.comm.read", scope="tenant")),
    ],
    service: Annotated[CommunicationService, Depends(get_communication_service)],
) -> OutboundMessageRead:
    return service.get_outbound_message(str(tenant_id), str(message_id), context)


@router.post(
    "/messages/{message_id}/recipients/{recipient_id}/attempts",
    response_model=DeliveryAttemptRead,
    status_code=status.HTTP_201_CREATED,
)
def record_delivery_attempt(
    tenant_id: UUID,
    message_id: UUID,
    recipient_id: UUID,
    payload: DeliveryAttemptCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("platform.comm.write", scope="tenant")),
    ],
    service: Annotated[CommunicationService, Depends(get_communication_service)],
) -> DeliveryAttemptRead:
    return service.record_delivery_attempt(str(tenant_id), str(message_id), str(recipient_id), payload, context)
