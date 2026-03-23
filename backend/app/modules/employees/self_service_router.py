"""Authenticated employee self-service API surface."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.rls import rls_session_context
from app.db.session import get_db_session
from app.modules.employees.availability_service import EmployeeAvailabilityService
from app.modules.employees.mobile_read_service import EmployeeMobileReadService
from app.modules.employees.repository import SqlAlchemyEmployeeRepository
from app.modules.finance.repository import SqlAlchemyFinanceRepository
from app.modules.finance.schemas import ActualApprovalActionRequest, ActualRecordRead
from app.modules.finance.service import FinanceActualService
from app.modules.employees.schemas import (
    EmployeeAbsenceRead,
    EmployeeAddressHistoryRead,
    EmployeeAvailabilityRuleRead,
    EmployeeEventApplicationRead,
    EmployeeMobileCredentialCollectionRead,
    EmployeeMobileContextRead,
    EmployeeMobileDocumentCollectionRead,
    EmployeeReleasedScheduleCollectionRead,
    EmployeeReleasedScheduleRead,
    EmployeeReleasedScheduleResponseRequest,
    EmployeeSelfServiceAddressUpdate,
    EmployeeSelfServiceAvailabilityRuleCreate,
    EmployeeSelfServiceAvailabilityRuleUpdate,
    EmployeeSelfServiceEventApplicationCancel,
    EmployeeSelfServiceEventApplicationCreate,
    EmployeeSelfServiceProfileRead,
    EmployeeSelfServiceProfileUpdate,
)
from app.modules.planning.released_schedule_service import ReleasedScheduleService
from app.modules.planning.repository import SqlAlchemyPlanningRepository
from app.modules.employees.self_service_service import EmployeeSelfService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, get_request_authorization_context, require_authorization
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import build_object_storage_adapter
from app.config import settings
from app.rate_limit import DOCUMENT_DOWNLOAD_RULE, rate_limiter


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


def get_employee_released_schedule_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> ReleasedScheduleService:
    return ReleasedScheduleService(
        SqlAlchemyPlanningRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_employee_mobile_read_service(
    session: Annotated[Session, Depends(get_db_session)],
    context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
) -> EmployeeMobileReadService:
    document_repository = SqlAlchemyDocumentRepository(session)
    with rls_session_context(session, tenant_id=context.tenant_id, bypass=context.is_platform_admin):
        yield EmployeeMobileReadService(
            repository=SqlAlchemyEmployeeRepository(session),
            released_schedule_service=ReleasedScheduleService(
                SqlAlchemyPlanningRepository(session),
                audit_service=AuditService(SqlAlchemyAuditRepository(session)),
            ),
            document_service=DocumentService(
                document_repository,
                storage=build_object_storage_adapter(settings),
                bucket_name=settings.object_storage_bucket,
            ),
        )


def get_employee_finance_actual_service(
    session: Annotated[Session, Depends(get_db_session)],
    context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
) -> FinanceActualService:
    with rls_session_context(session, tenant_id=context.tenant_id, bypass=context.is_platform_admin):
        yield FinanceActualService(
            repository=SqlAlchemyFinanceRepository(session),
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


@router.get("/mobile-context", response_model=EmployeeMobileContextRead)
def get_mobile_context(
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeSelfService, Depends(get_employee_self_service)],
) -> EmployeeMobileContextRead:
    return service.get_mobile_context(context)


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


@router.get("/released-schedules", response_model=EmployeeReleasedScheduleCollectionRead)
def list_released_schedules(
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[ReleasedScheduleService, Depends(get_employee_released_schedule_service)],
) -> EmployeeReleasedScheduleCollectionRead:
    return service.list_employee_schedules(context)


@router.post("/released-schedules/{assignment_id}/respond", response_model=EmployeeReleasedScheduleRead)
def respond_to_released_schedule(
    assignment_id: str,
    payload: EmployeeReleasedScheduleResponseRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[ReleasedScheduleService, Depends(get_employee_released_schedule_service)],
) -> EmployeeReleasedScheduleRead:
    return service.respond_employee_assignment(context, assignment_id, payload)


@router.get("/documents", response_model=EmployeeMobileDocumentCollectionRead)
def list_mobile_documents(
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeMobileReadService, Depends(get_employee_mobile_read_service)],
) -> EmployeeMobileDocumentCollectionRead:
    return service.list_documents(context)


@router.get("/documents/{document_id}/versions/{version_no}/download")
def download_mobile_document(
    document_id: str,
    version_no: int,
    request: Request,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeMobileReadService, Depends(get_employee_mobile_read_service)],
) -> Response:
    rate_limiter.assert_allowed(
        DOCUMENT_DOWNLOAD_RULE,
        principal=f"{context.tenant_id}:{context.user_id or (request.client.host if request.client else 'anonymous')}",
    )
    download = service.download_document(context, document_id, version_no)
    return Response(
        content=download.content,
        media_type=download.content_type,
        headers={"Content-Disposition": f'attachment; filename="{download.file_name}"'},
    )


@router.get("/credentials", response_model=EmployeeMobileCredentialCollectionRead)
def list_mobile_credentials(
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[EmployeeMobileReadService, Depends(get_employee_mobile_read_service)],
) -> EmployeeMobileCredentialCollectionRead:
    return service.list_credentials(context)


@router.post("/actual-records/{actual_record_id}/preliminary-submit", response_model=ActualRecordRead)
def submit_preliminary_actual(
    actual_record_id: str,
    payload: ActualApprovalActionRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("portal.employee.access", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_employee_finance_actual_service)],
) -> ActualRecordRead:
    return service.submit_employee_preliminary_actual(actual_record_id, payload, context)


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
