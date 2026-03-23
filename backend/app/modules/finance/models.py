"""Finance-owned actual bridge, payroll, and approval models."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, ForeignKeyConstraint, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditLifecycleMixin, Base, UUIDPrimaryKeyMixin
from app.modules.customers.models import Customer, CustomerBillingProfile, CustomerInvoiceParty, CustomerRateCard, CustomerRateLine, CustomerSurchargeRule
from app.modules.employees.models import Employee, FunctionType, QualificationType
from app.modules.field_execution.models import AttendanceRecord
from app.modules.planning.models import Assignment, CustomerOrder, PlanningRecord, Shift
from app.modules.platform_services.integration_models import ImportExportJob, IntegrationEndpoint
from app.modules.subcontractors.models import Subcontractor, SubcontractorRateCard, SubcontractorRateLine, SubcontractorWorker


class ActualRecord(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "actual_record"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["ops.assignment.tenant_id", "ops.assignment.id"],
            name="fk_finance_actual_record_tenant_assignment",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_finance_actual_record_tenant_shift",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "attendance_record_id"],
            ["field.attendance_record.tenant_id", "field.attendance_record.id"],
            name="fk_finance_actual_record_tenant_attendance",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_finance_actual_record_tenant_employee",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_finance_actual_record_tenant_worker",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "superseded_by_actual_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_record_tenant_superseded_by",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_actual_record_tenant_id_id"),
        CheckConstraint(
            "actor_type_code IN ('employee','subcontractor_worker')",
            name="actual_record_actor_type_valid",
        ),
        CheckConstraint(
            "(employee_id IS NOT NULL AND subcontractor_worker_id IS NULL AND actor_type_code = 'employee') OR "
            "(employee_id IS NULL AND subcontractor_worker_id IS NOT NULL AND actor_type_code = 'subcontractor_worker')",
            name="actual_record_actor_reference_valid",
        ),
        CheckConstraint(
            "discrepancy_state_code IN ('clean','warning','needs_review')",
            name="actual_record_discrepancy_state_valid",
        ),
        CheckConstraint(
            "derivation_status_code IN ('draft','derived','needs_review','superseded')",
            name="actual_record_derivation_status_valid",
        ),
        CheckConstraint(
            "approval_stage_code IN ('draft','preliminary_submitted','operational_confirmed','finance_signed_off')",
            name="actual_record_approval_stage_valid",
        ),
        CheckConstraint("planned_break_minutes >= 0", name="actual_record_planned_break_nonnegative"),
        CheckConstraint("actual_break_minutes >= 0", name="actual_record_actual_break_nonnegative"),
        CheckConstraint("payable_minutes >= 0", name="actual_record_payable_nonnegative"),
        CheckConstraint("billable_minutes >= 0", name="actual_record_billable_nonnegative"),
        CheckConstraint("customer_adjustment_minutes >= 0", name="actual_record_customer_adjustment_nonnegative"),
        Index("ix_finance_actual_record_shift_derived", "tenant_id", "shift_id", "derived_at"),
        Index("ix_finance_actual_record_attendance", "tenant_id", "attendance_record_id"),
        Index(
            "uq_finance_actual_record_assignment_current",
            "tenant_id",
            "assignment_id",
            unique=True,
            postgresql_where=text("is_current = true AND archived_at IS NULL"),
        ),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    assignment_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    shift_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    attendance_record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    actor_type_code: Mapped[str] = mapped_column(String(40), nullable=False)
    employee_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    subcontractor_worker_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    planned_start_at: Mapped[datetime | None] = mapped_column(nullable=True)
    planned_end_at: Mapped[datetime | None] = mapped_column(nullable=True)
    actual_start_at: Mapped[datetime | None] = mapped_column(nullable=True)
    actual_end_at: Mapped[datetime | None] = mapped_column(nullable=True)
    planned_break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    actual_break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    payable_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    billable_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    customer_adjustment_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    discrepancy_state_code: Mapped[str] = mapped_column(String(40), nullable=False, default="clean", server_default="clean")
    discrepancy_codes_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    discrepancy_details_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    derivation_status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    approval_stage_code: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    derived_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now(UTC), server_default=text("CURRENT_TIMESTAMP"))
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    superseded_at: Mapped[datetime | None] = mapped_column(nullable=True)
    superseded_by_actual_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    assignment: Mapped[Assignment] = relationship(lazy="selectin", overlaps="shift,attendance_record,employee,subcontractor_worker")
    shift: Mapped[Shift] = relationship(lazy="selectin", overlaps="assignment,attendance_record,employee,subcontractor_worker")
    attendance_record: Mapped[AttendanceRecord | None] = relationship(
        lazy="selectin",
        overlaps="assignment,shift,employee,subcontractor_worker",
    )
    employee: Mapped[Employee | None] = relationship(lazy="selectin", overlaps="assignment,shift,attendance_record,subcontractor_worker")
    subcontractor_worker: Mapped[SubcontractorWorker | None] = relationship(
        lazy="selectin",
        overlaps="assignment,shift,attendance_record,employee",
    )
    approvals: Mapped[list["ActualApproval"]] = relationship(
        back_populates="actual_record",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ActualApproval.created_at",
    )
    reconciliations: Mapped[list["ActualReconciliation"]] = relationship(
        back_populates="actual_record",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ActualReconciliation.created_at",
    )
    allowances: Mapped[list["ActualAllowance"]] = relationship(
        back_populates="actual_record",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ActualAllowance.created_at",
    )
    expenses: Mapped[list["ActualExpense"]] = relationship(
        back_populates="actual_record",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ActualExpense.created_at",
    )
    comments: Mapped[list["ActualComment"]] = relationship(
        back_populates="actual_record",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ActualComment.created_at",
    )


class ActualApproval(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "actual_approval"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_approval_tenant_actual",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_actual_approval_tenant_id_id"),
        UniqueConstraint("tenant_id", "actual_record_id", "stage_code", name="uq_finance_actual_approval_stage"),
        CheckConstraint(
            "stage_code IN ('preliminary_submitted','operational_confirmed','finance_signed_off')",
            name="actual_approval_stage_valid",
        ),
        CheckConstraint(
            "actor_scope_code IN ('employee_self','field_lead','operational_lead','finance')",
            name="actual_approval_actor_scope_valid",
        ),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    actual_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    stage_code: Mapped[str] = mapped_column(String(40), nullable=False)
    actor_scope_code: Mapped[str] = mapped_column(String(40), nullable=False)
    note_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_ref_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    actual_record: Mapped[ActualRecord] = relationship(back_populates="approvals", lazy="selectin")


class ActualReconciliation(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "actual_reconciliation"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_reconciliation_tenant_actual",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "replacement_employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_finance_actual_reconciliation_tenant_employee",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "replacement_subcontractor_worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_finance_actual_reconciliation_tenant_worker",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_actual_reconciliation_tenant_id_id"),
        CheckConstraint(
            "reconciliation_kind_code IN ('sickness','cancellation','replacement','customer_adjustment','flat_rate')",
            name="actual_reconciliation_kind_valid",
        ),
        CheckConstraint(
            "replacement_actor_type_code IS NULL OR replacement_actor_type_code IN ('employee','subcontractor_worker')",
            name="actual_reconciliation_replacement_actor_type_valid",
        ),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    actual_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    reconciliation_kind_code: Mapped[str] = mapped_column(String(40), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(60), nullable=False)
    note_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    payroll_minutes_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    billable_minutes_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    customer_adjustment_minutes_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    replacement_actor_type_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    replacement_employee_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    replacement_subcontractor_worker_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    source_ref_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    actual_record: Mapped[ActualRecord] = relationship(back_populates="reconciliations", lazy="selectin")


class ActualAllowance(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "actual_allowance"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_allowance_tenant_actual",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_actual_allowance_tenant_id_id"),
        CheckConstraint(
            "line_type_code IN ('allowance','flat_rate','customer_flat_rate')",
            name="actual_allowance_line_type_valid",
        ),
        CheckConstraint("quantity >= 0", name="actual_allowance_quantity_nonnegative"),
        CheckConstraint("amount_total >= 0", name="actual_allowance_amount_nonnegative"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    actual_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    line_type_code: Mapped[str] = mapped_column(String(40), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(60), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=1, server_default="1")
    unit_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    amount_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default="EUR")
    source_ref_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    note_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    actual_record: Mapped[ActualRecord] = relationship(back_populates="allowances", lazy="selectin")


class ActualExpense(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "actual_expense"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_expense_tenant_actual",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_actual_expense_tenant_id_id"),
        CheckConstraint("quantity >= 0", name="actual_expense_quantity_nonnegative"),
        CheckConstraint("amount_total >= 0", name="actual_expense_amount_nonnegative"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    actual_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    expense_type_code: Mapped[str] = mapped_column(String(40), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(60), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=1, server_default="1")
    unit_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    amount_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default="EUR")
    source_ref_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    note_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    actual_record: Mapped[ActualRecord] = relationship(back_populates="expenses", lazy="selectin")


class ActualComment(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "actual_comment"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_comment_tenant_actual",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_actual_comment_tenant_id_id"),
        CheckConstraint(
            "visibility_code IN ('shared','finance_only')",
            name="actual_comment_visibility_valid",
        ),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    actual_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    visibility_code: Mapped[str] = mapped_column(String(40), nullable=False, default="finance_only", server_default="finance_only")
    note_text: Mapped[str] = mapped_column(String(2000), nullable=False)

    actual_record: Mapped[ActualRecord] = relationship(back_populates="comments", lazy="selectin")


class PayrollTariffTable(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "payroll_tariff_table"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_finance_payroll_tariff_table_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_tariff_table_tenant_id_id"),
        CheckConstraint("effective_until IS NULL OR effective_until >= effective_from", name="payroll_tariff_table_window_valid"),
        CheckConstraint("tariff_status_code IN ('draft','active','archived')", name="payroll_tariff_table_status_valid"),
        Index("ix_finance_payroll_tariff_table_region_window", "tenant_id", "region_code", "effective_from"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    region_code: Mapped[str] = mapped_column(String(32), nullable=False)
    tariff_status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    effective_from: Mapped[date] = mapped_column(Date(), nullable=False)
    effective_until: Mapped[date | None] = mapped_column(Date(), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    rates: Mapped[list["PayrollTariffRate"]] = relationship(
        back_populates="tariff_table",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="PayrollTariffRate.created_at",
    )
    surcharge_rules: Mapped[list["PayrollSurchargeRule"]] = relationship(
        back_populates="tariff_table",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="PayrollSurchargeRule.created_at",
    )


class PayrollTariffRate(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "payroll_tariff_rate"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "tariff_table_id"],
            ["finance.payroll_tariff_table.tenant_id", "finance.payroll_tariff_table.id"],
            name="fk_finance_payroll_tariff_rate_tenant_table",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "function_type_id"],
            ["hr.function_type.tenant_id", "hr.function_type.id"],
            name="fk_finance_payroll_tariff_rate_tenant_function_type",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_finance_payroll_tariff_rate_tenant_qualification_type",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "tariff_table_id",
            "function_type_id",
            "qualification_type_id",
            "employment_type_code",
            "pay_unit_code",
            name="uq_finance_payroll_tariff_rate_dimensions",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_tariff_rate_tenant_id_id"),
        CheckConstraint("base_amount >= 0", name="payroll_tariff_rate_amount_nonnegative"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    tariff_table_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    function_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    qualification_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    employment_type_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    pay_unit_code: Mapped[str] = mapped_column(String(20), nullable=False, default="hour", server_default="hour")
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default="EUR")
    base_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payroll_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    tariff_table: Mapped[PayrollTariffTable] = relationship(back_populates="rates", lazy="selectin")
    function_type: Mapped[FunctionType | None] = relationship(lazy="selectin", overlaps="rates,tariff_table")
    qualification_type: Mapped[QualificationType | None] = relationship(lazy="selectin", overlaps="function_type,rates,tariff_table")


class PayrollSurchargeRule(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "payroll_surcharge_rule"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "tariff_table_id"],
            ["finance.payroll_tariff_table.tenant_id", "finance.payroll_tariff_table.id"],
            name="fk_finance_payroll_surcharge_rule_tenant_table",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "function_type_id"],
            ["hr.function_type.tenant_id", "hr.function_type.id"],
            name="fk_finance_payroll_surcharge_rule_tenant_function_type",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_finance_payroll_surcharge_rule_tenant_qualification_type",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "tariff_table_id",
            "surcharge_type_code",
            "custom_code",
            "weekday_mask",
            "start_minute_local",
            "end_minute_local",
            "function_type_id",
            "qualification_type_id",
            "employment_type_code",
            "holiday_region_code",
            name="uq_finance_payroll_surcharge_rule_dimensions",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_surcharge_rule_tenant_id_id"),
        CheckConstraint("weekday_mask >= 0 AND weekday_mask <= 127", name="payroll_surcharge_rule_weekday_mask_valid"),
        CheckConstraint("start_minute_local >= 0 AND start_minute_local <= 1439", name="payroll_surcharge_rule_start_minute_valid"),
        CheckConstraint("end_minute_local >= 0 AND end_minute_local <= 1440", name="payroll_surcharge_rule_end_minute_valid"),
        CheckConstraint("percent_value IS NOT NULL OR fixed_amount IS NOT NULL", name="payroll_surcharge_rule_amount_required"),
        CheckConstraint("percent_value IS NULL OR percent_value >= 0", name="payroll_surcharge_rule_percent_nonnegative"),
        CheckConstraint("fixed_amount IS NULL OR fixed_amount >= 0", name="payroll_surcharge_rule_fixed_amount_nonnegative"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    tariff_table_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    surcharge_type_code: Mapped[str] = mapped_column(String(40), nullable=False)
    custom_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    weekday_mask: Mapped[int] = mapped_column(Integer, nullable=False, default=127, server_default="127")
    start_minute_local: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    end_minute_local: Mapped[int] = mapped_column(Integer, nullable=False, default=1440, server_default="1440")
    holiday_region_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    function_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    qualification_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    employment_type_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    percent_value: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    fixed_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    payroll_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    tariff_table: Mapped[PayrollTariffTable] = relationship(back_populates="surcharge_rules", lazy="selectin")
    function_type: Mapped[FunctionType | None] = relationship(lazy="selectin", overlaps="surcharge_rules,tariff_table")
    qualification_type: Mapped[QualificationType | None] = relationship(lazy="selectin", overlaps="function_type,surcharge_rules,tariff_table")


class EmployeePayProfile(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_pay_profile"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_finance_employee_pay_profile_tenant_employee",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "tariff_table_id"],
            ["finance.payroll_tariff_table.tenant_id", "finance.payroll_tariff_table.id"],
            name="fk_finance_employee_pay_profile_tenant_tariff_table",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_employee_pay_profile_tenant_id_id"),
        CheckConstraint("effective_until IS NULL OR effective_until >= effective_from", name="employee_pay_profile_window_valid"),
        CheckConstraint("base_rate_override IS NULL OR base_rate_override >= 0", name="employee_pay_profile_base_rate_nonnegative"),
        Index("ix_finance_employee_pay_profile_employee_window", "tenant_id", "employee_id", "effective_from"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    tariff_table_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    payroll_region_code: Mapped[str] = mapped_column(String(32), nullable=False)
    employment_type_code: Mapped[str] = mapped_column(String(40), nullable=False)
    pay_cycle_code: Mapped[str] = mapped_column(String(40), nullable=False, default="monthly", server_default="monthly")
    pay_unit_code: Mapped[str] = mapped_column(String(20), nullable=False, default="hour", server_default="hour")
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default="EUR")
    export_employee_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    cost_center_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    base_rate_override: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    override_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    effective_from: Mapped[date] = mapped_column(Date(), nullable=False)
    effective_until: Mapped[date | None] = mapped_column(Date(), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(lazy="selectin", overlaps="tariff_table")
    tariff_table: Mapped[PayrollTariffTable | None] = relationship(lazy="selectin", overlaps="employee")


class PayrollExportBatch(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "payroll_export_batch"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "endpoint_id"],
            ["integration.endpoint.tenant_id", "integration.endpoint.id"],
            name="fk_finance_payroll_export_batch_tenant_endpoint",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "job_id"],
            ["integration.import_export_job.tenant_id", "integration.import_export_job.id"],
            name="fk_finance_payroll_export_batch_tenant_job",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "batch_no", name="uq_finance_payroll_export_batch_tenant_batch_no"),
        UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_export_batch_tenant_id_id"),
        CheckConstraint(
            "batch_status_code IN ('draft','generated','queued','dispatched','failed','archived')",
            name="payroll_export_batch_status_valid",
        ),
        CheckConstraint("period_end >= period_start", name="payroll_export_batch_period_valid"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    batch_no: Mapped[str] = mapped_column(String(80), nullable=False)
    provider_key: Mapped[str] = mapped_column(String(120), nullable=False)
    endpoint_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    job_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    batch_status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default="EUR")
    generated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    queued_at: Mapped[datetime | None] = mapped_column(nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    endpoint: Mapped[IntegrationEndpoint | None] = relationship(lazy="selectin", overlaps="job")
    job: Mapped[ImportExportJob | None] = relationship(lazy="selectin", overlaps="endpoint")
    items: Mapped[list["PayrollExportItem"]] = relationship(
        back_populates="batch",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="PayrollExportItem.created_at",
    )
    payslip_archives: Mapped[list["PayrollPayslipArchive"]] = relationship(
        back_populates="export_batch",
        lazy="selectin",
        order_by="PayrollPayslipArchive.period_start",
    )


class PayrollExportItem(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "payroll_export_item"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["finance.payroll_export_batch.tenant_id", "finance.payroll_export_batch.id"],
            name="fk_finance_payroll_export_item_tenant_batch",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_payroll_export_item_tenant_actual",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_finance_payroll_export_item_tenant_employee",
            ondelete="SET NULL",
        ),
        UniqueConstraint(
            "tenant_id",
            "batch_id",
            "actual_record_id",
            "pay_code",
            name="uq_finance_payroll_export_item_source_line",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_export_item_tenant_id_id"),
        CheckConstraint("quantity >= 0", name="payroll_export_item_quantity_nonnegative"),
        CheckConstraint("amount_total >= 0", name="payroll_export_item_amount_nonnegative"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    batch_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    actual_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    employee_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    pay_code: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    unit_code: Mapped[str] = mapped_column(String(20), nullable=False)
    amount_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default="EUR")
    payload_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    source_ref_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    batch: Mapped[PayrollExportBatch] = relationship(back_populates="items", lazy="selectin")
    actual_record: Mapped[ActualRecord] = relationship(lazy="selectin", overlaps="batch,items")
    employee: Mapped[Employee | None] = relationship(lazy="selectin", overlaps="actual_record,batch,items")


class PayrollPayslipArchive(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "payroll_payslip_archive"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_finance_payroll_payslip_archive_tenant_employee",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "export_batch_id"],
            ["finance.payroll_export_batch.tenant_id", "finance.payroll_export_batch.id"],
            name="fk_finance_payroll_payslip_archive_tenant_batch",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "superseded_by_archive_id"],
            ["finance.payroll_payslip_archive.tenant_id", "finance.payroll_payslip_archive.id"],
            name="fk_finance_payroll_payslip_archive_tenant_superseded_by",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_payslip_archive_tenant_id_id"),
        CheckConstraint(
            "archive_status_code IN ('active','superseded','import_failed')",
            name="payroll_payslip_archive_status_valid",
        ),
        CheckConstraint("period_end >= period_start", name="payroll_payslip_archive_period_valid"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    export_batch_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    provider_key: Mapped[str] = mapped_column(String(120), nullable=False)
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    archive_status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="active", server_default="active")
    source_document_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    superseded_by_archive_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    employee: Mapped[Employee] = relationship(lazy="selectin", overlaps="payslip_archives,export_batch")
    export_batch: Mapped[PayrollExportBatch | None] = relationship(back_populates="payslip_archives", lazy="selectin", overlaps="employee")


class SubcontractorInvoiceCheck(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_invoice_check"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_id"],
            ["partner.subcontractor.tenant_id", "partner.subcontractor.id"],
            name="fk_finance_subcontractor_invoice_check_tenant_subcontractor",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_subcontractor_invoice_check_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "subcontractor_id",
            "period_start",
            "period_end",
            name="uq_finance_subcontractor_invoice_check_period",
        ),
        CheckConstraint("period_end >= period_start", name="subcontractor_invoice_check_period_valid"),
        CheckConstraint(
            "status_code IN ('draft','review_required','approved','exception','released')",
            name="subcontractor_invoice_check_status_valid",
        ),
        CheckConstraint("assigned_minutes_total >= 0", name="subcontractor_invoice_check_assigned_minutes_nonnegative"),
        CheckConstraint("actual_minutes_total >= 0", name="subcontractor_invoice_check_actual_minutes_nonnegative"),
        CheckConstraint("approved_minutes_total >= 0", name="subcontractor_invoice_check_approved_minutes_nonnegative"),
        Index("ix_finance_subcontractor_invoice_check_period", "tenant_id", "subcontractor_id", "period_start", "period_end"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    subcontractor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    check_no: Mapped[str] = mapped_column(String(120), nullable=False)
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    period_label: Mapped[str] = mapped_column(String(120), nullable=False)
    status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    assigned_minutes_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    actual_minutes_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    approved_minutes_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    expected_amount_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    approved_amount_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    comparison_variance_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    submitted_invoice_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    submitted_invoice_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    submitted_variance_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    submitted_invoice_currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    review_reason_codes_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    last_generated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    subcontractor: Mapped[Subcontractor] = relationship(lazy="selectin")
    lines: Mapped[list["SubcontractorInvoiceCheckLine"]] = relationship(
        back_populates="invoice_check",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="SubcontractorInvoiceCheckLine.sort_order",
    )
    notes: Mapped[list["SubcontractorInvoiceCheckNote"]] = relationship(
        back_populates="invoice_check",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="SubcontractorInvoiceCheckNote.created_at",
    )


class SubcontractorInvoiceCheckLine(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_invoice_check_line"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "invoice_check_id"],
            ["finance.subcontractor_invoice_check.tenant_id", "finance.subcontractor_invoice_check.id"],
            name="fk_finance_subcontractor_invoice_check_line_tenant_check",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["ops.assignment.tenant_id", "ops.assignment.id"],
            name="fk_finance_subcontractor_invoice_check_line_tenant_assignment",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_subcontractor_invoice_check_line_tenant_actual",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_finance_subcontractor_invoice_check_line_tenant_shift",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_finance_subcontractor_invoice_check_line_tenant_worker",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "rate_card_id"],
            ["partner.subcontractor_rate_card.tenant_id", "partner.subcontractor_rate_card.id"],
            name="fk_finance_subcontractor_invoice_check_line_tenant_rate_card",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "rate_line_id"],
            ["partner.subcontractor_rate_line.tenant_id", "partner.subcontractor_rate_line.id"],
            name="fk_finance_subcontractor_invoice_check_line_tenant_rate_line",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "function_type_id"],
            ["hr.function_type.tenant_id", "hr.function_type.id"],
            name="fk_finance_subcontractor_invoice_check_line_tenant_function",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_fin_sic_line_tenant_qual",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_subcontractor_invoice_check_line_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "invoice_check_id",
            "assignment_id",
            "actual_record_id",
            name="uq_finance_subcontractor_invoice_check_line_source",
        ),
        CheckConstraint(
            "comparison_state_code IN ('clean','warning','needs_review')",
            name="subcontractor_invoice_check_line_comparison_state_valid",
        ),
        CheckConstraint("expected_quantity >= 0", name="subcontractor_invoice_check_line_expected_quantity_nonnegative"),
        CheckConstraint("actual_quantity >= 0", name="subcontractor_invoice_check_line_actual_quantity_nonnegative"),
        CheckConstraint("approved_quantity >= 0", name="subcontractor_invoice_check_line_approved_quantity_nonnegative"),
        Index("ix_finance_subcontractor_invoice_check_line_sort", "tenant_id", "invoice_check_id", "sort_order"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    invoice_check_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    assignment_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    actual_record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    shift_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    subcontractor_worker_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    rate_card_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    rate_line_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    function_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    qualification_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    service_date: Mapped[date] = mapped_column(Date(), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    billing_unit_code: Mapped[str] = mapped_column(String(20), nullable=False, default="hour", server_default="hour")
    assigned_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    actual_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    approved_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    expected_quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    actual_quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    approved_quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    unit_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    expected_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    approved_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    variance_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    comparison_state_code: Mapped[str] = mapped_column(String(40), nullable=False, default="clean", server_default="clean")
    variance_reason_codes_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    source_ref_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    invoice_check: Mapped[SubcontractorInvoiceCheck] = relationship(back_populates="lines", lazy="selectin")
    assignment: Mapped[Assignment | None] = relationship(lazy="selectin", overlaps="invoice_check,lines,actual_record,shift,subcontractor_worker,rate_card,rate_line,function_type,qualification_type")
    actual_record: Mapped[ActualRecord | None] = relationship(lazy="selectin", overlaps="invoice_check,lines,assignment,shift,subcontractor_worker,rate_card,rate_line,function_type,qualification_type")
    shift: Mapped[Shift | None] = relationship(lazy="selectin", overlaps="invoice_check,lines,assignment,actual_record,subcontractor_worker,rate_card,rate_line,function_type,qualification_type")
    subcontractor_worker: Mapped[SubcontractorWorker | None] = relationship(lazy="selectin", overlaps="invoice_check,lines,assignment,actual_record,shift,rate_card,rate_line,function_type,qualification_type")
    rate_card: Mapped[SubcontractorRateCard | None] = relationship(lazy="selectin", overlaps="invoice_check,lines,assignment,actual_record,shift,subcontractor_worker,rate_line,function_type,qualification_type")
    rate_line: Mapped[SubcontractorRateLine | None] = relationship(lazy="selectin", overlaps="invoice_check,lines,assignment,actual_record,shift,subcontractor_worker,rate_card,function_type,qualification_type")
    function_type: Mapped[FunctionType | None] = relationship(lazy="selectin", overlaps="invoice_check,lines,assignment,actual_record,shift,subcontractor_worker,rate_card,rate_line,qualification_type")
    qualification_type: Mapped[QualificationType | None] = relationship(lazy="selectin", overlaps="invoice_check,lines,assignment,actual_record,shift,subcontractor_worker,rate_card,rate_line,function_type")


class SubcontractorInvoiceCheckNote(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_invoice_check_note"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "invoice_check_id"],
            ["finance.subcontractor_invoice_check.tenant_id", "finance.subcontractor_invoice_check.id"],
            name="fk_finance_subcontractor_invoice_check_note_tenant_check",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_subcontractor_invoice_check_note_tenant_id_id"),
        CheckConstraint("visibility_code IN ('internal')", name="subcontractor_invoice_check_note_visibility_valid"),
        CheckConstraint("note_kind_code IN ('note','exception','approval')", name="subcontractor_invoice_check_note_kind_valid"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    invoice_check_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    visibility_code: Mapped[str] = mapped_column(String(40), nullable=False, default="internal", server_default="internal")
    note_kind_code: Mapped[str] = mapped_column(String(40), nullable=False, default="note", server_default="note")
    note_text: Mapped[str] = mapped_column(String(2000), nullable=False)

    invoice_check: Mapped[SubcontractorInvoiceCheck] = relationship(back_populates="notes", lazy="selectin")


class Timesheet(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "timesheet"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_finance_timesheet_tenant_customer",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "order_id"],
            ["ops.customer_order.tenant_id", "ops.customer_order.id"],
            name="fk_finance_timesheet_tenant_order",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_finance_timesheet_tenant_record",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_timesheet_tenant_id_id"),
        UniqueConstraint("tenant_id", "scope_key", name="uq_finance_timesheet_scope_key"),
        CheckConstraint("period_end >= period_start", name="timesheet_period_valid"),
        CheckConstraint(
            "billing_granularity_code IN ('shift','planning_record','order_day')",
            name="timesheet_billing_granularity_valid",
        ),
        CheckConstraint(
            "release_state_code IN ('draft','released','archived')",
            name="timesheet_release_state_valid",
        ),
        Index("ix_finance_timesheet_customer_period", "tenant_id", "customer_id", "period_start", "period_end"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    order_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    planning_record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    scope_key: Mapped[str] = mapped_column(String(255), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    billing_granularity_code: Mapped[str] = mapped_column(String(40), nullable=False)
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    total_planned_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_actual_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_billable_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    release_state_code: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    customer_visible_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    released_at: Mapped[datetime | None] = mapped_column(nullable=True)
    released_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    source_document_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    customer: Mapped[Customer] = relationship(lazy="selectin", overlaps="order,planning_record")
    order: Mapped[CustomerOrder | None] = relationship(lazy="selectin", overlaps="customer,planning_record")
    planning_record: Mapped[PlanningRecord | None] = relationship(lazy="selectin", overlaps="customer,order")
    lines: Mapped[list["TimesheetLine"]] = relationship(
        back_populates="timesheet",
        lazy="selectin",
        order_by="TimesheetLine.sort_order",
        cascade="all, delete-orphan",
    )
    invoices: Mapped[list["CustomerInvoice"]] = relationship(back_populates="timesheet", lazy="selectin", overlaps="customer,billing_profile,invoice_party,job")


class TimesheetLine(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "timesheet_line"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "timesheet_id"],
            ["finance.timesheet.tenant_id", "finance.timesheet.id"],
            name="fk_finance_timesheet_line_tenant_timesheet",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_timesheet_line_tenant_actual",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_finance_timesheet_line_tenant_shift",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "order_id"],
            ["ops.customer_order.tenant_id", "ops.customer_order.id"],
            name="fk_finance_timesheet_line_tenant_order",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_finance_timesheet_line_tenant_record",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_timesheet_line_tenant_id_id"),
        UniqueConstraint("tenant_id", "timesheet_id", "actual_record_id", name="uq_finance_timesheet_line_actual_once"),
        Index("ix_finance_timesheet_line_timesheet_sort", "tenant_id", "timesheet_id", "sort_order"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    timesheet_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    actual_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    shift_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    order_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    planning_record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    service_date: Mapped[date] = mapped_column(Date(), nullable=False)
    planning_mode_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    line_label: Mapped[str] = mapped_column(String(255), nullable=False)
    line_description: Mapped[str] = mapped_column(Text(), nullable=False)
    planned_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    actual_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    billable_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    unit_code: Mapped[str] = mapped_column(String(20), nullable=False, default="hour", server_default="hour")
    source_ref_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    customer_safe_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    personal_names_released: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))

    timesheet: Mapped[Timesheet] = relationship(back_populates="lines", lazy="selectin")
    actual_record: Mapped[ActualRecord] = relationship(lazy="selectin", overlaps="timesheet,lines")
    shift: Mapped[Shift] = relationship(lazy="selectin", overlaps="timesheet,actual_record,lines")
    order: Mapped[CustomerOrder | None] = relationship(lazy="selectin", overlaps="timesheet,planning_record,actual_record,shift,lines")
    planning_record: Mapped[PlanningRecord | None] = relationship(lazy="selectin", overlaps="timesheet,order,actual_record,shift,lines")
    invoice_lines: Mapped[list["CustomerInvoiceLine"]] = relationship(back_populates="timesheet_line", lazy="selectin", overlaps="invoice,lines,source_actual,rate_card,rate_line,surcharge_rule")


class CustomerInvoice(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer_invoice"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_finance_customer_invoice_tenant_customer",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "timesheet_id"],
            ["finance.timesheet.tenant_id", "finance.timesheet.id"],
            name="fk_finance_customer_invoice_tenant_timesheet",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "billing_profile_id"],
            ["crm.customer_billing_profile.tenant_id", "crm.customer_billing_profile.id"],
            name="fk_finance_customer_invoice_tenant_billing_profile",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "invoice_party_id"],
            ["crm.customer_invoice_party.tenant_id", "crm.customer_invoice_party.id"],
            name="fk_finance_customer_invoice_tenant_invoice_party",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "job_id"],
            ["integration.import_export_job.tenant_id", "integration.import_export_job.id"],
            name="fk_finance_customer_invoice_tenant_job",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_customer_invoice_tenant_id_id"),
        UniqueConstraint("tenant_id", "invoice_no", name="uq_finance_customer_invoice_number"),
        CheckConstraint("period_end >= period_start", name="customer_invoice_period_valid"),
        CheckConstraint("due_date >= issue_date", name="customer_invoice_due_date_valid"),
        CheckConstraint(
            "invoice_status_code IN ('draft','issued','released','queued','sent','failed','archived')",
            name="customer_invoice_status_valid",
        ),
        CheckConstraint("subtotal_amount >= 0", name="customer_invoice_subtotal_nonnegative"),
        CheckConstraint("tax_amount >= 0", name="customer_invoice_tax_nonnegative"),
        CheckConstraint("total_amount >= 0", name="customer_invoice_total_nonnegative"),
        Index("ix_finance_customer_invoice_customer_issue_date", "tenant_id", "customer_id", "issue_date"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    timesheet_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    billing_profile_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    invoice_party_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    job_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    invoice_no: Mapped[str] = mapped_column(String(120), nullable=False)
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date(), nullable=False)
    due_date: Mapped[date] = mapped_column(Date(), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default="EUR")
    layout_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    invoice_status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    subtotal_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    customer_visible_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    source_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    invoice_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dispatch_method_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    e_invoice_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    leitweg_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payment_terms_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    billing_profile_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    invoice_party_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    delivery_context_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    delivery_status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="not_queued", server_default="not_queued")
    issued_at: Mapped[datetime | None] = mapped_column(nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(nullable=True)
    source_document_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer] = relationship(lazy="selectin", overlaps="timesheet,billing_profile,invoice_party,invoices,job")
    timesheet: Mapped[Timesheet | None] = relationship(back_populates="invoices", lazy="selectin", overlaps="customer,billing_profile,invoice_party,job")
    billing_profile: Mapped[CustomerBillingProfile | None] = relationship(lazy="selectin", overlaps="customer,timesheet,invoice_party,invoices,job")
    invoice_party: Mapped[CustomerInvoiceParty | None] = relationship(lazy="selectin", overlaps="customer,timesheet,billing_profile,invoices,job")
    job: Mapped[ImportExportJob | None] = relationship(lazy="selectin", overlaps="customer,timesheet,billing_profile,invoice_party,invoices")
    lines: Mapped[list["CustomerInvoiceLine"]] = relationship(
        back_populates="invoice",
        lazy="selectin",
        order_by="CustomerInvoiceLine.sort_order",
        cascade="all, delete-orphan",
        overlaps="timesheet_line,invoice_lines,source_actual,rate_card,rate_line,surcharge_rule",
    )


class CustomerInvoiceLine(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer_invoice_line"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "invoice_id"],
            ["finance.customer_invoice.tenant_id", "finance.customer_invoice.id"],
            name="fk_finance_customer_invoice_line_tenant_invoice",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "timesheet_line_id"],
            ["finance.timesheet_line.tenant_id", "finance.timesheet_line.id"],
            name="fk_finance_customer_invoice_line_tenant_timesheet_line",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_actual_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_customer_invoice_line_tenant_actual",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "rate_card_id"],
            ["crm.customer_rate_card.tenant_id", "crm.customer_rate_card.id"],
            name="fk_finance_customer_invoice_line_tenant_rate_card",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "rate_line_id"],
            ["crm.customer_rate_line.tenant_id", "crm.customer_rate_line.id"],
            name="fk_finance_customer_invoice_line_tenant_rate_line",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "surcharge_rule_id"],
            ["crm.customer_surcharge_rule.tenant_id", "crm.customer_surcharge_rule.id"],
            name="fk_finance_customer_invoice_line_tenant_surcharge_rule",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_finance_customer_invoice_line_tenant_id_id"),
        CheckConstraint("quantity >= 0", name="customer_invoice_line_quantity_nonnegative"),
        CheckConstraint("unit_price >= 0", name="customer_invoice_line_unit_price_nonnegative"),
        CheckConstraint("net_amount >= 0", name="customer_invoice_line_net_nonnegative"),
        CheckConstraint("tax_amount >= 0", name="customer_invoice_line_tax_nonnegative"),
        CheckConstraint("gross_amount >= 0", name="customer_invoice_line_gross_nonnegative"),
        Index("ix_finance_customer_invoice_line_invoice_sort", "tenant_id", "invoice_id", "sort_order"),
        {"schema": "finance"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    invoice_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    timesheet_line_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    source_actual_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    rate_card_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    rate_line_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    surcharge_rule_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    line_kind_code: Mapped[str] = mapped_column(String(40), nullable=False, default="base", server_default="base")
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    unit_code: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0, server_default="0")
    net_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    gross_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    source_ref_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    invoice: Mapped[CustomerInvoice] = relationship(back_populates="lines", lazy="selectin", overlaps="timesheet_line,invoice_lines,source_actual,rate_card,rate_line,surcharge_rule")
    timesheet_line: Mapped[TimesheetLine | None] = relationship(back_populates="invoice_lines", lazy="selectin", overlaps="invoice,lines,source_actual,rate_card,rate_line,surcharge_rule")
    source_actual: Mapped[ActualRecord | None] = relationship(lazy="selectin", overlaps="invoice,timesheet_line,invoice_lines,lines")
    rate_card: Mapped[CustomerRateCard | None] = relationship(lazy="selectin", overlaps="invoice,timesheet_line,source_actual,invoice_lines,lines")
    rate_line: Mapped[CustomerRateLine | None] = relationship(lazy="selectin", overlaps="invoice,timesheet_line,rate_card,source_actual,invoice_lines,lines")
    surcharge_rule: Mapped[CustomerSurchargeRule | None] = relationship(lazy="selectin", overlaps="invoice,timesheet_line,rate_card,rate_line,source_actual,invoice_lines,lines")
