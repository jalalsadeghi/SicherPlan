"""Pydantic contracts for finance payroll configuration, export, and archive flows."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PayrollTariffTableFilter(BaseModel):
    region_code: str | None = None
    status: str | None = None
    active_on: date | None = None
    include_archived: bool = False


class PayrollTariffTableCreate(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=255)
    region_code: str = Field(min_length=1, max_length=32)
    status: str = "draft"
    effective_from: date
    effective_until: date | None = None
    notes: str | None = None


class PayrollTariffTableUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    region_code: str | None = Field(default=None, min_length=1, max_length=32)
    status: str | None = None
    effective_from: date | None = None
    effective_until: date | None = None
    notes: str | None = None
    version_no: int


class PayrollTariffRateCreate(BaseModel):
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    employment_type_code: str | None = None
    pay_unit_code: str = "hour"
    currency_code: str = "EUR"
    base_amount: float
    payroll_code: str | None = None
    notes: str | None = None


class PayrollSurchargeRuleCreate(BaseModel):
    surcharge_type_code: str
    custom_code: str | None = None
    weekday_mask: int = 127
    start_minute_local: int = 0
    end_minute_local: int = 1440
    holiday_region_code: str | None = None
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    employment_type_code: str | None = None
    percent_value: float | None = None
    fixed_amount: float | None = None
    currency_code: str | None = None
    payroll_code: str | None = None
    notes: str | None = None


class PayrollTariffRateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    function_type_id: str | None
    qualification_type_id: str | None
    employment_type_code: str | None
    pay_unit_code: str
    currency_code: str
    base_amount: float
    payroll_code: str | None
    notes: str | None
    version_no: int


class PayrollSurchargeRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    surcharge_type_code: str
    custom_code: str | None
    weekday_mask: int
    start_minute_local: int
    end_minute_local: int
    holiday_region_code: str | None
    function_type_id: str | None
    qualification_type_id: str | None
    employment_type_code: str | None
    percent_value: float | None
    fixed_amount: float | None
    currency_code: str | None
    payroll_code: str | None
    notes: str | None
    version_no: int


class PayrollTariffTableListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    title: str
    region_code: str
    status: str
    effective_from: date
    effective_until: date | None
    version_no: int
    archived_at: datetime | None


class PayrollTariffTableRead(PayrollTariffTableListItem):
    rates: list[PayrollTariffRateRead] = Field(default_factory=list)
    surcharge_rules: list[PayrollSurchargeRuleRead] = Field(default_factory=list)
    notes: str | None = None


class EmployeePayProfileFilter(BaseModel):
    employee_id: str | None = None
    active_on: date | None = None
    include_archived: bool = False


class EmployeePayProfileCreate(BaseModel):
    employee_id: str
    tariff_table_id: str | None = None
    payroll_region_code: str
    employment_type_code: str
    pay_cycle_code: str = "monthly"
    pay_unit_code: str = "hour"
    currency_code: str = "EUR"
    export_employee_code: str | None = None
    cost_center_code: str | None = None
    base_rate_override: float | None = None
    override_reason: str | None = None
    effective_from: date
    effective_until: date | None = None
    notes: str | None = None


class EmployeePayProfileUpdate(BaseModel):
    tariff_table_id: str | None = None
    payroll_region_code: str | None = None
    employment_type_code: str | None = None
    pay_cycle_code: str | None = None
    pay_unit_code: str | None = None
    currency_code: str | None = None
    export_employee_code: str | None = None
    cost_center_code: str | None = None
    base_rate_override: float | None = None
    override_reason: str | None = None
    effective_from: date | None = None
    effective_until: date | None = None
    notes: str | None = None
    version_no: int


class EmployeePayProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_id: str
    tariff_table_id: str | None
    payroll_region_code: str
    employment_type_code: str
    pay_cycle_code: str
    pay_unit_code: str
    currency_code: str
    export_employee_code: str | None
    cost_center_code: str | None
    base_rate_override: float | None
    override_reason: str | None
    effective_from: date
    effective_until: date | None
    notes: str | None
    version_no: int
    archived_at: datetime | None


class PayrollResolvedAllowanceRead(BaseModel):
    source: str
    code: str
    amount: float
    currency_code: str
    details: dict[str, object] = Field(default_factory=dict)


class PayrollResolvedAdvanceRead(BaseModel):
    advance_no: str
    outstanding_amount: float
    currency_code: str
    status: str


class PayrollResolvedTimeAccountRead(BaseModel):
    account_type: str
    balance_minutes: int
    unit_code: str


class PayrollResolvedSurchargeRead(BaseModel):
    rule_id: str
    surcharge_type_code: str
    pay_code: str
    percent_value: float | None = None
    fixed_amount: float | None = None
    amount_total: float
    currency_code: str


class PayrollActualResolutionRead(BaseModel):
    actual_record_id: str
    employee_id: str
    pay_profile_id: str | None
    tariff_table_id: str | None
    tariff_rate_id: str | None
    pay_code: str
    quantity: float
    unit_code: str
    base_amount: float
    currency_code: str
    minutes_basis: int
    allowances: list[PayrollResolvedAllowanceRead] = Field(default_factory=list)
    advances: list[PayrollResolvedAdvanceRead] = Field(default_factory=list)
    time_accounts: list[PayrollResolvedTimeAccountRead] = Field(default_factory=list)
    surcharges: list[PayrollResolvedSurchargeRead] = Field(default_factory=list)
    source_ref_json: dict[str, object] = Field(default_factory=dict)


class PayrollExportBatchFilter(BaseModel):
    provider_key: str | None = None
    status: str | None = None
    period_start: date | None = None
    period_end: date | None = None


class PayrollExportBatchGenerate(BaseModel):
    provider_key: str
    period_start: date
    period_end: date
    endpoint_id: str | None = None
    notes: str | None = None


class PayrollExportItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actual_record_id: str
    employee_id: str | None
    pay_code: str
    description: str | None
    quantity: float
    unit_code: str
    amount_total: float
    currency_code: str
    payload_json: dict[str, object] = Field(default_factory=dict)
    source_ref_json: dict[str, object] = Field(default_factory=dict)


class PayrollExportBatchListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    batch_no: str
    provider_key: str
    status: str
    period_start: date
    period_end: date
    item_count: int
    total_amount: float
    currency_code: str
    generated_at: datetime | None
    queued_at: datetime | None
    dispatched_at: datetime | None


class PayrollExportBatchRead(PayrollExportBatchListItem):
    endpoint_id: str | None
    job_id: str | None
    source_hash: str
    notes: str | None
    version_no: int
    items: list[PayrollExportItemRead] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)


class PayrollPayslipArchiveFilter(BaseModel):
    employee_id: str | None = None
    provider_key: str | None = None
    period_start: date | None = None
    period_end: date | None = None


class PayrollPayslipArchiveCreate(BaseModel):
    employee_id: str
    export_batch_id: str | None = None
    provider_key: str
    period_start: date
    period_end: date
    source_document_id: str
    notes: str | None = None


class PayrollPayslipArchiveRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_id: str
    export_batch_id: str | None
    provider_key: str
    period_start: date
    period_end: date
    archive_status_code: str
    source_document_id: str | None
    notes: str | None
    superseded_by_archive_id: str | None
    version_no: int


class PayrollReconciliationFilter(BaseModel):
    employee_id: str | None = None
    period_start: date
    period_end: date


class PayrollReconciliationRowRead(BaseModel):
    employee_id: str
    export_employee_code: str | None
    pay_profile_id: str | None
    approved_actual_count: int
    exported_item_count: int
    archived_payslip_count: int
    payable_minutes: int
    exported_amount_total: float
    allowance_amount_total: float
    outstanding_advance_total: float
    overtime_balance_minutes: int
    missing_export: bool
    missing_payslip: bool
    mismatch_codes: list[str] = Field(default_factory=list)

