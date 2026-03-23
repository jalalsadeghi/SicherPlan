"""HTTP API for reporting read models and exports."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.db.rls import rls_session_context
from app.db.session import get_db_session
from app.modules.iam.authz import (
    RequestAuthorizationContext,
    get_request_authorization_context,
    require_permission_only,
)
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import build_document_service
from app.modules.platform_services.integration_repository import SqlAlchemyIntegrationRepository
from app.modules.platform_services.storage import build_object_storage_adapter
from app.modules.reporting.repository import SqlAlchemyReportingRepository
from app.modules.reporting.schemas import (
    AbsenceVisibilityReportRow,
    ComplianceStatusReportRow,
    CustomerProfitabilityReportRow,
    CustomerRevenueReportRow,
    EmployeeActivityReportRow,
    FreeSundayStatusReportRow,
    InactivitySignalReportRow,
    NoticeReadStatsReportRow,
    PayrollBasisReportRow,
    ReportingDeliveryJobRead,
    ReportingDeliveryRequest,
    PlanningPerformanceReportRow,
    ReportingFilterBase,
    SecurityActivityReportRow,
    SubcontractorControlReportRow,
)
from app.modules.reporting.service import ReportingService
from app.rate_limit import REPORT_EXPORT_RULE, rate_limiter


router = APIRouter(prefix="/api/reporting/tenants/{tenant_id}", tags=["reporting"])


def get_reporting_service(
    session: Annotated[Session, Depends(get_db_session)],
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
) -> ReportingService:
    with rls_session_context(session, tenant_id=actor.tenant_id, bypass=actor.is_platform_admin):
        yield ReportingService(
            SqlAlchemyReportingRepository(session),
            document_service=build_document_service(
                SqlAlchemyDocumentRepository(session),
                storage=build_object_storage_adapter(settings),
            ),
            integration_repository=SqlAlchemyIntegrationRepository(session),
        )


@router.get("/employee-activity", response_model=list[EmployeeActivityReportRow])
def list_employee_activity(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("reporting.read")),
    ],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[EmployeeActivityReportRow]:
    return service.list_employee_activity(str(tenant_id), filters, actor)


@router.get("/customer-revenue", response_model=list[CustomerRevenueReportRow])
def list_customer_revenue(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("reporting.read")),
    ],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[CustomerRevenueReportRow]:
    return service.list_customer_revenue(str(tenant_id), filters, actor)


@router.get("/subcontractor-control", response_model=list[SubcontractorControlReportRow])
def list_subcontractor_control(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("reporting.read")),
    ],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[SubcontractorControlReportRow]:
    return service.list_subcontractor_control(str(tenant_id), filters, actor)


@router.get("/planning-performance", response_model=list[PlanningPerformanceReportRow])
def list_planning_performance(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("reporting.read")),
    ],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[PlanningPerformanceReportRow]:
    return service.list_planning_performance(str(tenant_id), filters, actor)


@router.get("/payroll-basis", response_model=list[PayrollBasisReportRow])
def list_payroll_basis(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("reporting.read")),
    ],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[PayrollBasisReportRow]:
    return service.list_payroll_basis(str(tenant_id), filters, actor)


@router.get("/customer-profitability", response_model=list[CustomerProfitabilityReportRow])
def list_customer_profitability(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("reporting.read")),
    ],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[CustomerProfitabilityReportRow]:
    return service.list_customer_profitability(str(tenant_id), filters, actor)


@router.get("/compliance-status", response_model=list[ComplianceStatusReportRow])
def list_compliance_status(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[RequestAuthorizationContext, Depends(require_permission_only("reporting.read"))],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[ComplianceStatusReportRow]:
    return service.list_compliance_status(str(tenant_id), filters, actor)


@router.get("/notice-read-stats", response_model=list[NoticeReadStatsReportRow])
def list_notice_read_stats(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[RequestAuthorizationContext, Depends(require_permission_only("reporting.read"))],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[NoticeReadStatsReportRow]:
    return service.list_notice_read_stats(str(tenant_id), filters, actor)


@router.get("/free-sundays", response_model=list[FreeSundayStatusReportRow])
def list_free_sundays(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[RequestAuthorizationContext, Depends(require_permission_only("reporting.read"))],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[FreeSundayStatusReportRow]:
    return service.list_free_sundays(str(tenant_id), filters, actor)


@router.get("/absence-visibility", response_model=list[AbsenceVisibilityReportRow])
def list_absence_visibility(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[RequestAuthorizationContext, Depends(require_permission_only("reporting.read"))],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[AbsenceVisibilityReportRow]:
    return service.list_absence_visibility(str(tenant_id), filters, actor)


@router.get("/inactivity-signals", response_model=list[InactivitySignalReportRow])
def list_inactivity_signals(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[RequestAuthorizationContext, Depends(require_permission_only("reporting.read"))],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[InactivitySignalReportRow]:
    return service.list_inactivity_signals(str(tenant_id), filters, actor)


@router.get("/security-activity", response_model=list[SecurityActivityReportRow])
def list_security_activity(
    tenant_id: UUID,
    filters: Annotated[ReportingFilterBase, Depends()],
    actor: Annotated[RequestAuthorizationContext, Depends(require_permission_only("reporting.read"))],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> list[SecurityActivityReportRow]:
    return service.list_security_activity(str(tenant_id), filters, actor)


@router.get("/{report_key}/export")
def export_report(
    tenant_id: UUID,
    report_key: str,
    filters: Annotated[ReportingFilterBase, Depends()],
    request: Request,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("reporting.export")),
    ],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> Response:
    rate_limiter.assert_allowed(
        REPORT_EXPORT_RULE,
        principal=f"{actor.tenant_id}:{actor.user_id or (request.client.host if request.client else 'anonymous')}",
    )
    envelope, csv_payload = service.export_csv(report_key, str(tenant_id), filters, actor)
    headers = {
        "Content-Disposition": f'attachment; filename="{report_key}.csv"',
        "X-Report-Generated-At": envelope.generated_at.isoformat(),
        "X-Report-Row-Count": str(envelope.row_count),
    }
    return Response(content=csv_payload, media_type="text/csv; charset=utf-8", headers=headers)


@router.get("/{report_key}/export-meta")
def get_report_export_meta(
    tenant_id: UUID,
    report_key: str,
    filters: Annotated[ReportingFilterBase, Depends()],
    request: Request,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("reporting.export")),
    ],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> JSONResponse:
    rate_limiter.assert_allowed(
        REPORT_EXPORT_RULE,
        principal=f"{actor.tenant_id}:{actor.user_id or (request.client.host if request.client else 'anonymous')}",
    )
    envelope, _ = service.export_csv(report_key, str(tenant_id), filters, actor)
    return JSONResponse(content=envelope.model_dump(mode="json"))


@router.post("/{report_key}/delivery-jobs", response_model=ReportingDeliveryJobRead)
def queue_report_delivery_job(
    tenant_id: UUID,
    report_key: str,
    payload: ReportingDeliveryRequest,
    filters: Annotated[ReportingFilterBase, Depends()],
    request: Request,
    actor: Annotated[RequestAuthorizationContext, Depends(require_permission_only("reporting.export"))],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
) -> ReportingDeliveryJobRead:
    rate_limiter.assert_allowed(
        REPORT_EXPORT_RULE,
        principal=f"{actor.tenant_id}:{actor.user_id or (request.client.host if request.client else 'anonymous')}",
    )
    return service.queue_export_delivery(report_key, str(tenant_id), filters, payload, actor)


@router.get("/delivery-jobs", response_model=list[ReportingDeliveryJobRead])
def list_report_delivery_jobs(
    tenant_id: UUID,
    actor: Annotated[RequestAuthorizationContext, Depends(require_permission_only("reporting.export"))],
    service: Annotated[ReportingService, Depends(get_reporting_service)],
    report_key: str | None = None,
    limit: int = 50,
) -> list[ReportingDeliveryJobRead]:
    return service.list_delivery_jobs(str(tenant_id), report_key=report_key, actor=actor, limit=limit)
