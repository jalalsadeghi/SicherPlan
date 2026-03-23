"""Pydantic contracts for finance actual bridge, approval, and reconciliation flows."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.iam.audit_schemas import AuditEventRead


class ActualRecordDiscrepancyIssueRead(BaseModel):
    code: str
    severity: str
    message_key: str
    attendance_record_id: str | None = None
    source_event_ids: list[str] = Field(default_factory=list)
    details: dict[str, object] = Field(default_factory=dict)


class ActualRecordListFilter(BaseModel):
    shift_id: str | None = None
    assignment_id: str | None = None
    employee_id: str | None = None
    subcontractor_worker_id: str | None = None
    discrepancy_only: bool = False
    current_only: bool = True
    include_archived: bool = False
    approval_stage_code: str | None = None


class ActualApprovalActionRequest(BaseModel):
    note_text: str | None = Field(default=None, max_length=1000)


class ActualReconciliationCreate(BaseModel):
    reconciliation_kind_code: str
    reason_code: str
    note_text: str | None = Field(default=None, max_length=1000)
    payroll_minutes_delta: int = 0
    billable_minutes_delta: int = 0
    customer_adjustment_minutes_delta: int = 0
    replacement_actor_type_code: str | None = None
    replacement_employee_id: str | None = None
    replacement_subcontractor_worker_id: str | None = None
    source_ref_json: dict[str, object] = Field(default_factory=dict)


class ActualAllowanceCreate(BaseModel):
    line_type_code: str
    reason_code: str
    quantity: float = 1
    unit_code: str | None = None
    amount_total: float
    currency_code: str = "EUR"
    source_ref_json: dict[str, object] = Field(default_factory=dict)
    note_text: str | None = Field(default=None, max_length=1000)


class ActualExpenseCreate(BaseModel):
    expense_type_code: str
    reason_code: str
    quantity: float = 1
    unit_code: str | None = None
    amount_total: float
    currency_code: str = "EUR"
    source_ref_json: dict[str, object] = Field(default_factory=dict)
    note_text: str | None = Field(default=None, max_length=1000)


class ActualCommentCreate(BaseModel):
    visibility_code: str = "finance_only"
    note_text: str = Field(max_length=2000)


class ActualApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    stage_code: str
    actor_scope_code: str
    note_text: str | None
    source_ref_json: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    created_by_user_id: str | None


class ActualReconciliationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reconciliation_kind_code: str
    reason_code: str
    note_text: str | None
    payroll_minutes_delta: int
    billable_minutes_delta: int
    customer_adjustment_minutes_delta: int
    replacement_actor_type_code: str | None
    replacement_employee_id: str | None
    replacement_subcontractor_worker_id: str | None
    source_ref_json: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    created_by_user_id: str | None


class ActualAllowanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    line_type_code: str
    reason_code: str
    quantity: float
    unit_code: str | None
    amount_total: float
    currency_code: str
    source_ref_json: dict[str, object] = Field(default_factory=dict)
    note_text: str | None
    created_at: datetime
    created_by_user_id: str | None


class ActualExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    expense_type_code: str
    reason_code: str
    quantity: float
    unit_code: str | None
    amount_total: float
    currency_code: str
    source_ref_json: dict[str, object] = Field(default_factory=dict)
    note_text: str | None
    created_at: datetime
    created_by_user_id: str | None


class ActualCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    visibility_code: str
    note_text: str
    created_at: datetime
    created_by_user_id: str | None


class ActualRecordListItem(BaseModel):
    id: str
    assignment_id: str
    shift_id: str
    attendance_record_id: str | None
    actor_type_code: str
    employee_id: str | None
    subcontractor_worker_id: str | None
    planned_start_at: datetime | None
    planned_end_at: datetime | None
    actual_start_at: datetime | None
    actual_end_at: datetime | None
    payable_minutes: int
    billable_minutes: int
    discrepancy_state_code: str
    discrepancy_codes_json: list[str] = Field(default_factory=list)
    derivation_status_code: str
    approval_stage_code: str
    is_current: bool
    derived_at: datetime


class ActualRecordRead(ActualRecordListItem):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    planned_break_minutes: int
    actual_break_minutes: int
    customer_adjustment_minutes: int
    discrepancy_details_json: dict[str, object] = Field(default_factory=dict)
    discrepancies: list[ActualRecordDiscrepancyIssueRead] = Field(default_factory=list)
    superseded_at: datetime | None
    superseded_by_actual_id: str | None
    status: str
    archived_at: datetime | None
    version_no: int
    created_at: datetime
    updated_at: datetime
    approvals: list[ActualApprovalRead] = Field(default_factory=list)
    reconciliations: list[ActualReconciliationRead] = Field(default_factory=list)
    allowances: list[ActualAllowanceRead] = Field(default_factory=list)
    expenses: list[ActualExpenseRead] = Field(default_factory=list)
    comments: list[ActualCommentRead] = Field(default_factory=list)
    audit_history: list[AuditEventRead] = Field(default_factory=list)
