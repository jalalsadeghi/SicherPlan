"""Authenticated employee self-service API surface."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.employees.availability_service import EmployeeAvailabilityService
from app.modules.employees.repository import SqlAlchemyEmployeeRepository
from app.modules.employees.schemas import (
    EmployeeAbsenceRead,
    EmployeeAddressHistoryRead,
    EmployeeAvailabilityRuleRead,
    EmployeeEventApplicationRead,
    EmployeeSelfServiceAddressUpdate,
    EmployeeSelfServiceAvailabilityRuleCreate,
    EmployeeSelfServiceAvailabilityRuleUpdate,
    EmployeeSelfServiceEventApplicationCancel,
    EmployeeSelfServiceEventApplicationCreate,
    EmployeeSelfServiceProfileRead,
    EmployeeSelfServiceProfileUpdate,
)
from app.modules.employees.self_service_service import EmployeeSelfService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization


router = APIRouter(prefix="/api/employee-self-service/me", tags=["employee-self-service"])


def get_employee_self_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> EmployeeSelfService:
    repository = SqlAlchemyEmployeeRepository(session)
    return EmployeeSelfService(
        repository=repository,
        availability_service=EmployeeAvailabilityService(
            repository,
            audit_service=AuditService(SqlAlchemyAuditRepository(session)),
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.get("/profile", response_model=EmployeeSelfServiceProfileRead)
def get_profile(
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeSelfService, Depends(get_employee_self_service)],
) -> EmployeeSelfServiceProfileRead:
    return service.get_profile(context)


@router.patch("/profile", response_model=EmployeeSelfServiceProfileRead)
def update_profile(
    payload: EmployeeSelfServiceProfileUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeSelfService, Depends(get_employee_self_service)],
) -> EmployeeSelfServiceProfileRead:
    return service.update_profile(payload, context)


@router.post("/current-address", response_model=EmployeeAddressHistoryRead, status_code=status.HTTP_201_CREATED)
def update_current_address(
    payload: EmployeeSelfServiceAddressUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeSelfService, Depends(get_employee_self_service)],
) -> EmployeeAddressHistoryRead:
    return service.update_current_address(payload, context)


@router.get("/availability-rules", response_model=list[EmployeeAvailabilityRuleRead])
def list_availability_rules(
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeSelfService, Depends(get_employee_self_service)],
) -> list[EmployeeAvailabilityRuleRead]:
    return service.list_availability_rules(context)


@router.post("/availability-rules", response_model=EmployeeAvailabilityRuleRead, status_code=status.HTTP_201_CREATED)
def create_availability_rule(
    payload: EmployeeSelfServiceAvailabilityRuleCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeSelfService, Depends(get_employee_self_service)],
) -> EmployeeAvailabilityRuleRead:
    return service.create_availability_rule(payload, context)


@router.patch("/availability-rules/{rule_id}", response_model=EmployeeAvailabilityRuleRead)
def update_availability_rule(
    rule_id: str,
    payload: EmployeeSelfServiceAvailabilityRuleUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeSelfService, Depends(get_employee_self_service)],
) -> EmployeeAvailabilityRuleRead:
    return service.update_availability_rule(rule_id, payload, context)


@router.get("/absences", response_model=list[EmployeeAbsenceRead])
def list_absences(
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeSelfService, Depends(get_employee_self_service)],
) -> list[EmployeeAbsenceRead]:
    return service.list_absences(context)


@router.get("/event-applications", response_model=list[EmployeeEventApplicationRead])
def list_event_applications(
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeSelfService, Depends(get_employee_self_service)],
) -> list[EmployeeEventApplicationRead]:
    return service.list_event_applications(context)


@router.post("/event-applications", response_model=EmployeeEventApplicationRead, status_code=status.HTTP_201_CREATED)
def create_event_application(
    payload: EmployeeSelfServiceEventApplicationCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeSelfService, Depends(get_employee_self_service)],
) -> EmployeeEventApplicationRead:
    return service.create_event_application(payload, context)


@router.post("/event-applications/{application_id}/cancel", response_model=EmployeeEventApplicationRead)
def cancel_event_application(
    application_id: str,
    payload: EmployeeSelfServiceEventApplicationCancel,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeSelfService, Depends(get_employee_self_service)],
) -> EmployeeEventApplicationRead:
    return service.cancel_event_application(application_id, payload, context)
