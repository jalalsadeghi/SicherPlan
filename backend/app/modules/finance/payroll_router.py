"""HTTP API for finance payroll configuration, exports, and archive flows."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.finance.payroll_repository import SqlAlchemyPayrollRepository
from app.modules.finance.payroll_schemas import (
    EmployeePayProfileCreate,
    EmployeePayProfileFilter,
    EmployeePayProfileRead,
    EmployeePayProfileUpdate,
    PayrollActualResolutionRead,
    PayrollExportBatchFilter,
    PayrollExportBatchGenerate,
    PayrollExportBatchListItem,
    PayrollExportBatchRead,
    PayrollPayslipArchiveCreate,
    PayrollPayslipArchiveFilter,
    PayrollPayslipArchiveRead,
    PayrollReconciliationFilter,
    PayrollReconciliationRowRead,
    PayrollSurchargeRuleCreate,
    PayrollTariffRateCreate,
    PayrollTariffTableCreate,
    PayrollTariffTableFilter,
    PayrollTariffTableListItem,
    PayrollTariffTableRead,
    PayrollTariffTableUpdate,
)
from app.modules.finance.payroll_service import PayrollService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization
from app.modules.platform_services.docs_router import get_document_service
from app.modules.platform_services.integration_repository import SqlAlchemyIntegrationRepository


router = APIRouter(prefix="/api/finance/tenants/{tenant_id}/payroll", tags=["finance-payroll"])


def get_payroll_service(
    session: Annotated[Session, Depends(get_db_session)],
):
    return PayrollService(
        repository=SqlAlchemyPayrollRepository(session),
        integration_repository=SqlAlchemyIntegrationRepository(session),
        document_service=get_document_service(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.get("/tariff-tables", response_model=list[PayrollTariffTableListItem])
def list_tariff_tables(
    tenant_id: UUID,
    filters: Annotated[PayrollTariffTableFilter, Depends()],
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.read", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> list[PayrollTariffTableListItem]:
    return service.list_tariff_tables(str(tenant_id), filters, actor)


@router.post("/tariff-tables", response_model=PayrollTariffTableRead, status_code=status.HTTP_201_CREATED)
def create_tariff_table(
    tenant_id: UUID,
    payload: PayrollTariffTableCreate,
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.write", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> PayrollTariffTableRead:
    return service.create_tariff_table(str(tenant_id), payload, actor)


@router.put("/tariff-tables/{tariff_table_id}", response_model=PayrollTariffTableRead)
def update_tariff_table(
    tenant_id: UUID,
    tariff_table_id: UUID,
    payload: PayrollTariffTableUpdate,
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.write", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> PayrollTariffTableRead:
    return service.update_tariff_table(str(tenant_id), str(tariff_table_id), payload, actor)


@router.post("/tariff-tables/{tariff_table_id}/rates", response_model=PayrollTariffTableRead, status_code=status.HTTP_201_CREATED)
def add_tariff_rate(
    tenant_id: UUID,
    tariff_table_id: UUID,
    payload: PayrollTariffRateCreate,
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.write", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> PayrollTariffTableRead:
    return service.add_tariff_rate(str(tenant_id), str(tariff_table_id), payload, actor)


@router.post("/tariff-tables/{tariff_table_id}/surcharge-rules", response_model=PayrollTariffTableRead, status_code=status.HTTP_201_CREATED)
def add_surcharge_rule(
    tenant_id: UUID,
    tariff_table_id: UUID,
    payload: PayrollSurchargeRuleCreate,
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.write", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> PayrollTariffTableRead:
    return service.add_surcharge_rule(str(tenant_id), str(tariff_table_id), payload, actor)


@router.get("/pay-profiles", response_model=list[EmployeePayProfileRead])
def list_pay_profiles(
    tenant_id: UUID,
    filters: Annotated[EmployeePayProfileFilter, Depends()],
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.read", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> list[EmployeePayProfileRead]:
    return service.list_employee_pay_profiles(str(tenant_id), filters, actor)


@router.post("/pay-profiles", response_model=EmployeePayProfileRead, status_code=status.HTTP_201_CREATED)
def create_pay_profile(
    tenant_id: UUID,
    payload: EmployeePayProfileCreate,
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.write", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> EmployeePayProfileRead:
    return service.create_employee_pay_profile(str(tenant_id), payload, actor)


@router.put("/pay-profiles/{profile_id}", response_model=EmployeePayProfileRead)
def update_pay_profile(
    tenant_id: UUID,
    profile_id: UUID,
    payload: EmployeePayProfileUpdate,
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.write", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> EmployeePayProfileRead:
    return service.update_employee_pay_profile(str(tenant_id), str(profile_id), payload, actor)


@router.get("/resolve/actuals/{actual_record_id}", response_model=PayrollActualResolutionRead)
def resolve_actual(
    tenant_id: UUID,
    actual_record_id: UUID,
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.read", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> PayrollActualResolutionRead:
    return service.resolve_actual(str(tenant_id), str(actual_record_id), actor)


@router.get("/export-batches", response_model=list[PayrollExportBatchListItem])
def list_export_batches(
    tenant_id: UUID,
    filters: Annotated[PayrollExportBatchFilter, Depends()],
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.read", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> list[PayrollExportBatchListItem]:
    return service.list_export_batches(str(tenant_id), filters, actor)


@router.post("/export-batches", response_model=PayrollExportBatchRead, status_code=status.HTTP_201_CREATED)
def generate_export_batch(
    tenant_id: UUID,
    payload: PayrollExportBatchGenerate,
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.export", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> PayrollExportBatchRead:
    return service.generate_export_batch(str(tenant_id), payload, actor)


@router.get("/export-batches/{batch_id}", response_model=PayrollExportBatchRead)
def get_export_batch(
    tenant_id: UUID,
    batch_id: UUID,
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.read", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> PayrollExportBatchRead:
    return service.get_export_batch(str(tenant_id), str(batch_id), actor)


@router.get("/payslip-archives", response_model=list[PayrollPayslipArchiveRead])
def list_payslip_archives(
    tenant_id: UUID,
    filters: Annotated[PayrollPayslipArchiveFilter, Depends()],
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.read", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> list[PayrollPayslipArchiveRead]:
    return service.list_payslip_archives(str(tenant_id), filters, actor)


@router.post("/payslip-archives", response_model=PayrollPayslipArchiveRead, status_code=status.HTTP_201_CREATED)
def archive_payslip(
    tenant_id: UUID,
    payload: PayrollPayslipArchiveCreate,
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.write", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> PayrollPayslipArchiveRead:
    return service.archive_payslip(str(tenant_id), payload, actor)


@router.get("/reconciliation", response_model=list[PayrollReconciliationRowRead])
def list_reconciliation_rows(
    tenant_id: UUID,
    filters: Annotated[PayrollReconciliationFilter, Depends()],
    actor: Annotated[RequestAuthorizationContext, Depends(require_authorization("finance.payroll.read", scope="tenant"))],
    service: Annotated[PayrollService, Depends(get_payroll_service)],
) -> list[PayrollReconciliationRowRead]:
    return service.list_reconciliation_rows(str(tenant_id), filters, actor)
