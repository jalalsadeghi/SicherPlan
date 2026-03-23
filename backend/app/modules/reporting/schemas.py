"""Read-only reporting filters and DTOs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


ReportSortDirection = Literal["asc", "desc"]


class ReportingFilterBase(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    branch_id: str | None = None
    mandate_id: str | None = None
    customer_id: str | None = None
    order_id: str | None = None
    planning_record_id: str | None = None
    employee_id: str | None = None
    subcontractor_id: str | None = None
    actor_type_code: str | None = None
    rule_code: str | None = None
    document_type_key: str | None = None
    severity_code: str | None = None
    category_code: str | None = None
    result_status_code: str | None = None
    entity_type: str | None = None
    request_id: str | None = None
    inactivity_threshold_days: int | None = Field(default=None, ge=1, le=3650)
    free_sunday_threshold: int | None = Field(default=None, ge=0, le=5)
    planning_mode_code: str | None = None
    invoice_status_code: str | None = None
    export_state_code: str | None = None
    status_code: str | None = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0, le=10_000)
    sort_by: str | None = None
    sort_direction: ReportSortDirection = "desc"


class EmployeeActivityReportRow(BaseModel):
    tenant_id: str
    employee_id: str
    personnel_no: str
    display_name: str
    activity_month: date
    confirmed_shift_count: int
    unconfirmed_shift_count: int
    approved_actual_count: int
    payable_minutes_total: int
    login_count: int
    last_login_at: datetime | None
    application_count: int
    pending_application_count: int
    approved_absence_days: Decimal
    pending_absence_days: Decimal
    overtime_balance_minutes: int
    work_time_balance_minutes: int
    hire_date: date | None
    termination_date: date | None


class CustomerRevenueReportRow(BaseModel):
    tenant_id: str
    customer_id: str
    customer_number: str
    customer_name: str
    order_id: str | None
    order_no: str | None
    planning_record_id: str | None
    planning_record_name: str | None
    planning_mode_code: str | None
    invoice_id: str
    invoice_no: str
    issue_date: date
    due_date: date
    invoice_status_code: str
    delivery_status_code: str
    period_start: date
    period_end: date
    released_at: datetime | None
    timesheet_id: str | None
    timesheet_release_state_code: str | None
    actual_record_count: int
    billable_minutes_total: int
    payable_minutes_total: int
    subtotal_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    source_document_id: str | None


class SubcontractorControlReportRow(BaseModel):
    tenant_id: str
    subcontractor_id: str
    subcontractor_number: str
    subcontractor_name: str
    invoice_check_id: str
    check_no: str
    period_start: date
    period_end: date
    status_code: str
    released_shift_count: int
    assigned_shift_count: int
    actual_minutes_total: int
    approved_minutes_total: int
    attendance_marker_count: int
    variance_warning_count: int
    variance_review_count: int
    expected_amount_total: Decimal
    approved_amount_total: Decimal
    comparison_variance_amount: Decimal
    compliance_complete_worker_count: int
    compliance_gap_worker_count: int
    released_at: datetime | None
    approved_at: datetime | None


class PlanningPerformanceReportRow(BaseModel):
    tenant_id: str
    shift_id: str
    shift_plan_id: str
    planning_record_id: str
    order_id: str
    customer_id: str
    customer_number: str
    customer_name: str
    order_no: str
    planning_record_name: str
    planning_mode_code: str
    shift_date: date
    starts_at: datetime
    ends_at: datetime
    release_state: str
    target_qty_total: int
    min_qty_total: int
    assigned_qty_total: int
    confirmed_assignment_count: int
    approved_actual_count: int
    billable_minutes_total: int
    payable_minutes_total: int
    coverage_gap_qty: int
    fill_rate_ratio: Decimal


class PayrollBasisReportRow(BaseModel):
    tenant_id: str
    actual_record_id: str
    employee_id: str
    personnel_no: str
    display_name: str
    shift_id: str
    service_date: date
    payroll_region_code: str | None
    employment_type_code: str | None
    pay_cycle_code: str | None
    export_state_code: str
    approval_stage_code: str
    payable_minutes: int
    billable_minutes: int
    base_rate_resolved: Decimal
    allowance_amount_total: Decimal
    advance_outstanding_total: Decimal
    payroll_cost_basis_amount: Decimal
    export_batch_no: str | None
    export_generated_at: datetime | None
    payslip_archive_status_code: str | None


class CustomerProfitabilityReportRow(BaseModel):
    tenant_id: str
    customer_id: str
    customer_number: str
    customer_name: str
    order_id: str | None
    order_no: str | None
    planning_record_id: str | None
    planning_record_name: str | None
    service_month: date
    invoice_count: int
    revenue_net_amount: Decimal
    payroll_cost_basis_amount: Decimal
    allowance_cost_amount: Decimal
    expense_cost_amount: Decimal
    contribution_margin_amount: Decimal
    contribution_margin_ratio: Decimal


class ComplianceStatusReportRow(BaseModel):
    tenant_id: str
    actor_type_code: str
    actor_id: str
    actor_number: str
    actor_display_name: str
    employee_id: str | None = None
    subcontractor_id: str | None = None
    subcontractor_worker_id: str | None = None
    branch_id: str | None = None
    mandate_id: str | None = None
    source_entity_type: str
    source_entity_id: str
    rule_family_code: str
    rule_code: str
    rule_label: str
    document_type_key: str | None = None
    status_code: str
    severity_code: str
    release_relevant_flag: bool
    valid_until: date | None = None
    days_until_expiry: int | None = None
    proof_document_count: int | None = None


class NoticeReadStatsReportRow(BaseModel):
    tenant_id: str
    notice_id: str
    title: str
    language_code: str
    mandatory_acknowledgement: bool
    published_at: datetime | None = None
    publish_until: datetime | None = None
    audience_count: int
    opened_count: int
    acknowledged_count: int
    unread_count: int
    overdue_unread_count: int
    completion_ratio: Decimal
    last_opened_at: datetime | None = None
    last_acknowledged_at: datetime | None = None
    status_code: str
    severity_code: str


class FreeSundayStatusReportRow(BaseModel):
    tenant_id: str
    employee_id: str
    personnel_no: str
    display_name: str
    branch_id: str | None = None
    mandate_id: str | None = None
    service_month: date
    sunday_count_in_month: int
    worked_sunday_count: int
    free_sunday_count: int
    approved_absence_sunday_count: int
    threshold_days_or_count: int
    status_code: str
    severity_code: str


class AbsenceVisibilityReportRow(BaseModel):
    tenant_id: str
    absence_id: str
    employee_id: str
    personnel_no: str
    display_name: str
    branch_id: str | None = None
    mandate_id: str | None = None
    absence_type: str
    status_code: str
    starts_on: date
    ends_on: date
    quantity_days: Decimal
    approved_at: datetime | None = None
    approved_by_user_id: str | None = None


class InactivitySignalReportRow(BaseModel):
    tenant_id: str
    user_account_id: str
    actor_type_code: str
    actor_id: str | None = None
    actor_display_name: str
    role_keys: str
    account_status: str
    branch_id: str | None = None
    mandate_id: str | None = None
    last_login_at: datetime | None = None
    last_login_failure_at: datetime | None = None
    days_since_last_login: int | None = None
    inactivity_threshold_days: int
    status_code: str
    severity_code: str


class SecurityActivityReportRow(BaseModel):
    tenant_id: str
    source_table: str
    source_id: str
    occurred_at: datetime
    category_code: str
    severity_code: str
    result_status_code: str
    actor_user_id: str | None = None
    actor_display_name: str | None = None
    branch_id: str | None = None
    mandate_id: str | None = None
    request_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    event_type: str
    role_key: str | None = None
    scope_type: str | None = None
    summary_text: str
    trace_json: dict[str, object] = Field(default_factory=dict)


class ReportingDeliveryRequest(BaseModel):
    endpoint_id: str | None = None
    scheduled_for: datetime | None = None
    target_label: str | None = None
    target_address: str | None = None
    note_text: str | None = None


class ReportingDeliveryJobRead(BaseModel):
    job_id: str
    tenant_id: str
    report_key: str
    job_status: str
    requested_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    scheduled_for: datetime | None = None
    requested_by_user_id: str | None = None
    endpoint_id: str | None = None
    document_id: str | None = None
    document_title: str | None = None
    row_count: int
    target_label: str | None = None


class ReportExportEnvelope(BaseModel):
    report_key: str
    generated_at: datetime
    row_count: int
    applied_filters: dict[str, object]
