from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.modules.iam.audit_schemas import AuditEventRead


class SubcontractorInvoiceCheckListFilter(BaseModel):
    subcontractor_id: str | None = None
    status_code: str | None = None
    period_start: date | None = None
    period_end: date | None = None


class SubcontractorInvoiceCheckGenerateRequest(BaseModel):
    subcontractor_id: str = Field(min_length=1, max_length=120)
    period_start: date
    period_end: date


class SubcontractorInvoiceSubmissionUpdateRequest(BaseModel):
    submitted_invoice_ref: str | None = Field(default=None, max_length=120)
    submitted_invoice_amount: Decimal | None = None
    submitted_invoice_currency_code: str | None = Field(default=None, min_length=3, max_length=3)


class SubcontractorInvoiceCheckStatusRequest(BaseModel):
    status_code: str = Field(pattern="^(review_required|approved|exception|released)$")
    note_text: str | None = Field(default=None, max_length=1000)


class SubcontractorInvoiceCheckNoteCreate(BaseModel):
    note_text: str = Field(min_length=1, max_length=2000)
    note_kind_code: str = Field(default="note", pattern="^(note|exception|approval)$")


class SubcontractorInvoiceCheckLineRead(BaseModel):
    id: str
    assignment_id: str | None
    actual_record_id: str | None
    shift_id: str | None
    subcontractor_worker_id: str | None
    function_type_id: str | None
    qualification_type_id: str | None
    service_date: date
    label: str
    billing_unit_code: str
    assigned_minutes: int
    actual_minutes: int
    approved_minutes: int
    expected_quantity: Decimal
    actual_quantity: Decimal
    approved_quantity: Decimal
    unit_price: Decimal | None
    expected_amount: Decimal
    approved_amount: Decimal
    variance_amount: Decimal
    comparison_state_code: str
    variance_reason_codes_json: list[str] = Field(default_factory=list)
    source_ref_json: dict[str, object] = Field(default_factory=dict)


class SubcontractorInvoiceCheckNoteRead(BaseModel):
    id: str
    note_kind_code: str
    note_text: str
    created_at: datetime
    created_by_user_id: str | None


class SubcontractorInvoiceCheckListItem(BaseModel):
    id: str
    subcontractor_id: str
    check_no: str
    period_start: date
    period_end: date
    period_label: str
    status_code: str
    assigned_minutes_total: int
    actual_minutes_total: int
    approved_minutes_total: int
    expected_amount_total: Decimal
    approved_amount_total: Decimal
    comparison_variance_amount: Decimal
    submitted_invoice_ref: str | None
    submitted_invoice_amount: Decimal | None
    submitted_variance_amount: Decimal | None
    review_reason_codes_json: list[str] = Field(default_factory=list)
    last_generated_at: datetime | None


class SubcontractorInvoiceCheckRead(SubcontractorInvoiceCheckListItem):
    submitted_invoice_currency_code: str | None
    approved_at: datetime | None
    released_at: datetime | None
    metadata_json: dict[str, object] = Field(default_factory=dict)
    lines: list[SubcontractorInvoiceCheckLineRead] = Field(default_factory=list)
    notes: list[SubcontractorInvoiceCheckNoteRead] = Field(default_factory=list)


class SubcontractorPortalInvoiceCheckLineRead(BaseModel):
    id: str
    service_date: date
    label: str
    billing_unit_code: str
    approved_quantity: Decimal
    unit_price: Decimal | None
    approved_amount: Decimal
    variance_amount: Decimal
    variance_reason_codes_json: list[str] = Field(default_factory=list)


class SubcontractorPortalInvoiceCheckRead(BaseModel):
    id: str
    subcontractor_id: str
    period_label: str
    status: str
    submitted_invoice_ref: str | None = None
    approved_minutes: int
    approved_amount: Decimal
    submitted_invoice_amount: Decimal | None = None
    variance_amount: Decimal | None = None
    last_checked_at: datetime | None = None


class SubcontractorPortalInvoiceCheckDetailRead(SubcontractorPortalInvoiceCheckRead):
    period_start: date
    period_end: date
    released_at: datetime | None = None
    lines: list[SubcontractorPortalInvoiceCheckLineRead] = Field(default_factory=list)


class SubcontractorInvoiceCheckAuditRead(BaseModel):
    events: list[AuditEventRead] = Field(default_factory=list)
