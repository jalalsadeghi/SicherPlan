"""HTTP API for attendance derivation and discrepancy-aware review reads."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.field_execution.attendance_repository import SqlAlchemyAttendanceRepository
from app.modules.field_execution.attendance_service import AttendanceService
from app.modules.field_execution.schemas import AttendanceRecordListFilter, AttendanceRecordListItem, AttendanceRecordRead
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization


router = APIRouter(prefix="/api/field/tenants/{tenant_id}/attendance", tags=["field-attendance"])


def get_attendance_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> AttendanceService:
    return AttendanceService(
        repository=SqlAlchemyAttendanceRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.get("", response_model=list[AttendanceRecordListItem])
def list_attendance_records(
    tenant_id: UUID,
    filters: Annotated[AttendanceRecordListFilter, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.attendance.read", scope="tenant")),
    ],
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
) -> list[AttendanceRecordListItem]:
    return service.list_attendance_records(str(tenant_id), filters, actor)


@router.get("/{attendance_record_id}", response_model=AttendanceRecordRead)
def get_attendance_record(
    tenant_id: UUID,
    attendance_record_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.attendance.read", scope="tenant")),
    ],
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
) -> AttendanceRecordRead:
    return service.get_attendance_record(str(tenant_id), str(attendance_record_id), actor)


@router.post("/derive/shifts/{shift_id}", response_model=list[AttendanceRecordRead], status_code=status.HTTP_201_CREATED)
def derive_attendance_for_shift(
    tenant_id: UUID,
    shift_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.attendance.write", scope="tenant")),
    ],
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
) -> list[AttendanceRecordRead]:
    return service.derive_for_shift(str(tenant_id), str(shift_id), actor)


@router.post("/derive/assignments/{assignment_id}", response_model=AttendanceRecordRead, status_code=status.HTTP_201_CREATED)
def derive_attendance_for_assignment(
    tenant_id: UUID,
    assignment_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("field.attendance.write", scope="tenant")),
    ],
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
) -> AttendanceRecordRead:
    return service.derive_for_assignment(str(tenant_id), str(assignment_id), actor)
