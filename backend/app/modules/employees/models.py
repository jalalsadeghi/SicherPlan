"""Employee master, qualifications, availability, absences, balances, private profile, and notes."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditLifecycleMixin, Base, UUIDPrimaryKeyMixin
from app.modules.core.models import Address, Branch, Mandate
from app.modules.iam.models import UserAccount


EMPLOYEE_ADDRESS_TYPES = ("home", "mailing")
EMPLOYEE_NOTE_TYPES = ("operational_note", "positive_activity", "reminder")
EMPLOYEE_EMPLOYMENT_TYPES = ("full_time", "part_time", "mini_job", "temporary", "working_student", "freelance", "other")
EMPLOYEE_QUALIFICATION_RECORD_KINDS = ("function", "qualification")
EMPLOYEE_AVAILABILITY_RULE_KINDS = ("availability", "unavailable", "free_wish")
EMPLOYEE_AVAILABILITY_RECURRENCE_TYPES = ("none", "weekly")
EMPLOYEE_ABSENCE_TYPES = ("vacation", "sickness", "child_care", "other")
EMPLOYEE_ABSENCE_STATUSES = ("pending", "approved", "rejected", "cancelled")
EMPLOYEE_EVENT_APPLICATION_STATUSES = ("pending", "approved", "rejected", "withdrawn")
EMPLOYEE_TIME_ACCOUNT_TYPES = ("work_time", "overtime", "flextime")
EMPLOYEE_TIME_ACCOUNT_TXN_TYPES = ("opening", "credit", "debit", "correction")
EMPLOYEE_ADVANCE_STATUSES = ("requested", "approved", "disbursed", "settled", "cancelled")
EMPLOYEE_CREDENTIAL_TYPES = ("company_id", "work_badge")
EMPLOYEE_CREDENTIAL_STATUSES = ("draft", "issued", "revoked", "expired")


class Employee(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "default_branch_id"],
            ["core.branch.tenant_id", "core.branch.id"],
            name="fk_hr_employee_tenant_branch",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "default_mandate_id"],
            ["core.mandate.tenant_id", "core.mandate.id"],
            name="fk_hr_employee_tenant_mandate",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "personnel_no", name="uq_hr_employee_tenant_personnel_no"),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_tenant_id_id"),
        Index(
            "uq_hr_employee_tenant_user_id",
            "tenant_id",
            "user_id",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL AND archived_at IS NULL"),
        ),
        CheckConstraint(
            "termination_date IS NULL OR hire_date IS NULL OR termination_date >= hire_date",
            name="employee_hire_termination_valid",
        ),
        CheckConstraint(
            "target_weekly_hours IS NULL OR target_weekly_hours >= 0",
            name="employee_target_weekly_hours_non_negative",
        ),
        CheckConstraint(
            "target_monthly_hours IS NULL OR target_monthly_hours >= 0",
            name="employee_target_monthly_hours_non_negative",
        ),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    personnel_no: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    preferred_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    work_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    work_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mobile_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_branch_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    default_mandate_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    hire_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    termination_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    employment_type_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_weekly_hours: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    target_monthly_hours: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("iam.user_account.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    default_branch: Mapped[Branch | None] = relationship(foreign_keys=[default_branch_id], lazy="selectin")
    default_mandate: Mapped[Mandate | None] = relationship(foreign_keys=[default_mandate_id], lazy="selectin")
    user_account: Mapped[UserAccount | None] = relationship(lazy="selectin")
    private_profile: Mapped["EmployeePrivateProfile | None"] = relationship(
        back_populates="employee",
        lazy="selectin",
        uselist=False,
    )
    address_history: Mapped[list["EmployeeAddressHistory"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeAddressHistory.valid_from",
    )
    group_memberships: Mapped[list["EmployeeGroupMember"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeGroupMember.valid_from",
        overlaps="group,members",
    )
    activity_notes: Mapped[list["EmployeeNote"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeNote.created_at",
    )
    qualifications: Mapped[list["EmployeeQualification"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeQualification.valid_until",
    )
    availability_rules: Mapped[list["EmployeeAvailabilityRule"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeAvailabilityRule.starts_at",
    )
    absences: Mapped[list["EmployeeAbsence"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeAbsence.starts_on",
    )
    leave_balances: Mapped[list["EmployeeLeaveBalance"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeLeaveBalance.balance_year",
    )
    event_applications: Mapped[list["EmployeeEventApplication"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeEventApplication.applied_at",
    )
    time_accounts: Mapped[list["EmployeeTimeAccount"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeTimeAccount.account_type",
    )
    allowances: Mapped[list["EmployeeAllowance"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeAllowance.effective_from",
    )
    advances: Mapped[list["EmployeeAdvance"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeAdvance.requested_on",
    )
    credentials: Mapped[list["EmployeeIdCredential"]] = relationship(
        back_populates="employee",
        lazy="selectin",
        order_by="EmployeeIdCredential.valid_from",
    )


class EmployeePrivateProfile(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_private_profile"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_private_profile_tenant_employee",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "employee_id", name="uq_hr_employee_private_profile_employee"),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    private_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    private_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    place_of_birth: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nationality_country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    social_security_no: Mapped[str | None] = mapped_column(String(80), nullable=True)
    bank_account_holder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bank_iban: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bank_bic: Mapped[str | None] = mapped_column(String(64), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="private_profile", lazy="selectin")


class EmployeeAddressHistory(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_address_history"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_address_history_tenant_employee",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_address_history_tenant_id_id"),
        Index("ix_hr_employee_address_history_employee_window", "tenant_id", "employee_id", "address_type", "valid_from"),
        CheckConstraint("address_type IN ('home', 'mailing')", name="employee_address_type_valid"),
        CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="employee_address_window_valid"),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    address_id: Mapped[str] = mapped_column(ForeignKey("common.address.id", ondelete="RESTRICT"), nullable=False)
    address_type: Mapped[str] = mapped_column(String(40), nullable=False, default="home", server_default="home")
    valid_from: Mapped[date] = mapped_column(Date(), nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date(), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="address_history", lazy="selectin")
    address: Mapped[Address] = relationship(lazy="selectin")


class EmployeeGroup(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_group"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_hr_employee_group_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_group_tenant_id_id"),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    members: Mapped[list["EmployeeGroupMember"]] = relationship(
        back_populates="group",
        lazy="selectin",
        order_by="EmployeeGroupMember.valid_from",
        overlaps="employee,group_memberships",
    )


class EmployeeGroupMember(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_group_member"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_group_member_tenant_employee",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "group_id"],
            ["hr.employee_group.tenant_id", "hr.employee_group.id"],
            name="fk_hr_employee_group_member_tenant_group",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "employee_id",
            "group_id",
            "valid_from",
            name="uq_hr_employee_group_member_assignment",
        ),
        CheckConstraint("valid_until IS NULL OR valid_until >= valid_from", name="employee_group_member_window_valid"),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    group_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date(), nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date(), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(
        back_populates="group_memberships",
        lazy="selectin",
        overlaps="members",
    )
    group: Mapped[EmployeeGroup] = relationship(
        back_populates="members",
        lazy="selectin",
        overlaps="employee,group_memberships",
    )


class EmployeeNote(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_note"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_note_tenant_employee",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_note_tenant_id_id"),
        CheckConstraint(
            "note_type IN ('operational_note', 'positive_activity', 'reminder')",
            name="employee_note_type_valid",
        ),
        CheckConstraint(
            "completed_at IS NULL OR reminder_at IS NOT NULL OR note_type <> 'reminder'",
            name="employee_note_completion_requires_reminder",
        ),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    note_type: Mapped[str] = mapped_column(String(40), nullable=False, default="operational_note")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text(), nullable=True)
    reminder_at: Mapped[date | None] = mapped_column(Date(), nullable=True)
    completed_at: Mapped[date | None] = mapped_column(Date(), nullable=True)
    completed_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="activity_notes", lazy="selectin")


class FunctionType(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "function_type"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_hr_function_type_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_hr_function_type_tenant_id_id"),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    planning_relevant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))


class QualificationType(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "qualification_type"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_hr_qualification_type_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_hr_qualification_type_tenant_id_id"),
        CheckConstraint(
            "default_validity_days IS NULL OR default_validity_days > 0",
            name="qualification_type_default_validity_positive",
        ),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    planning_relevant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    compliance_relevant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    expiry_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    default_validity_days: Mapped[int | None] = mapped_column(nullable=True)
    proof_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))


class EmployeeQualification(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_qualification"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_qualification_tenant_employee",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "function_type_id"],
            ["hr.function_type.tenant_id", "hr.function_type.id"],
            name="fk_hr_employee_qualification_tenant_function_type",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_hr_employee_qualification_tenant_qualification_type",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_qualification_tenant_id_id"),
        Index(
            "ix_hr_employee_qualification_employee_kind_status",
            "tenant_id",
            "employee_id",
            "record_kind",
            "status",
        ),
        CheckConstraint(
            "record_kind IN ('function', 'qualification')",
            name="employee_qualification_record_kind_valid",
        ),
        CheckConstraint(
            "(record_kind = 'function' AND function_type_id IS NOT NULL AND qualification_type_id IS NULL) OR "
            "(record_kind = 'qualification' AND function_type_id IS NULL AND qualification_type_id IS NOT NULL)",
            name="employee_qualification_target_matches_kind",
        ),
        CheckConstraint(
            "valid_until IS NULL OR issued_at IS NULL OR valid_until >= issued_at",
            name="employee_qualification_valid_window",
        ),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    record_kind: Mapped[str] = mapped_column(String(40), nullable=False, default="qualification")
    function_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    qualification_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    certificate_no: Mapped[str | None] = mapped_column(String(120), nullable=True)
    issued_at: Mapped[date | None] = mapped_column(Date(), nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date(), nullable=True)
    issuing_authority: Mapped[str | None] = mapped_column(String(255), nullable=True)
    granted_internally: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="qualifications", lazy="selectin")
    function_type: Mapped[FunctionType | None] = relationship(lazy="selectin", overlaps="employee,qualifications")
    qualification_type: Mapped[QualificationType | None] = relationship(
        lazy="selectin",
        overlaps="employee,function_type,qualifications",
    )


class EmployeeAvailabilityRule(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_availability_rule"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_availability_rule_tenant_employee",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_availability_rule_tenant_id_id"),
        Index("ix_hr_employee_availability_rule_employee_start", "tenant_id", "employee_id", "starts_at"),
        CheckConstraint(
            "rule_kind IN ('availability', 'unavailable', 'free_wish')",
            name="employee_availability_rule_kind_valid",
        ),
        CheckConstraint(
            "recurrence_type IN ('none', 'weekly')",
            name="employee_availability_rule_recurrence_valid",
        ),
        CheckConstraint("ends_at > starts_at", name="employee_availability_rule_window_valid"),
        CheckConstraint(
            "(recurrence_type = 'none' AND weekday_mask IS NULL) OR "
            "(recurrence_type = 'weekly' AND weekday_mask IS NOT NULL)",
            name="employee_availability_rule_recurrence_fields_valid",
        ),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    rule_kind: Mapped[str] = mapped_column(String(40), nullable=False, default="availability")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recurrence_type: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    weekday_mask: Mapped[str | None] = mapped_column(String(7), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="availability_rules", lazy="selectin")


class EmployeeAbsence(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_absence"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_absence_tenant_employee",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_absence_tenant_id_id"),
        Index("ix_hr_employee_absence_employee_dates", "tenant_id", "employee_id", "starts_on", "ends_on"),
        CheckConstraint(
            "absence_type IN ('vacation', 'sickness', 'child_care', 'other')",
            name="employee_absence_type_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name="employee_absence_status_valid",
        ),
        CheckConstraint("ends_on >= starts_on", name="employee_absence_window_valid"),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    absence_type: Mapped[str] = mapped_column(String(40), nullable=False, default="vacation")
    starts_on: Mapped[date] = mapped_column(Date(), nullable=False)
    ends_on: Mapped[date] = mapped_column(Date(), nullable=False)
    quantity_days: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0, server_default=text("0"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    approved_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="absences", lazy="selectin")


class EmployeeLeaveBalance(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_leave_balance"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_leave_balance_tenant_employee",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "employee_id", "balance_year", name="uq_hr_employee_leave_balance_employee_year"),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_leave_balance_tenant_id_id"),
        CheckConstraint("balance_year >= 2000", name="employee_leave_balance_year_valid"),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    balance_year: Mapped[int] = mapped_column(Integer(), nullable=False)
    entitlement_days: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0, server_default=text("0"))
    carry_over_days: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0, server_default=text("0"))
    manual_adjustment_days: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0, server_default=text("0"))
    consumed_days: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0, server_default=text("0"))
    pending_days: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0, server_default=text("0"))
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="leave_balances", lazy="selectin")


class EmployeeEventApplication(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_event_application"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_event_application_tenant_employee",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "employee_id",
            "planning_record_id",
            name="uq_hr_employee_event_application_employee_planning_record",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_event_application_tenant_id_id"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'withdrawn')",
            name="employee_event_application_status_valid",
        ),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    planning_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    decided_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="event_applications", lazy="selectin")


class EmployeeTimeAccount(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_time_account"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_time_account_tenant_employee",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "employee_id", "account_type", name="uq_hr_employee_time_account_employee_type"),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_time_account_tenant_id_id"),
        CheckConstraint(
            "account_type IN ('work_time', 'overtime', 'flextime')",
            name="employee_time_account_type_valid",
        ),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    account_type: Mapped[str] = mapped_column(String(40), nullable=False, default="work_time")
    unit_code: Mapped[str] = mapped_column(String(20), nullable=False, default="minutes", server_default="minutes")
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="time_accounts", lazy="selectin")
    transactions: Mapped[list["EmployeeTimeAccountTxn"]] = relationship(
        back_populates="time_account",
        lazy="selectin",
        order_by="EmployeeTimeAccountTxn.posted_at",
    )


class EmployeeTimeAccountTxn(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "employee_time_account_txn"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "time_account_id"],
            ["hr.employee_time_account.tenant_id", "hr.employee_time_account.id"],
            name="fk_hr_employee_time_account_txn_tenant_account",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_time_account_txn_tenant_id_id"),
        CheckConstraint(
            "txn_type IN ('opening', 'credit', 'debit', 'correction')",
            name="employee_time_account_txn_type_valid",
        ),
        {"schema": "hr"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    time_account_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    txn_type: Mapped[str] = mapped_column(String(20), nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    amount_minutes: Mapped[int] = mapped_column(Integer(), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    time_account: Mapped[EmployeeTimeAccount] = relationship(back_populates="transactions", lazy="selectin")


class EmployeeAllowance(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_allowance"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_allowance_tenant_employee",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "function_type_id"],
            ["hr.function_type.tenant_id", "hr.function_type.id"],
            name="fk_hr_employee_allowance_tenant_function_type",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_hr_employee_allowance_tenant_qualification_type",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_allowance_tenant_id_id"),
        CheckConstraint("effective_until IS NULL OR effective_until >= effective_from", name="employee_allowance_window_valid"),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    basis_code: Mapped[str] = mapped_column(String(80), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default="EUR")
    function_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    qualification_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    effective_from: Mapped[date] = mapped_column(Date(), nullable=False)
    effective_until: Mapped[date | None] = mapped_column(Date(), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="allowances", lazy="selectin")
    function_type: Mapped[FunctionType | None] = relationship(lazy="selectin", overlaps="employee,allowances")
    qualification_type: Mapped[QualificationType | None] = relationship(
        lazy="selectin",
        overlaps="employee,function_type,allowances",
    )


class EmployeeAdvance(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_advance"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_advance_tenant_employee",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "advance_no", name="uq_hr_employee_advance_tenant_advance_no"),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_advance_tenant_id_id"),
        CheckConstraint(
            "status IN ('requested', 'approved', 'disbursed', 'settled', 'cancelled')",
            name="employee_advance_status_valid",
        ),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    advance_no: Mapped[str] = mapped_column(String(80), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    outstanding_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default="EUR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="requested", server_default="requested")
    requested_on: Mapped[date] = mapped_column(Date(), nullable=False)
    disbursed_on: Mapped[date | None] = mapped_column(Date(), nullable=True)
    settled_on: Mapped[date | None] = mapped_column(Date(), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="advances", lazy="selectin")


class EmployeeIdCredential(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "employee_id_credential"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_id_credential_tenant_employee",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "credential_no", name="uq_hr_employee_id_credential_tenant_credential_no"),
        UniqueConstraint("tenant_id", "encoded_value", name="uq_hr_employee_id_credential_tenant_encoded_value"),
        UniqueConstraint("tenant_id", "id", name="uq_hr_employee_id_credential_tenant_id_id"),
        CheckConstraint(
            "credential_type IN ('company_id', 'work_badge')",
            name="employee_id_credential_type_valid",
        ),
        CheckConstraint(
            "status IN ('draft', 'issued', 'revoked', 'expired')",
            name="employee_id_credential_status_valid",
        ),
        CheckConstraint("valid_until IS NULL OR valid_until >= valid_from", name="employee_id_credential_window_valid"),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    credential_no: Mapped[str] = mapped_column(String(120), nullable=False)
    credential_type: Mapped[str] = mapped_column(String(40), nullable=False, default="company_id")
    encoded_value: Mapped[str] = mapped_column(String(255), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date(), nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date(), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft")
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    employee: Mapped[Employee] = relationship(back_populates="credentials", lazy="selectin")
