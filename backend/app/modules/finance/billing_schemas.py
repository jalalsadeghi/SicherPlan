"""Pydantic contracts for finance customer timesheets and invoices."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TimesheetListFilter(BaseModel):
    customer_id: str | None = None
    order_id: str | None = None
    planning_record_id: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    release_state_code: str | None = None
    customer_visible_only: bool = False
    include_archived: bool = False


class TimesheetGenerateRequest(BaseModel):
    customer_id: str
    order_id: str | None = None
    planning_record_id: str | None = None
    period_start: date
    period_end: date
    billing_granularity_code: str = "shift"


class TimesheetReleaseRequest(BaseModel):
    customer_visible_flag: bool = True
    version_no: int


class TimesheetLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actual_record_id: str
    shift_id: str
    order_id: str | None
    planning_record_id: str | None
    sort_order: int
    service_date: date
    planning_mode_code: str | None
    line_label: str
    line_description: str
    planned_minutes: int
    actual_minutes: int
    billable_minutes: int
    quantity: float
    unit_code: str
    source_ref_json: dict[str, object] = Field(default_factory=dict)
    customer_safe_flag: bool
    personal_names_released: bool


class TimesheetListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    order_id: str | None
    planning_record_id: str | None
    billing_granularity_code: str
    period_start: date
    period_end: date
    headline: str
    total_planned_minutes: int
    total_actual_minutes: int
    total_billable_minutes: int
    release_state_code: str
    customer_visible_flag: bool
    released_at: datetime | None
    source_document_id: str | None
    version_no: int
    archived_at: datetime | None


class TimesheetRead(TimesheetListItem):
    source_hash: str
    summary: str | None
    metadata_json: dict[str, object] = Field(default_factory=dict)
    lines: list[TimesheetLineRead] = Field(default_factory=list)


class InvoiceListFilter(BaseModel):
    customer_id: str | None = None
    timesheet_id: str | None = None
    invoice_status_code: str | None = None
    issue_date_from: date | None = None
    issue_date_to: date | None = None
    delivery_status_code: str | None = None
    customer_visible_only: bool = False
    include_archived: bool = False


class InvoiceGenerateRequest(BaseModel):
    customer_id: str
    timesheet_id: str | None = None
    issue_date: date
    tax_rate: float = 19.0
    notes: str | None = None


class InvoiceIssueRequest(BaseModel):
    version_no: int


class InvoiceReleaseRequest(BaseModel):
    customer_visible_flag: bool = True
    version_no: int


class InvoiceDispatchRequest(BaseModel):
    endpoint_id: str | None = None
    version_no: int


class CustomerInvoiceLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timesheet_line_id: str | None
    source_actual_id: str | None
    rate_card_id: str | None
    rate_line_id: str | None
    surcharge_rule_id: str | None
    sort_order: int
    line_kind_code: str
    description: str
    quantity: float
    unit_code: str
    unit_price: float
    tax_rate: float
    net_amount: float
    tax_amount: float
    gross_amount: float
    source_ref_json: dict[str, object] = Field(default_factory=dict)


class CustomerInvoiceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    timesheet_id: str | None
    invoice_no: str
    period_start: date
    period_end: date
    issue_date: date
    due_date: date
    currency_code: str
    layout_code: str | None
    invoice_status_code: str
    subtotal_amount: float
    tax_amount: float
    total_amount: float
    customer_visible_flag: bool
    issued_at: datetime | None
    released_at: datetime | None
    dispatched_at: datetime | None
    source_document_id: str | None
    delivery_status_code: str
    version_no: int
    archived_at: datetime | None


class CustomerInvoiceRead(CustomerInvoiceListItem):
    billing_profile_id: str | None
    invoice_party_id: str | None
    job_id: str | None
    source_hash: str
    invoice_email: str | None
    dispatch_method_code: str | None
    e_invoice_enabled: bool
    leitweg_id: str | None
    payment_terms_days: int | None
    billing_profile_snapshot_json: dict[str, object] = Field(default_factory=dict)
    invoice_party_snapshot_json: dict[str, object] = Field(default_factory=dict)
    delivery_context_json: dict[str, object] = Field(default_factory=dict)
    notes: str | None
    lines: list[CustomerInvoiceLineRead] = Field(default_factory=list)
