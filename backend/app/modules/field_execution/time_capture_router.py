"""HTTP API for time-capture device management and raw event ingest."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.field_execution.schemas import (
    TimeCaptureDeviceCreate,
    TimeCaptureDeviceFilter,
    TimeCaptureDeviceListItem,
    TimeCaptureDeviceRead,
    TimeCaptureDeviceUpdate,
    TimeCaptureEventCapture,
    TimeCaptureEventFilter,
    TimeCaptureEventListItem,
    TimeCaptureEventRead,
    TimeCaptureOwnEventCollectionRead,
    TimeCapturePolicyCreate,
    TimeCapturePolicyFilter,
    TimeCapturePolicyListItem,
    TimeCapturePolicyRead,
    TimeCapturePolicyUpdate,
    TimeCaptureTerminalEventCapture,
    TimeEventValidationStatusUpdate,
)
from app.modules.field_execution.time_capture_repository import SqlAlchemyTimeCaptureRepository
from app.modules.field_execution.time_capture_service import TimeCaptureService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, get_request_authorization_context, require_authorization


router = APIRouter(tags=["field-time-capture"])


def get_time_capture_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> TimeCaptureService:
    return TimeCaptureService(
        repository=SqlAlchemyTimeCaptureRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.get("/api/field/tenants/{tenant_id}/time-capture/devices", response_model=list[TimeCaptureDeviceListItem])
def list_time_capture_devices(
    tenant_id: UUID,
    filters: Annotated[TimeCaptureDeviceFilter, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.time_capture.read", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> list[TimeCaptureDeviceListItem]:
    return service.list_devices(str(tenant_id), filters, actor)


@router.post("/api/field/tenants/{tenant_id}/time-capture/devices", response_model=TimeCaptureDeviceRead, status_code=status.HTTP_201_CREATED)
def create_time_capture_device(
    tenant_id: UUID,
    payload: TimeCaptureDeviceCreate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.time_capture.write", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> TimeCaptureDeviceRead:
    return service.create_device(str(tenant_id), payload, actor)


@router.get("/api/field/tenants/{tenant_id}/time-capture/devices/{device_id}", response_model=TimeCaptureDeviceRead)
def get_time_capture_device(
    tenant_id: UUID,
    device_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.time_capture.read", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> TimeCaptureDeviceRead:
    return service.get_device(str(tenant_id), str(device_id), actor)


@router.patch("/api/field/tenants/{tenant_id}/time-capture/devices/{device_id}", response_model=TimeCaptureDeviceRead)
def update_time_capture_device(
    tenant_id: UUID,
    device_id: UUID,
    payload: TimeCaptureDeviceUpdate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.time_capture.write", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> TimeCaptureDeviceRead:
    return service.update_device(str(tenant_id), str(device_id), payload, actor)


@router.get("/api/field/tenants/{tenant_id}/time-capture/policies", response_model=list[TimeCapturePolicyListItem])
def list_time_capture_policies(
    tenant_id: UUID,
    filters: Annotated[TimeCapturePolicyFilter, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.time_capture.read", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> list[TimeCapturePolicyListItem]:
    return service.list_policies(str(tenant_id), filters, actor)


@router.post("/api/field/tenants/{tenant_id}/time-capture/policies", response_model=TimeCapturePolicyRead, status_code=status.HTTP_201_CREATED)
def create_time_capture_policy(
    tenant_id: UUID,
    payload: TimeCapturePolicyCreate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.time_capture.write", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> TimeCapturePolicyRead:
    return service.create_policy(str(tenant_id), payload, actor)


@router.get("/api/field/tenants/{tenant_id}/time-capture/policies/{policy_id}", response_model=TimeCapturePolicyRead)
def get_time_capture_policy(
    tenant_id: UUID,
    policy_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.time_capture.read", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> TimeCapturePolicyRead:
    return service.get_policy(str(tenant_id), str(policy_id), actor)


@router.patch("/api/field/tenants/{tenant_id}/time-capture/policies/{policy_id}", response_model=TimeCapturePolicyRead)
def update_time_capture_policy(
    tenant_id: UUID,
    policy_id: UUID,
    payload: TimeCapturePolicyUpdate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.time_capture.write", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> TimeCapturePolicyRead:
    return service.update_policy(str(tenant_id), str(policy_id), payload, actor)


@router.get("/api/field/tenants/{tenant_id}/time-capture/events", response_model=list[TimeCaptureEventListItem])
def list_time_capture_events(
    tenant_id: UUID,
    filters: Annotated[TimeCaptureEventFilter, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.time_capture.read", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> list[TimeCaptureEventListItem]:
    return service.list_time_events(str(tenant_id), filters, actor)


@router.patch("/api/field/tenants/{tenant_id}/time-capture/events/{event_id}/validation-status", response_model=TimeCaptureEventRead)
def transition_time_event_validation_status(
    tenant_id: UUID,
    event_id: UUID,
    payload: TimeEventValidationStatusUpdate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.time_capture.write", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> TimeCaptureEventRead:
    return service.transition_event_validation_status(str(tenant_id), str(event_id), payload, actor)


@router.get("/api/field/time-capture/me/events", response_model=TimeCaptureOwnEventCollectionRead)
def list_own_time_capture_events(
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> TimeCaptureOwnEventCollectionRead:
    return service.list_own_time_events(actor)


@router.post("/api/field/time-capture/me/events/browser", response_model=TimeCaptureEventRead, status_code=status.HTTP_201_CREATED)
def capture_browser_time_event(
    payload: TimeCaptureEventCapture,
    request: Request,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> TimeCaptureEventRead:
    return service.capture_employee_event(actor, payload, source_channel_code="browser", source_ip=request.client.host if request.client else None)


@router.post("/api/field/time-capture/me/events/mobile", response_model=TimeCaptureEventRead, status_code=status.HTTP_201_CREATED)
def capture_mobile_time_event(
    payload: TimeCaptureEventCapture,
    request: Request,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> TimeCaptureEventRead:
    return service.capture_employee_event(actor, payload, source_channel_code="mobile", source_ip=request.client.host if request.client else None)


@router.post("/api/field/tenants/{tenant_id}/time-capture/terminal/events", response_model=TimeCaptureEventRead, status_code=status.HTTP_201_CREATED)
def capture_terminal_time_event(
    tenant_id: UUID,
    payload: TimeCaptureTerminalEventCapture,
    request: Request,
    service: Annotated[TimeCaptureService, Depends(get_time_capture_service)],
) -> TimeCaptureEventRead:
    return service.capture_terminal_event(str(tenant_id), payload, source_ip=request.client.host if request.client else None)
