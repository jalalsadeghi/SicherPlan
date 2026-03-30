"""HTTP API for employee operational file maintenance."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db_session
from app.modules.employees.availability_service import EmployeeAvailabilityService
from app.modules.employees.catalog_seed import seed_sample_employee_catalogs
from app.modules.employees.compensation_service import EmployeeCompensationService
from app.modules.employees.file_service import EmployeeFileService
from app.modules.employees.ops_service import EmployeeOpsService
from app.modules.employees.qualification_service import EmployeeQualificationService
from app.modules.employees.repository import SqlAlchemyEmployeeRepository
from app.modules.employees.schemas import (
    EmployeeAccessAttachExistingRequest,
    EmployeeAccessCreateUserRequest,
    EmployeeAccessDetachRequest,
    EmployeeAccessLinkRead,
    EmployeeAccessResetPasswordRequest,
    EmployeeAccessUpdateUserRequest,
    EmployeeAdvanceCreate,
    EmployeeAdvanceFilter,
    EmployeeAdvanceRead,
    EmployeeAdvanceUpdate,
    EmployeeAbsenceCreate,
    EmployeeAbsenceFilter,
    EmployeeAbsenceRead,
    EmployeeAbsenceUpdate,
    EmployeeAddressHistoryCreate,
    EmployeeAddressHistoryRead,
    EmployeeAddressHistoryUpdate,
    EmployeeAllowanceCreate,
    EmployeeAllowanceFilter,
    EmployeeAllowanceRead,
    EmployeeAllowanceUpdate,
    EmployeeAvailabilityRuleCreate,
    EmployeeAvailabilityRuleFilter,
    EmployeeAvailabilityRuleRead,
    EmployeeAvailabilityRuleUpdate,
    EmployeeCatalogBootstrapRead,
    EmployeeCredentialBadgeIssue,
    EmployeeCredentialBadgeRead,
    EmployeeCredentialCreate,
    EmployeeCredentialFilter,
    EmployeeCredentialRead,
    EmployeeCredentialUpdate,
    EmployeeDocumentListItemRead,
    EmployeeEventApplicationCreate,
    EmployeeEventApplicationFilter,
    EmployeeEventApplicationRead,
    EmployeeEventApplicationUpdate,
    EmployeeExportRequest,
    EmployeeExportResult,
    EmployeeFilter,
    EmployeeGroupCreate,
    EmployeeGroupMemberCreate,
    EmployeeGroupMemberRead,
    EmployeeGroupMemberUpdate,
    EmployeeGroupRead,
    EmployeeGroupUpdate,
    EmployeeListItem,
    EmployeeNoteCreate,
    EmployeeNoteRead,
    EmployeeNoteUpdate,
    EmployeeImportDryRunRequest,
    EmployeeImportDryRunResult,
    EmployeeImportExecuteRequest,
    EmployeeImportExecuteResult,
    EmployeeLifecycleTransitionRequest,
    EmployeeLeaveBalanceFilter,
    EmployeeLeaveBalanceRead,
    EmployeeLeaveBalanceUpsert,
    EmployeeOperationalCreate,
    EmployeeOperationalRead,
    EmployeeOperationalUpdate,
    EmployeeQualificationCreate,
    EmployeeQualificationFilter,
    EmployeeQualificationProofLinkCreate,
    EmployeeQualificationProofRead,
    EmployeeQualificationProofUpload,
    EmployeeQualificationRead,
    EmployeeQualificationUpdate,
    EmployeePhotoRead,
    EmployeePhotoUpload,
    EmployeeTimeAccountCreate,
    EmployeeTimeAccountFilter,
    EmployeeTimeAccountRead,
    EmployeeTimeAccountTxnCreate,
    EmployeeTimeAccountTxnRead,
    FunctionTypeCreate,
    FunctionTypeRead,
    FunctionTypeUpdate,
    QualificationTypeCreate,
    QualificationTypeRead,
    QualificationTypeUpdate,
)
from app.modules.employees.service import EmployeeService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import build_object_storage_adapter


router = APIRouter(prefix="/api/employees/tenants/{tenant_id}/employees", tags=["employees"])


def get_employee_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> EmployeeService:
    return EmployeeService(
        SqlAlchemyEmployeeRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_employee_file_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> EmployeeFileService:
    document_repository = SqlAlchemyDocumentRepository(session)
    return EmployeeFileService(
        employee_repository=SqlAlchemyEmployeeRepository(session),
        document_repository=document_repository,
        document_service=DocumentService(
            document_repository,
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_employee_ops_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> EmployeeOpsService:
    repository = SqlAlchemyEmployeeRepository(session)
    document_repository = SqlAlchemyDocumentRepository(session)
    return EmployeeOpsService(
        employee_service=EmployeeService(repository, audit_service=AuditService(SqlAlchemyAuditRepository(session))),
        repository=repository,
        document_service=DocumentService(
            document_repository,
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_employee_qualification_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> EmployeeQualificationService:
    repository = SqlAlchemyEmployeeRepository(session)
    document_repository = SqlAlchemyDocumentRepository(session)
    return EmployeeQualificationService(
        repository=repository,
        document_repository=document_repository,
        document_service=DocumentService(
            document_repository,
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_employee_availability_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> EmployeeAvailabilityService:
    return EmployeeAvailabilityService(
        SqlAlchemyEmployeeRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_employee_compensation_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> EmployeeCompensationService:
    repository = SqlAlchemyEmployeeRepository(session)
    document_repository = SqlAlchemyDocumentRepository(session)
    return EmployeeCompensationService(
        repository=repository,
        document_repository=document_repository,
        document_service=DocumentService(
            document_repository,
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.get("", response_model=list[EmployeeListItem])
def list_employees(
    tenant_id: UUID,
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    default_branch_id: UUID | None = Query(default=None),
    default_mandate_id: UUID | None = Query(default=None),
    include_archived: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeService, Depends(get_employee_service)] = None,
) -> list[EmployeeListItem]:
    return service.list_operational_employees(
        str(tenant_id),
        context,
        EmployeeFilter(
            search=search,
            status=status_filter,
            default_branch_id=str(default_branch_id) if default_branch_id else None,
            default_mandate_id=str(default_mandate_id) if default_mandate_id else None,
            include_archived=include_archived,
        ),
    )


@router.post("", response_model=EmployeeOperationalRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    tenant_id: UUID,
    payload: EmployeeOperationalCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeOperationalRead:
    return service.create_employee(str(tenant_id), payload, context)


@router.get("/groups/catalog", response_model=list[EmployeeGroupRead])
def list_groups(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeService, Depends(get_employee_service)] = None,
) -> list[EmployeeGroupRead]:
    return service.list_groups(str(tenant_id), context)


@router.post("/groups/catalog", response_model=EmployeeGroupRead, status_code=status.HTTP_201_CREATED)
def create_group(
    tenant_id: UUID,
    payload: EmployeeGroupCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeGroupRead:
    return service.create_group(str(tenant_id), payload, context)


@router.patch("/groups/catalog/{group_id}", response_model=EmployeeGroupRead)
def update_group(
    tenant_id: UUID,
    group_id: UUID,
    payload: EmployeeGroupUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeGroupRead:
    return service.update_group(str(tenant_id), str(group_id), payload, context)


@router.post("/groups/memberships", response_model=EmployeeGroupMemberRead, status_code=status.HTTP_201_CREATED)
def add_group_membership(
    tenant_id: UUID,
    payload: EmployeeGroupMemberCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeGroupMemberRead:
    return service.add_group_member(str(tenant_id), payload, context)


@router.patch("/groups/memberships/{member_id}", response_model=EmployeeGroupMemberRead)
def update_group_membership(
    tenant_id: UUID,
    member_id: UUID,
    payload: EmployeeGroupMemberUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeGroupMemberRead:
    return service.update_group_member(str(tenant_id), str(member_id), payload, context)


@router.get("/{employee_id}", response_model=EmployeeOperationalRead)
def get_employee(
    tenant_id: UUID,
    employee_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeService, Depends(get_employee_service)] = None,
) -> EmployeeOperationalRead:
    return service.get_operational_employee(str(tenant_id), str(employee_id), context)


@router.patch("/{employee_id}", response_model=EmployeeOperationalRead)
def update_employee(
    tenant_id: UUID,
    employee_id: UUID,
    payload: EmployeeOperationalUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeOperationalRead:
    return service.update_employee(str(tenant_id), str(employee_id), payload, context)


@router.post("/{employee_id}/archive", response_model=EmployeeOperationalRead)
def archive_employee(
    tenant_id: UUID,
    employee_id: UUID,
    payload: EmployeeLifecycleTransitionRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeOperationalRead:
    return service.archive_employee(str(tenant_id), str(employee_id), payload, context)


@router.post("/{employee_id}/reactivate", response_model=EmployeeOperationalRead)
def reactivate_employee(
    tenant_id: UUID,
    employee_id: UUID,
    payload: EmployeeLifecycleTransitionRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeOperationalRead:
    return service.reactivate_employee(str(tenant_id), str(employee_id), payload, context)


@router.get("/{employee_id}/addresses", response_model=list[EmployeeAddressHistoryRead])
def list_employee_addresses(
    tenant_id: UUID,
    employee_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeService, Depends(get_employee_service)] = None,
) -> list[EmployeeAddressHistoryRead]:
    return service.list_address_history(str(tenant_id), str(employee_id), context)


@router.post("/{employee_id}/addresses", response_model=EmployeeAddressHistoryRead, status_code=status.HTTP_201_CREATED)
def add_employee_address(
    tenant_id: UUID,
    employee_id: UUID,
    payload: EmployeeAddressHistoryCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeAddressHistoryRead:
    return service.add_address_history(str(tenant_id), str(employee_id), payload, context)


@router.patch("/{employee_id}/addresses/{history_id}", response_model=EmployeeAddressHistoryRead)
def update_employee_address(
    tenant_id: UUID,
    employee_id: UUID,
    history_id: UUID,
    payload: EmployeeAddressHistoryUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeAddressHistoryRead:
    return service.update_address_history(str(tenant_id), str(employee_id), str(history_id), payload, context)


@router.get("/availability-rules", response_model=list[EmployeeAvailabilityRuleRead])
def list_availability_rules(
    tenant_id: UUID,
    employee_id: UUID | None = Query(default=None),
    rule_kind: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    active_on: datetime | None = Query(default=None),
    include_archived: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeAvailabilityService, Depends(get_employee_availability_service)] = None,
) -> list[EmployeeAvailabilityRuleRead]:
    return service.list_availability_rules(
        str(tenant_id),
        EmployeeAvailabilityRuleFilter(
            employee_id=str(employee_id) if employee_id else None,
            rule_kind=rule_kind,
            status=status_filter,
            active_on=active_on,
            include_archived=include_archived,
        ),
        context,
    )


@router.post("/availability-rules", response_model=EmployeeAvailabilityRuleRead, status_code=status.HTTP_201_CREATED)
def create_availability_rule(
    tenant_id: UUID,
    payload: EmployeeAvailabilityRuleCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeAvailabilityService, Depends(get_employee_availability_service)],
) -> EmployeeAvailabilityRuleRead:
    return service.create_availability_rule(str(tenant_id), payload, context)


@router.patch("/availability-rules/{rule_id}", response_model=EmployeeAvailabilityRuleRead)
def update_availability_rule(
    tenant_id: UUID,
    rule_id: UUID,
    payload: EmployeeAvailabilityRuleUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeAvailabilityService, Depends(get_employee_availability_service)],
) -> EmployeeAvailabilityRuleRead:
    return service.update_availability_rule(str(tenant_id), str(rule_id), payload, context)


@router.get("/absences", response_model=list[EmployeeAbsenceRead])
def list_absences(
    tenant_id: UUID,
    employee_id: UUID | None = Query(default=None),
    absence_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    starts_on_or_after: date | None = Query(default=None),
    ends_on_or_before: date | None = Query(default=None),
    include_archived: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeAvailabilityService, Depends(get_employee_availability_service)] = None,
) -> list[EmployeeAbsenceRead]:
    return service.list_absences(
        str(tenant_id),
        EmployeeAbsenceFilter(
            employee_id=str(employee_id) if employee_id else None,
            absence_type=absence_type,
            status=status_filter,
            starts_on_or_after=starts_on_or_after,
            ends_on_or_before=ends_on_or_before,
            include_archived=include_archived,
        ),
        context,
    )


@router.post("/absences", response_model=EmployeeAbsenceRead, status_code=status.HTTP_201_CREATED)
def create_absence(
    tenant_id: UUID,
    payload: EmployeeAbsenceCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.write", scope="tenant")),
    ],
    service: Annotated[EmployeeAvailabilityService, Depends(get_employee_availability_service)],
) -> EmployeeAbsenceRead:
    return service.create_absence(str(tenant_id), payload, context)


@router.patch("/absences/{absence_id}", response_model=EmployeeAbsenceRead)
def update_absence(
    tenant_id: UUID,
    absence_id: UUID,
    payload: EmployeeAbsenceUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.write", scope="tenant")),
    ],
    service: Annotated[EmployeeAvailabilityService, Depends(get_employee_availability_service)],
) -> EmployeeAbsenceRead:
    return service.update_absence(str(tenant_id), str(absence_id), payload, context)


@router.get("/leave-balances", response_model=list[EmployeeLeaveBalanceRead])
def list_leave_balances(
    tenant_id: UUID,
    employee_id: UUID | None = Query(default=None),
    balance_year: int | None = Query(default=None),
    include_archived: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeAvailabilityService, Depends(get_employee_availability_service)] = None,
) -> list[EmployeeLeaveBalanceRead]:
    return service.list_leave_balances(
        str(tenant_id),
        EmployeeLeaveBalanceFilter(
            employee_id=str(employee_id) if employee_id else None,
            balance_year=balance_year,
            include_archived=include_archived,
        ),
        context,
    )


@router.post("/leave-balances", response_model=EmployeeLeaveBalanceRead, status_code=status.HTTP_201_CREATED)
def upsert_leave_balance(
    tenant_id: UUID,
    payload: EmployeeLeaveBalanceUpsert,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.write", scope="tenant")),
    ],
    service: Annotated[EmployeeAvailabilityService, Depends(get_employee_availability_service)],
) -> EmployeeLeaveBalanceRead:
    return service.upsert_leave_balance(str(tenant_id), payload, context)


@router.get("/event-applications", response_model=list[EmployeeEventApplicationRead])
def list_event_applications(
    tenant_id: UUID,
    employee_id: UUID | None = Query(default=None),
    planning_record_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    include_archived: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeAvailabilityService, Depends(get_employee_availability_service)] = None,
) -> list[EmployeeEventApplicationRead]:
    return service.list_event_applications(
        str(tenant_id),
        EmployeeEventApplicationFilter(
            employee_id=str(employee_id) if employee_id else None,
            planning_record_id=str(planning_record_id) if planning_record_id else None,
            status=status_filter,
            include_archived=include_archived,
        ),
        context,
    )


@router.post("/event-applications", response_model=EmployeeEventApplicationRead, status_code=status.HTTP_201_CREATED)
def create_event_application(
    tenant_id: UUID,
    payload: EmployeeEventApplicationCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeAvailabilityService, Depends(get_employee_availability_service)],
) -> EmployeeEventApplicationRead:
    return service.create_event_application(str(tenant_id), payload, context)


@router.patch("/event-applications/{application_id}", response_model=EmployeeEventApplicationRead)
def update_event_application(
    tenant_id: UUID,
    application_id: UUID,
    payload: EmployeeEventApplicationUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeAvailabilityService, Depends(get_employee_availability_service)],
) -> EmployeeEventApplicationRead:
    return service.update_event_application(str(tenant_id), str(application_id), payload, context)


@router.get("/time-accounts", response_model=list[EmployeeTimeAccountRead])
def list_time_accounts(
    tenant_id: UUID,
    employee_id: UUID | None = Query(default=None),
    account_type: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)] = None,
) -> list[EmployeeTimeAccountRead]:
    return service.list_time_accounts(
        str(tenant_id),
        EmployeeTimeAccountFilter(
            employee_id=str(employee_id) if employee_id else None,
            account_type=account_type,
            include_archived=include_archived,
        ),
        context,
    )


@router.post("/time-accounts", response_model=EmployeeTimeAccountRead, status_code=status.HTTP_201_CREATED)
def create_time_account(
    tenant_id: UUID,
    payload: EmployeeTimeAccountCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.write", scope="tenant")),
    ],
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)],
) -> EmployeeTimeAccountRead:
    return service.create_time_account(str(tenant_id), payload, context)


@router.post("/time-accounts/{account_id}/transactions", response_model=EmployeeTimeAccountTxnRead, status_code=status.HTTP_201_CREATED)
def add_time_account_transaction(
    tenant_id: UUID,
    account_id: UUID,
    payload: EmployeeTimeAccountTxnCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.write", scope="tenant")),
    ],
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)],
) -> EmployeeTimeAccountTxnRead:
    return service.add_time_account_txn(str(tenant_id), str(account_id), payload, context)


@router.get("/allowances", response_model=list[EmployeeAllowanceRead])
def list_allowances(
    tenant_id: UUID,
    employee_id: UUID | None = Query(default=None),
    basis_code: str | None = Query(default=None),
    function_type_id: UUID | None = Query(default=None),
    qualification_type_id: UUID | None = Query(default=None),
    active_on: date | None = Query(default=None),
    include_archived: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)] = None,
) -> list[EmployeeAllowanceRead]:
    return service.list_allowances(
        str(tenant_id),
        EmployeeAllowanceFilter(
            employee_id=str(employee_id) if employee_id else None,
            basis_code=basis_code,
            function_type_id=str(function_type_id) if function_type_id else None,
            qualification_type_id=str(qualification_type_id) if qualification_type_id else None,
            active_on=active_on,
            include_archived=include_archived,
        ),
        context,
    )


@router.post("/allowances", response_model=EmployeeAllowanceRead, status_code=status.HTTP_201_CREATED)
def create_allowance(
    tenant_id: UUID,
    payload: EmployeeAllowanceCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.write", scope="tenant")),
    ],
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)],
) -> EmployeeAllowanceRead:
    return service.create_allowance(str(tenant_id), payload, context)


@router.patch("/allowances/{allowance_id}", response_model=EmployeeAllowanceRead)
def update_allowance(
    tenant_id: UUID,
    allowance_id: UUID,
    payload: EmployeeAllowanceUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.write", scope="tenant")),
    ],
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)],
) -> EmployeeAllowanceRead:
    return service.update_allowance(str(tenant_id), str(allowance_id), payload, context)


@router.get("/advances", response_model=list[EmployeeAdvanceRead])
def list_advances(
    tenant_id: UUID,
    employee_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    include_archived: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)] = None,
) -> list[EmployeeAdvanceRead]:
    return service.list_advances(
        str(tenant_id),
        EmployeeAdvanceFilter(
            employee_id=str(employee_id) if employee_id else None,
            status=status_filter,
            include_archived=include_archived,
        ),
        context,
    )


@router.post("/advances", response_model=EmployeeAdvanceRead, status_code=status.HTTP_201_CREATED)
def create_advance(
    tenant_id: UUID,
    payload: EmployeeAdvanceCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.write", scope="tenant")),
    ],
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)],
) -> EmployeeAdvanceRead:
    return service.create_advance(str(tenant_id), payload, context)


@router.patch("/advances/{advance_id}", response_model=EmployeeAdvanceRead)
def update_advance(
    tenant_id: UUID,
    advance_id: UUID,
    payload: EmployeeAdvanceUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.private.write", scope="tenant")),
    ],
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)],
) -> EmployeeAdvanceRead:
    return service.update_advance(str(tenant_id), str(advance_id), payload, context)


@router.get("/credentials", response_model=list[EmployeeCredentialRead])
def list_credentials(
    tenant_id: UUID,
    employee_id: UUID | None = Query(default=None),
    credential_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    active_on: date | None = Query(default=None),
    include_archived: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)] = None,
) -> list[EmployeeCredentialRead]:
    return service.list_credentials(
        str(tenant_id),
        EmployeeCredentialFilter(
            employee_id=str(employee_id) if employee_id else None,
            credential_type=credential_type,
            status=status_filter,
            active_on=active_on,
            include_archived=include_archived,
        ),
        context,
    )


@router.post("/credentials", response_model=EmployeeCredentialRead, status_code=status.HTTP_201_CREATED)
def create_credential(
    tenant_id: UUID,
    payload: EmployeeCredentialCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)],
) -> EmployeeCredentialRead:
    return service.create_credential(str(tenant_id), payload, context)


@router.patch("/credentials/{credential_id}", response_model=EmployeeCredentialRead)
def update_credential(
    tenant_id: UUID,
    credential_id: UUID,
    payload: EmployeeCredentialUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)],
) -> EmployeeCredentialRead:
    return service.update_credential(str(tenant_id), str(credential_id), payload, context)


@router.post("/credentials/{credential_id}/badge-output", response_model=EmployeeCredentialBadgeRead, status_code=status.HTTP_201_CREATED)
def issue_badge_output(
    tenant_id: UUID,
    credential_id: UUID,
    payload: EmployeeCredentialBadgeIssue,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeCompensationService, Depends(get_employee_compensation_service)],
) -> EmployeeCredentialBadgeRead:
    return service.issue_badge_output(str(tenant_id), str(credential_id), payload, context)


@router.get("/catalog/function-types", response_model=list[FunctionTypeRead])
def list_function_types(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)] = None,
) -> list[FunctionTypeRead]:
    return service.list_function_types(str(tenant_id), context)


@router.post("/catalog/bootstrap-sample-data", response_model=EmployeeCatalogBootstrapRead)
def bootstrap_sample_catalog_data(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> EmployeeCatalogBootstrapRead:
    if settings.env not in {"development", "test"}:
        from app.errors import ApiException

        raise ApiException(
            403,
            "employees.catalog.bootstrap_disabled",
            "errors.employees.catalog.bootstrap_not_allowed",
        )
    result = seed_sample_employee_catalogs(
        session,
        tenant_id=str(tenant_id),
        actor_user_id=context.user_id,
    )
    session.commit()
    return EmployeeCatalogBootstrapRead.model_validate(result)


@router.post("/catalog/function-types", response_model=FunctionTypeRead, status_code=status.HTTP_201_CREATED)
def create_function_type(
    tenant_id: UUID,
    payload: FunctionTypeCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)],
) -> FunctionTypeRead:
    return service.create_function_type(str(tenant_id), payload, context)


@router.patch("/catalog/function-types/{function_type_id}", response_model=FunctionTypeRead)
def update_function_type(
    tenant_id: UUID,
    function_type_id: UUID,
    payload: FunctionTypeUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)],
) -> FunctionTypeRead:
    return service.update_function_type(str(tenant_id), str(function_type_id), payload, context)


@router.get("/catalog/qualification-types", response_model=list[QualificationTypeRead])
def list_qualification_types(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)] = None,
) -> list[QualificationTypeRead]:
    return service.list_qualification_types(str(tenant_id), context)


@router.post("/catalog/qualification-types", response_model=QualificationTypeRead, status_code=status.HTTP_201_CREATED)
def create_qualification_type(
    tenant_id: UUID,
    payload: QualificationTypeCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)],
) -> QualificationTypeRead:
    return service.create_qualification_type(str(tenant_id), payload, context)


@router.patch("/catalog/qualification-types/{qualification_type_id}", response_model=QualificationTypeRead)
def update_qualification_type(
    tenant_id: UUID,
    qualification_type_id: UUID,
    payload: QualificationTypeUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)],
) -> QualificationTypeRead:
    return service.update_qualification_type(str(tenant_id), str(qualification_type_id), payload, context)


@router.get("/qualifications", response_model=list[EmployeeQualificationRead])
def list_employee_qualifications(
    tenant_id: UUID,
    employee_id: UUID | None = Query(default=None),
    record_kind: str | None = Query(default=None),
    qualification_type_id: UUID | None = Query(default=None),
    function_type_id: UUID | None = Query(default=None),
    include_archived: bool = Query(default=False),
    include_expired: bool = Query(default=False),
    valid_on: date | None = Query(default=None),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)] = None,
) -> list[EmployeeQualificationRead]:
    return service.list_employee_qualifications(
        str(tenant_id),
        context,
        EmployeeQualificationFilter(
            employee_id=str(employee_id) if employee_id else None,
            record_kind=record_kind,
            qualification_type_id=str(qualification_type_id) if qualification_type_id else None,
            function_type_id=str(function_type_id) if function_type_id else None,
            include_archived=include_archived,
            include_expired=include_expired,
            valid_on=valid_on,
        ),
    )


@router.post("/qualifications", response_model=EmployeeQualificationRead, status_code=status.HTTP_201_CREATED)
def create_employee_qualification(
    tenant_id: UUID,
    payload: EmployeeQualificationCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)],
) -> EmployeeQualificationRead:
    return service.create_employee_qualification(str(tenant_id), payload, context)


@router.get("/qualifications/{qualification_id}", response_model=EmployeeQualificationRead)
def get_employee_qualification(
    tenant_id: UUID,
    qualification_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)] = None,
) -> EmployeeQualificationRead:
    return service.get_employee_qualification(str(tenant_id), str(qualification_id), context)


@router.patch("/qualifications/{qualification_id}", response_model=EmployeeQualificationRead)
def update_employee_qualification(
    tenant_id: UUID,
    qualification_id: UUID,
    payload: EmployeeQualificationUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)],
) -> EmployeeQualificationRead:
    return service.update_employee_qualification(str(tenant_id), str(qualification_id), payload, context)


@router.get("/qualifications/{qualification_id}/proofs", response_model=list[EmployeeQualificationProofRead])
def list_employee_qualification_proofs(
    tenant_id: UUID,
    qualification_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)] = None,
) -> list[EmployeeQualificationProofRead]:
    return service.list_proofs(str(tenant_id), str(qualification_id), context)


@router.post(
    "/qualifications/{qualification_id}/proofs/uploads",
    response_model=EmployeeQualificationProofRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_employee_qualification_proof(
    tenant_id: UUID,
    qualification_id: UUID,
    payload: EmployeeQualificationProofUpload,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)],
) -> EmployeeQualificationProofRead:
    return service.upload_proof(str(tenant_id), str(qualification_id), payload, context)


@router.post(
    "/qualifications/{qualification_id}/proofs/links",
    response_model=EmployeeQualificationProofRead,
    status_code=status.HTTP_201_CREATED,
)
def link_employee_qualification_proof(
    tenant_id: UUID,
    qualification_id: UUID,
    payload: EmployeeQualificationProofLinkCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeQualificationService, Depends(get_employee_qualification_service)],
) -> EmployeeQualificationProofRead:
    return service.link_existing_proof(str(tenant_id), str(qualification_id), payload, context)


@router.get("/{employee_id}/notes", response_model=list[EmployeeNoteRead])
def list_employee_notes(
    tenant_id: UUID,
    employee_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeService, Depends(get_employee_service)] = None,
) -> list[EmployeeNoteRead]:
    return service.list_notes(str(tenant_id), str(employee_id), context)


@router.post("/{employee_id}/notes", response_model=EmployeeNoteRead, status_code=status.HTTP_201_CREATED)
def create_employee_note(
    tenant_id: UUID,
    employee_id: UUID,
    payload: EmployeeNoteCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeNoteRead:
    return service.create_note(str(tenant_id), str(employee_id), payload, context)


@router.patch("/{employee_id}/notes/{note_id}", response_model=EmployeeNoteRead)
def update_employee_note(
    tenant_id: UUID,
    employee_id: UUID,
    note_id: UUID,
    payload: EmployeeNoteUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeService, Depends(get_employee_service)],
) -> EmployeeNoteRead:
    return service.update_note(str(tenant_id), str(employee_id), str(note_id), payload, context)


@router.get("/{employee_id}/documents", response_model=list[EmployeeDocumentListItemRead])
def list_employee_documents(
    tenant_id: UUID,
    employee_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeFileService, Depends(get_employee_file_service)] = None,
) -> list[EmployeeDocumentListItemRead]:
    return service.list_documents(str(tenant_id), str(employee_id), context)


@router.get("/{employee_id}/photo", response_model=EmployeePhotoRead | None)
def get_employee_photo(
    tenant_id: UUID,
    employee_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ] = None,
    service: Annotated[EmployeeFileService, Depends(get_employee_file_service)] = None,
) -> EmployeePhotoRead | None:
    return service.get_profile_photo(str(tenant_id), str(employee_id), context)


@router.post("/{employee_id}/photo", response_model=EmployeePhotoRead, status_code=status.HTTP_201_CREATED)
def upload_employee_photo(
    tenant_id: UUID,
    employee_id: UUID,
    payload: EmployeePhotoUpload,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeFileService, Depends(get_employee_file_service)],
) -> EmployeePhotoRead:
    return service.upsert_profile_photo(str(tenant_id), str(employee_id), payload, context)


@router.post("/ops/import/dry-run", response_model=EmployeeImportDryRunResult)
def import_employees_dry_run(
    tenant_id: UUID,
    payload: EmployeeImportDryRunRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeOpsService, Depends(get_employee_ops_service)],
) -> EmployeeImportDryRunResult:
    return service.import_dry_run(str(tenant_id), payload, context)


@router.post("/ops/import/execute", response_model=EmployeeImportExecuteResult)
def import_employees_execute(
    tenant_id: UUID,
    payload: EmployeeImportExecuteRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeOpsService, Depends(get_employee_ops_service)],
) -> EmployeeImportExecuteResult:
    return service.execute_import(str(tenant_id), payload, context)


@router.post("/ops/export", response_model=EmployeeExportResult)
def export_employees(
    tenant_id: UUID,
    payload: EmployeeExportRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.read", scope="tenant")),
    ],
    service: Annotated[EmployeeOpsService, Depends(get_employee_ops_service)],
) -> EmployeeExportResult:
    return service.export_employees(str(tenant_id), payload, context)


@router.get("/{employee_id}/access-link", response_model=EmployeeAccessLinkRead)
def get_employee_access_link(
    tenant_id: UUID,
    employee_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeOpsService, Depends(get_employee_ops_service)],
) -> EmployeeAccessLinkRead:
    return service.get_access_link(str(tenant_id), str(employee_id), context)


@router.post("/{employee_id}/access-link/create-user", response_model=EmployeeAccessLinkRead, status_code=status.HTTP_201_CREATED)
def create_employee_access_user(
    tenant_id: UUID,
    employee_id: UUID,
    payload: EmployeeAccessCreateUserRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeOpsService, Depends(get_employee_ops_service)],
) -> EmployeeAccessLinkRead:
    return service.create_access_user(str(tenant_id), str(employee_id), payload, context)


@router.patch("/{employee_id}/access-link/user", response_model=EmployeeAccessLinkRead)
def update_employee_access_user(
    tenant_id: UUID,
    employee_id: UUID,
    payload: EmployeeAccessUpdateUserRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeOpsService, Depends(get_employee_ops_service)],
) -> EmployeeAccessLinkRead:
    return service.update_access_user(str(tenant_id), str(employee_id), payload, context)


@router.post("/{employee_id}/access-link/reset-password", response_model=EmployeeAccessLinkRead)
def reset_employee_access_user_password(
    tenant_id: UUID,
    employee_id: UUID,
    payload: EmployeeAccessResetPasswordRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeOpsService, Depends(get_employee_ops_service)],
) -> EmployeeAccessLinkRead:
    return service.reset_access_user_password(str(tenant_id), str(employee_id), payload, context)


@router.post("/{employee_id}/access-link/attach", response_model=EmployeeAccessLinkRead)
def attach_employee_access_user(
    tenant_id: UUID,
    employee_id: UUID,
    payload: EmployeeAccessAttachExistingRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeOpsService, Depends(get_employee_ops_service)],
) -> EmployeeAccessLinkRead:
    return service.attach_existing_user(str(tenant_id), str(employee_id), payload, context)


@router.post("/{employee_id}/access-link/detach", response_model=EmployeeAccessLinkRead)
def detach_employee_access_user(
    tenant_id: UUID,
    employee_id: UUID,
    payload: EmployeeAccessDetachRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeOpsService, Depends(get_employee_ops_service)],
) -> EmployeeAccessLinkRead:
    return service.detach_access_user(str(tenant_id), str(employee_id), payload, context)


@router.post("/{employee_id}/access-link/reconcile", response_model=EmployeeAccessLinkRead)
def reconcile_employee_access_user(
    tenant_id: UUID,
    employee_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("employees.employee.write", scope="tenant")),
    ],
    service: Annotated[EmployeeOpsService, Depends(get_employee_ops_service)],
) -> EmployeeAccessLinkRead:
    return service.reconcile_access_user(str(tenant_id), str(employee_id), context)
