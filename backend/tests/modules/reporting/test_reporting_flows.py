from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal

from app.errors import ApiException
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
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
    PlanningPerformanceReportRow,
    ReportingDeliveryJobRead,
    ReportingDeliveryRequest,
    ReportingFilterBase,
    SecurityActivityReportRow,
    SubcontractorControlReportRow,
)
from app.modules.reporting.service import ReportingService


def _actor(*permissions: str, scopes: tuple[AuthenticatedRoleScope, ...] | None = None) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-reporting",
        user_id="user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"controller_qm"}),
        permission_keys=frozenset(permissions),
        scopes=scopes or (AuthenticatedRoleScope(role_key="controller_qm", scope_type="tenant"),),
        request_id="req-reporting",
    )


@dataclass
class _FakeReportingRepository:
    employee_rows: list[EmployeeActivityReportRow] = field(default_factory=list)
    revenue_rows: list[CustomerRevenueReportRow] = field(default_factory=list)
    subcontractor_rows: list[SubcontractorControlReportRow] = field(default_factory=list)
    planning_rows: list[PlanningPerformanceReportRow] = field(default_factory=list)
    payroll_rows: list[PayrollBasisReportRow] = field(default_factory=list)
    profitability_rows: list[CustomerProfitabilityReportRow] = field(default_factory=list)
    compliance_rows: list[ComplianceStatusReportRow] = field(default_factory=list)
    notice_rows: list[NoticeReadStatsReportRow] = field(default_factory=list)
    free_sunday_rows: list[FreeSundayStatusReportRow] = field(default_factory=list)
    absence_rows: list[AbsenceVisibilityReportRow] = field(default_factory=list)
    inactivity_rows: list[InactivitySignalReportRow] = field(default_factory=list)
    security_rows: list[SecurityActivityReportRow] = field(default_factory=list)
    delivery_jobs: list[ReportingDeliveryJobRead] = field(default_factory=list)
    calls: list[tuple[str, str, set[str] | None, set[str] | None]] = field(default_factory=list)

    def list_employee_activity(self, tenant_id: str, filters: ReportingFilterBase, *, allowed_customer_ids=None, allowed_subcontractor_ids=None):
        self.calls.append(("employee", tenant_id, allowed_customer_ids, allowed_subcontractor_ids))
        return self.employee_rows

    def list_customer_revenue(self, tenant_id: str, filters: ReportingFilterBase, *, allowed_customer_ids=None):
        self.calls.append(("revenue", tenant_id, allowed_customer_ids, None))
        rows = self.revenue_rows
        if allowed_customer_ids is not None:
            rows = [row for row in rows if row.customer_id in allowed_customer_ids]
        return rows

    def list_subcontractor_control(self, tenant_id: str, filters: ReportingFilterBase, *, allowed_subcontractor_ids=None):
        self.calls.append(("subcontractor", tenant_id, None, allowed_subcontractor_ids))
        rows = self.subcontractor_rows
        if allowed_subcontractor_ids is not None:
            rows = [row for row in rows if row.subcontractor_id in allowed_subcontractor_ids]
        return rows

    def list_planning_performance(self, tenant_id: str, filters: ReportingFilterBase, *, allowed_customer_ids=None):
        self.calls.append(("planning", tenant_id, allowed_customer_ids, None))
        rows = self.planning_rows
        if allowed_customer_ids is not None:
            rows = [row for row in rows if row.customer_id in allowed_customer_ids]
        return rows

    def list_payroll_basis(self, tenant_id: str, filters: ReportingFilterBase):
        self.calls.append(("payroll", tenant_id, None, None))
        return self.payroll_rows

    def list_customer_profitability(self, tenant_id: str, filters: ReportingFilterBase, *, allowed_customer_ids=None):
        self.calls.append(("profitability", tenant_id, allowed_customer_ids, None))
        rows = self.profitability_rows
        if allowed_customer_ids is not None:
            rows = [row for row in rows if row.customer_id in allowed_customer_ids]
        return rows

    def list_compliance_status(self, tenant_id: str, filters: ReportingFilterBase):
        self.calls.append(("compliance", tenant_id, None, None))
        return self.compliance_rows

    def list_notice_read_stats(self, tenant_id: str, filters: ReportingFilterBase):
        self.calls.append(("notice", tenant_id, None, None))
        return self.notice_rows

    def list_free_sundays(self, tenant_id: str, filters: ReportingFilterBase):
        self.calls.append(("free_sundays", tenant_id, None, None))
        return self.free_sunday_rows

    def list_absence_visibility(self, tenant_id: str, filters: ReportingFilterBase):
        self.calls.append(("absence", tenant_id, None, None))
        return self.absence_rows

    def list_inactivity_signals(self, tenant_id: str, filters: ReportingFilterBase):
        self.calls.append(("inactivity", tenant_id, None, None))
        return self.inactivity_rows

    def list_security_activity(self, tenant_id: str, filters: ReportingFilterBase):
        self.calls.append(("security", tenant_id, None, None))
        return self.security_rows

    def list_reporting_delivery_jobs(self, tenant_id: str, *, report_key: str | None = None, limit: int = 50):
        rows = [row for row in self.delivery_jobs if row.tenant_id == tenant_id]
        if report_key is not None:
            rows = [row for row in rows if row.report_key == report_key]
        return rows[:limit]


@dataclass
class _FakeDocumentRead:
    id: str
    title: str


@dataclass
class _FakeDocumentService:
    created_documents: list[tuple[str, str, dict[str, object]]] = field(default_factory=list)
    linked_documents: list[tuple[str, str, str]] = field(default_factory=list)

    def create_document(self, tenant_id: str, payload, actor):  # noqa: ANN001
        document = _FakeDocumentRead(id=f"doc-{len(self.created_documents) + 1}", title=payload.title)
        self.created_documents.append((tenant_id, payload.title, payload.metadata_json))
        return document

    def add_document_version(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        return None

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.linked_documents.append((tenant_id, document_id, payload.owner_id))
        return None


@dataclass
class _FakeEndpoint:
    id: str


@dataclass
class _FakeIntegrationRepository:
    jobs: list[object] = field(default_factory=list)
    endpoint: _FakeEndpoint | None = None

    def get_endpoint(self, tenant_id: str, endpoint_id: str):  # noqa: ANN001
        if self.endpoint and self.endpoint.id == endpoint_id:
            return self.endpoint
        return None

    def create_job_and_outbox(self, job, outbox_event):  # noqa: ANN001
        job.id = f"job-{len(self.jobs) + 1}"
        self.jobs.append((job, outbox_event))
        return job


class ReportingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _FakeReportingRepository(
            employee_rows=[
                EmployeeActivityReportRow(
                    tenant_id="tenant-1",
                    employee_id="employee-1",
                    personnel_no="EMP-1",
                    display_name="Max Muster",
                    activity_month=date(2026, 3, 1),
                    confirmed_shift_count=3,
                    unconfirmed_shift_count=1,
                    approved_actual_count=2,
                    payable_minutes_total=960,
                    login_count=7,
                    last_login_at=datetime(2026, 3, 9, 9, 0, tzinfo=UTC),
                    application_count=2,
                    pending_application_count=1,
                    approved_absence_days=Decimal("1.50"),
                    pending_absence_days=Decimal("0.50"),
                    overtime_balance_minutes=120,
                    work_time_balance_minutes=60,
                    hire_date=date(2025, 1, 1),
                    termination_date=None,
                )
            ],
            revenue_rows=[
                CustomerRevenueReportRow(
                    tenant_id="tenant-1",
                    customer_id="customer-1",
                    customer_number="C-1",
                    customer_name="Alpha",
                    order_id="order-1",
                    order_no="O-1",
                    planning_record_id="record-1",
                    planning_record_name="Nord",
                    planning_mode_code="site",
                    invoice_id="invoice-1",
                    invoice_no="INV-1",
                    issue_date=date(2026, 3, 10),
                    due_date=date(2026, 3, 24),
                    invoice_status_code="released",
                    delivery_status_code="queued",
                    period_start=date(2026, 3, 1),
                    period_end=date(2026, 3, 31),
                    released_at=datetime(2026, 3, 10, 10, 0, tzinfo=UTC),
                    timesheet_id="timesheet-1",
                    timesheet_release_state_code="released",
                    actual_record_count=2,
                    billable_minutes_total=900,
                    payable_minutes_total=840,
                    subtotal_amount=Decimal("1000.00"),
                    tax_amount=Decimal("190.00"),
                    total_amount=Decimal("1190.00"),
                    source_document_id="doc-1",
                ),
                CustomerRevenueReportRow(
                    tenant_id="tenant-1",
                    customer_id="customer-2",
                    customer_number="C-2",
                    customer_name="Beta",
                    order_id=None,
                    order_no=None,
                    planning_record_id=None,
                    planning_record_name=None,
                    planning_mode_code=None,
                    invoice_id="invoice-2",
                    invoice_no="INV-2",
                    issue_date=date(2026, 3, 12),
                    due_date=date(2026, 3, 26),
                    invoice_status_code="draft",
                    delivery_status_code="not_queued",
                    period_start=date(2026, 3, 1),
                    period_end=date(2026, 3, 31),
                    released_at=None,
                    timesheet_id=None,
                    timesheet_release_state_code=None,
                    actual_record_count=0,
                    billable_minutes_total=0,
                    payable_minutes_total=0,
                    subtotal_amount=Decimal("250.00"),
                    tax_amount=Decimal("47.50"),
                    total_amount=Decimal("297.50"),
                    source_document_id=None,
                ),
            ],
            subcontractor_rows=[
                SubcontractorControlReportRow(
                    tenant_id="tenant-1",
                    subcontractor_id="sub-1",
                    subcontractor_number="S-1",
                    subcontractor_name="Partner A",
                    invoice_check_id="check-1",
                    check_no="CHK-1",
                    period_start=date(2026, 3, 1),
                    period_end=date(2026, 3, 31),
                    status_code="released",
                    released_shift_count=4,
                    assigned_shift_count=4,
                    actual_minutes_total=1400,
                    approved_minutes_total=1380,
                    attendance_marker_count=4,
                    variance_warning_count=1,
                    variance_review_count=0,
                    expected_amount_total=Decimal("800.00"),
                    approved_amount_total=Decimal("790.00"),
                    comparison_variance_amount=Decimal("-10.00"),
                    compliance_complete_worker_count=3,
                    compliance_gap_worker_count=1,
                    released_at=datetime(2026, 3, 20, 11, 0, tzinfo=UTC),
                    approved_at=datetime(2026, 3, 19, 12, 0, tzinfo=UTC),
                )
            ],
            planning_rows=[
                PlanningPerformanceReportRow(
                    tenant_id="tenant-1",
                    shift_id="shift-1",
                    shift_plan_id="plan-1",
                    planning_record_id="record-1",
                    order_id="order-1",
                    customer_id="customer-1",
                    customer_number="C-1",
                    customer_name="Alpha",
                    order_no="O-1",
                    planning_record_name="Nord",
                    planning_mode_code="site",
                    shift_date=date(2026, 3, 10),
                    starts_at=datetime(2026, 3, 10, 8, 0, tzinfo=UTC),
                    ends_at=datetime(2026, 3, 10, 16, 0, tzinfo=UTC),
                    release_state="released",
                    target_qty_total=4,
                    min_qty_total=3,
                    assigned_qty_total=3,
                    confirmed_assignment_count=2,
                    approved_actual_count=2,
                    billable_minutes_total=900,
                    payable_minutes_total=840,
                    coverage_gap_qty=1,
                    fill_rate_ratio=Decimal("0.7500"),
                )
            ],
            payroll_rows=[
                PayrollBasisReportRow(
                    tenant_id="tenant-1",
                    actual_record_id="actual-1",
                    employee_id="employee-1",
                    personnel_no="EMP-1",
                    display_name="Max Muster",
                    shift_id="shift-1",
                    service_date=date(2026, 3, 10),
                    payroll_region_code="DE-BE",
                    employment_type_code="full_time",
                    pay_cycle_code="monthly",
                    export_state_code="generated",
                    approval_stage_code="finance_signed_off",
                    payable_minutes=480,
                    billable_minutes=450,
                    base_rate_resolved=Decimal("18.50"),
                    allowance_amount_total=Decimal("12.00"),
                    advance_outstanding_total=Decimal("40.00"),
                    payroll_cost_basis_amount=Decimal("160.00"),
                    export_batch_no="PAY-1",
                    export_generated_at=datetime(2026, 3, 20, 8, 0, tzinfo=UTC),
                    payslip_archive_status_code="active",
                )
            ],
            profitability_rows=[
                CustomerProfitabilityReportRow(
                    tenant_id="tenant-1",
                    customer_id="customer-1",
                    customer_number="C-1",
                    customer_name="Alpha",
                    order_id="order-1",
                    order_no="O-1",
                    planning_record_id="record-1",
                    planning_record_name="Nord",
                    service_month=date(2026, 3, 1),
                    invoice_count=1,
                    revenue_net_amount=Decimal("1000.00"),
                    payroll_cost_basis_amount=Decimal("600.00"),
                    allowance_cost_amount=Decimal("50.00"),
                    expense_cost_amount=Decimal("25.00"),
                    contribution_margin_amount=Decimal("375.00"),
                    contribution_margin_ratio=Decimal("0.3750"),
                )
            ],
            compliance_rows=[
                ComplianceStatusReportRow(
                    tenant_id="tenant-1",
                    actor_type_code="employee",
                    actor_id="employee-1",
                    actor_number="EMP-1",
                    actor_display_name="Max Muster",
                    employee_id="employee-1",
                    source_entity_type="hr.employee_qualification",
                    source_entity_id="qual-1",
                    rule_family_code="qualification_expiry",
                    rule_code="sa1",
                    rule_label="Sachkunde",
                    status_code="expiring",
                    severity_code="warning",
                    release_relevant_flag=True,
                    valid_until=date(2026, 4, 1),
                    days_until_expiry=12,
                    proof_document_count=1,
                )
            ],
            notice_rows=[
                NoticeReadStatsReportRow(
                    tenant_id="tenant-1",
                    notice_id="notice-1",
                    title="Pflichtunterweisung",
                    language_code="de",
                    mandatory_acknowledgement=True,
                    published_at=datetime(2026, 3, 1, 8, 0, tzinfo=UTC),
                    publish_until=datetime(2026, 3, 31, 23, 0, tzinfo=UTC),
                    audience_count=10,
                    opened_count=8,
                    acknowledged_count=7,
                    unread_count=2,
                    overdue_unread_count=0,
                    completion_ratio=Decimal("0.8000"),
                    last_opened_at=datetime(2026, 3, 10, 8, 0, tzinfo=UTC),
                    last_acknowledged_at=datetime(2026, 3, 11, 8, 0, tzinfo=UTC),
                    status_code="open",
                    severity_code="warning",
                )
            ],
            free_sunday_rows=[
                FreeSundayStatusReportRow(
                    tenant_id="tenant-1",
                    employee_id="employee-1",
                    personnel_no="EMP-1",
                    display_name="Max Muster",
                    branch_id="branch-1",
                    mandate_id="mandate-1",
                    service_month=date(2026, 3, 1),
                    sunday_count_in_month=5,
                    worked_sunday_count=4,
                    free_sunday_count=1,
                    approved_absence_sunday_count=0,
                    threshold_days_or_count=1,
                    status_code="compliant",
                    severity_code="info",
                )
            ],
            absence_rows=[
                AbsenceVisibilityReportRow(
                    tenant_id="tenant-1",
                    absence_id="absence-1",
                    employee_id="employee-1",
                    personnel_no="EMP-1",
                    display_name="Max Muster",
                    branch_id="branch-1",
                    mandate_id="mandate-1",
                    absence_type="vacation",
                    status_code="approved",
                    starts_on=date(2026, 3, 15),
                    ends_on=date(2026, 3, 20),
                    quantity_days=Decimal("5.00"),
                    approved_at=datetime(2026, 3, 1, 9, 0, tzinfo=UTC),
                    approved_by_user_id="lead-1",
                )
            ],
            inactivity_rows=[
                InactivitySignalReportRow(
                    tenant_id="tenant-1",
                    user_account_id="user-2",
                    actor_type_code="employee",
                    actor_id="employee-2",
                    actor_display_name="Erika Beispiel",
                    role_keys="employee_user",
                    account_status="active",
                    branch_id="branch-1",
                    mandate_id="mandate-1",
                    last_login_at=datetime(2026, 2, 1, 10, 0, tzinfo=UTC),
                    last_login_failure_at=None,
                    days_since_last_login=40,
                    inactivity_threshold_days=30,
                    status_code="inactive",
                    severity_code="warning",
                )
            ],
            security_rows=[
                SecurityActivityReportRow(
                    tenant_id="tenant-1",
                    source_table="audit.login_event",
                    source_id="login-1",
                    occurred_at=datetime(2026, 3, 12, 10, 0, tzinfo=UTC),
                    category_code="login_failure",
                    severity_code="warning",
                    result_status_code="failure",
                    actor_user_id=None,
                    actor_display_name="max@example.com",
                    request_id="req-1",
                    entity_type="iam.user_account",
                    entity_id="user-2",
                    event_type="iam.auth.login",
                    summary_text="invalid_credentials",
                )
            ],
            delivery_jobs=[
                ReportingDeliveryJobRead(
                    job_id="job-1",
                    tenant_id="tenant-1",
                    report_key="compliance-status",
                    job_status="requested",
                    requested_at=datetime(2026, 3, 20, 8, 0, tzinfo=UTC),
                    row_count=1,
                )
            ],
        )
        self.document_service = _FakeDocumentService()
        self.integration_repository = _FakeIntegrationRepository(endpoint=_FakeEndpoint(id="endpoint-1"))
        self.service = ReportingService(
            self.repo,
            document_service=self.document_service,
            integration_repository=self.integration_repository,
        )

    def test_customer_scope_filters_revenue_rows(self) -> None:
        actor = _actor(
            "reporting.read",
            scopes=(AuthenticatedRoleScope(role_key="controller_qm", scope_type="customer", customer_id="customer-1"),),
        )
        rows = self.service.list_customer_revenue("tenant-1", ReportingFilterBase(), actor)
        self.assertEqual(1, len(rows))
        self.assertEqual("customer-1", rows[0].customer_id)
        self.assertEqual(("revenue", "tenant-1", {"customer-1"}, None), self.repo.calls[-1])

    def test_subcontractor_scope_filters_control_rows(self) -> None:
        actor = _actor(
            "reporting.read",
            scopes=(AuthenticatedRoleScope(role_key="controller_qm", scope_type="subcontractor", subcontractor_id="sub-1"),),
        )
        rows = self.service.list_subcontractor_control("tenant-1", ReportingFilterBase(), actor)
        self.assertEqual(1, len(rows))
        self.assertEqual("sub-1", rows[0].subcontractor_id)
        self.assertEqual(("subcontractor", "tenant-1", None, {"sub-1"}), self.repo.calls[-1])

    def test_export_csv_matches_report_contract(self) -> None:
        actor = _actor("reporting.read", "reporting.export")
        envelope, csv_payload = self.service.export_csv("customer-profitability", "tenant-1", ReportingFilterBase(), actor)
        self.assertEqual("customer-profitability", envelope.report_key)
        self.assertEqual(1, envelope.row_count)
        self.assertIn("customer_id", csv_payload)
        self.assertIn("contribution_margin_amount", csv_payload)
        self.assertIn("customer-1", csv_payload)

    def test_payroll_basis_and_planning_performance_are_exposed(self) -> None:
        actor = _actor("reporting.read")
        payroll_rows = self.service.list_payroll_basis("tenant-1", ReportingFilterBase(), actor)
        planning_rows = self.service.list_planning_performance("tenant-1", ReportingFilterBase(), actor)
        self.assertEqual("generated", payroll_rows[0].export_state_code)
        self.assertEqual(Decimal("0.7500"), planning_rows[0].fill_rate_ratio)

    def test_unknown_report_export_is_rejected(self) -> None:
        actor = _actor("reporting.read", "reporting.export")
        with self.assertRaises(ApiException) as ctx:
            self.service.export_csv("does-not-exist", "tenant-1", ReportingFilterBase(), actor)
        self.assertEqual("reporting.report.not_found", ctx.exception.code)

    def test_compliance_and_security_reports_are_exposed(self) -> None:
        actor = _actor("reporting.read")
        compliance_rows = self.service.list_compliance_status("tenant-1", ReportingFilterBase(), actor)
        security_rows = self.service.list_security_activity("tenant-1", ReportingFilterBase(), actor)
        self.assertEqual("sa1", compliance_rows[0].rule_code)
        self.assertEqual("login_failure", security_rows[0].category_code)

    def test_threshold_overrides_recompute_free_sunday_and_inactivity_states(self) -> None:
        actor = _actor("reporting.read")
        sunday_rows = self.service.list_free_sundays(
            "tenant-1",
            ReportingFilterBase(free_sunday_threshold=2),
            actor,
        )
        inactivity_rows = self.service.list_inactivity_signals(
            "tenant-1",
            ReportingFilterBase(inactivity_threshold_days=50),
            actor,
        )
        self.assertEqual(2, sunday_rows[0].threshold_days_or_count)
        self.assertEqual("non_compliant", sunday_rows[0].status_code)
        self.assertEqual(50, inactivity_rows[0].inactivity_threshold_days)
        self.assertEqual("active", inactivity_rows[0].status_code)

    def test_delivery_hook_creates_document_and_job_for_supported_report(self) -> None:
        actor = _actor("reporting.read", "reporting.export")
        job = self.service.queue_export_delivery(
            "compliance-status",
            "tenant-1",
            ReportingFilterBase(),
            ReportingDeliveryRequest(endpoint_id="endpoint-1", target_label="QM inbox"),
            actor,
        )
        self.assertEqual("compliance-status", job.report_key)
        self.assertEqual(1, len(self.integration_repository.jobs))
        self.assertEqual(1, len(self.document_service.created_documents))

    def test_delivery_hook_rejects_unsupported_report(self) -> None:
        actor = _actor("reporting.read", "reporting.export")
        with self.assertRaises(ApiException) as ctx:
            self.service.queue_export_delivery(
                "customer-revenue",
                "tenant-1",
                ReportingFilterBase(),
                ReportingDeliveryRequest(),
                actor,
            )
        self.assertEqual("reporting.delivery.report_not_supported", ctx.exception.code)
