"""Partner subcontractor master, history, contacts, scopes, and finance profile."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditLifecycleMixin, Base, UUIDPrimaryKeyMixin
from app.modules.core.models import Address, Branch, LookupValue, Mandate
from app.modules.employees.models import (
    EMPLOYEE_CREDENTIAL_STATUSES,
    EMPLOYEE_CREDENTIAL_TYPES,
    QualificationType,
)
from app.modules.iam.models import UserAccount


class Subcontractor(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor"
    __table_args__ = (
        UniqueConstraint("tenant_id", "subcontractor_number", name="uq_partner_subcontractor_tenant_number"),
        UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_tenant_id_id"),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)",
            name="partner_subcontractor_coordinates_valid",
        ),
        {"schema": "partner"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    subcontractor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    legal_form_lookup_id: Mapped[str | None] = mapped_column(ForeignKey("core.lookup_value.id", ondelete="SET NULL"), nullable=True)
    subcontractor_status_lookup_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.lookup_value.id", ondelete="SET NULL"),
        nullable=True,
    )
    managing_director_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_id: Mapped[str | None] = mapped_column(ForeignKey("common.address.id", ondelete="SET NULL"), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    address: Mapped[Address | None] = relationship(lazy="selectin")
    legal_form_lookup: Mapped[LookupValue | None] = relationship(foreign_keys=[legal_form_lookup_id], lazy="selectin")
    subcontractor_status_lookup: Mapped[LookupValue | None] = relationship(
        foreign_keys=[subcontractor_status_lookup_id],
        lazy="selectin",
    )
    contacts: Mapped[list["SubcontractorContact"]] = relationship(
        back_populates="subcontractor",
        lazy="selectin",
        order_by="SubcontractorContact.full_name",
    )
    scopes: Mapped[list["SubcontractorScope"]] = relationship(
        back_populates="subcontractor",
        lazy="selectin",
        order_by="SubcontractorScope.valid_from",
    )
    finance_profile: Mapped["SubcontractorFinanceProfile | None"] = relationship(
        back_populates="subcontractor",
        lazy="selectin",
        uselist=False,
    )
    history_entries: Mapped[list["SubcontractorHistoryEntry"]] = relationship(
        back_populates="subcontractor",
        lazy="selectin",
        order_by=lambda: (
            SubcontractorHistoryEntry.occurred_at.desc(),
            SubcontractorHistoryEntry.created_at.desc(),
        ),
    )
    workers: Mapped[list["SubcontractorWorker"]] = relationship(
        back_populates="subcontractor",
        lazy="selectin",
        order_by="SubcontractorWorker.worker_no",
    )


class SubcontractorContact(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_contact"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_id"],
            ["partner.subcontractor.tenant_id", "partner.subcontractor.id"],
            name="fk_partner_subcontractor_contact_tenant_subcontractor",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_contact_tenant_id_id"),
        Index("ix_partner_subcontractor_contact_tenant_subcontractor", "tenant_id", "subcontractor_id"),
        Index(
            "uq_partner_subcontractor_contact_primary_per_company",
            "tenant_id",
            "subcontractor_id",
            unique=True,
            postgresql_where=text("is_primary_contact = true AND archived_at IS NULL"),
        ),
        Index(
            "uq_partner_subcontractor_contact_tenant_user_id",
            "tenant_id",
            "user_id",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL AND archived_at IS NULL"),
        ),
        {"schema": "partner"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    subcontractor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    function_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    portal_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("iam.user_account.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    subcontractor: Mapped[Subcontractor] = relationship(back_populates="contacts", lazy="selectin")
    user_account: Mapped[UserAccount | None] = relationship(lazy="selectin")


class SubcontractorScope(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_scope"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_id"],
            ["partner.subcontractor.tenant_id", "partner.subcontractor.id"],
            name="fk_partner_subcontractor_scope_tenant_subcontractor",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "branch_id"],
            ["core.branch.tenant_id", "core.branch.id"],
            name="fk_partner_subcontractor_scope_tenant_branch",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "mandate_id"],
            ["core.mandate.tenant_id", "core.mandate.id"],
            name="fk_partner_subcontractor_scope_tenant_mandate",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_scope_tenant_id_id"),
        CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="partner_subcontractor_scope_window_valid"),
        {"schema": "partner"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    subcontractor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    branch_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    mandate_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    valid_from: Mapped[date] = mapped_column(nullable=False)
    valid_to: Mapped[date | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    subcontractor: Mapped[Subcontractor] = relationship(back_populates="scopes", lazy="selectin")
    branch: Mapped[Branch] = relationship(foreign_keys=[branch_id], lazy="selectin")
    mandate: Mapped[Mandate | None] = relationship(foreign_keys=[mandate_id], lazy="selectin")


class SubcontractorFinanceProfile(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_finance_profile"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_id"],
            ["partner.subcontractor.tenant_id", "partner.subcontractor.id"],
            name="fk_partner_subcontractor_finance_profile_tenant_subcontractor",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "subcontractor_id", name="uq_partner_subcontractor_finance_profile_company"),
        {"schema": "partner"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    subcontractor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    invoice_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_terms_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_terms_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    vat_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bank_account_holder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bank_iban: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bank_bic: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_delivery_method_lookup_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.lookup_value.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_status_mode_lookup_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.lookup_value.id", ondelete="SET NULL"),
        nullable=True,
    )
    billing_note: Mapped[str | None] = mapped_column(Text(), nullable=True)

    subcontractor: Mapped[Subcontractor] = relationship(back_populates="finance_profile", lazy="selectin")
    invoice_delivery_method_lookup: Mapped[LookupValue | None] = relationship(
        foreign_keys=[invoice_delivery_method_lookup_id],
        lazy="selectin",
    )
    invoice_status_mode_lookup: Mapped[LookupValue | None] = relationship(
        foreign_keys=[invoice_status_mode_lookup_id],
        lazy="selectin",
    )


class SubcontractorRateCard(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_rate_card"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_id"],
            ["partner.subcontractor.tenant_id", "partner.subcontractor.id"],
            name="fk_partner_subcontractor_rate_card_tenant_subcontractor",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_rate_card_tenant_id_id"),
        UniqueConstraint("tenant_id", "subcontractor_id", "code", name="uq_partner_subcontractor_rate_card_code"),
        CheckConstraint("effective_until IS NULL OR effective_until >= effective_from", name="partner_subcontractor_rate_card_window_valid"),
        CheckConstraint("status_code IN ('draft','active','archived')", name="partner_subcontractor_rate_card_status_valid"),
        Index("ix_partner_subcontractor_rate_card_window", "tenant_id", "subcontractor_id", "effective_from"),
        {"schema": "partner"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    subcontractor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    effective_from: Mapped[date] = mapped_column(nullable=False)
    effective_until: Mapped[date | None] = mapped_column(nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default="EUR")
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    subcontractor: Mapped[Subcontractor] = relationship(lazy="selectin")
    rate_lines: Mapped[list["SubcontractorRateLine"]] = relationship(
        back_populates="rate_card",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="SubcontractorRateLine.created_at",
    )


class SubcontractorRateLine(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_rate_line"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "rate_card_id"],
            ["partner.subcontractor_rate_card.tenant_id", "partner.subcontractor_rate_card.id"],
            name="fk_partner_subcontractor_rate_line_tenant_rate_card",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "function_type_id"],
            ["hr.function_type.tenant_id", "hr.function_type.id"],
            name="fk_partner_subcontractor_rate_line_tenant_function_type",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_partner_subcontractor_rate_line_tenant_qualification_type",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_rate_line_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "rate_card_id",
            "function_type_id",
            "qualification_type_id",
            "billing_unit_code",
            name="uq_partner_subcontractor_rate_line_dimensions",
        ),
        CheckConstraint("billing_unit_code IN ('hour','day','flat')", name="partner_subcontractor_rate_line_billing_unit_valid"),
        CheckConstraint("unit_price >= 0", name="partner_subcontractor_rate_line_unit_price_nonnegative"),
        CheckConstraint("minimum_quantity IS NULL OR minimum_quantity >= 0", name="partner_subcontractor_rate_line_minimum_nonnegative"),
        {"schema": "partner"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    rate_card_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    function_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    qualification_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    line_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_unit_code: Mapped[str] = mapped_column(String(20), nullable=False, default="hour", server_default="hour")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    minimum_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    rate_card: Mapped[SubcontractorRateCard] = relationship(back_populates="rate_lines", lazy="selectin")
    function_type: Mapped[FunctionType | None] = relationship(lazy="selectin", overlaps="qualification_type,rate_card,rate_lines")
    qualification_type: Mapped[QualificationType | None] = relationship(lazy="selectin", overlaps="function_type,rate_card,rate_lines")


class SubcontractorHistoryEntry(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "subcontractor_history_entry"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_id"],
            ["partner.subcontractor.tenant_id", "partner.subcontractor.id"],
            name="fk_partner_subcontractor_history_tenant_subcontractor",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_partner_subcontractor_history_company_occurred",
            "tenant_id",
            "subcontractor_id",
            "occurred_at",
            "created_at",
        ),
        {"schema": "partner"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    subcontractor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("iam.user_account.id", name="fk_partner_history_actor_user_account", ondelete="SET NULL"),
        nullable=True,
    )
    related_contact_id: Mapped[str | None] = mapped_column(
        ForeignKey("partner.subcontractor_contact.id", name="fk_partner_history_contact_subcontractor_contact", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    subcontractor: Mapped[Subcontractor] = relationship(back_populates="history_entries", lazy="selectin")
    actor_user: Mapped[UserAccount | None] = relationship(foreign_keys=[actor_user_id], lazy="selectin")
    related_contact: Mapped[SubcontractorContact | None] = relationship(foreign_keys=[related_contact_id], lazy="selectin")


class SubcontractorWorker(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_worker"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_id"],
            ["partner.subcontractor.tenant_id", "partner.subcontractor.id"],
            name="fk_partner_subcontractor_worker_tenant_subcontractor",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "subcontractor_id", "worker_no", name="uq_partner_subcontractor_worker_company_worker_no"),
        UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_worker_tenant_id_id"),
        {"schema": "partner"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    subcontractor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    worker_no: Mapped[str] = mapped_column(String(80), nullable=False)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    preferred_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    subcontractor: Mapped[Subcontractor] = relationship(back_populates="workers", lazy="selectin")
    qualifications: Mapped[list["SubcontractorWorkerQualification"]] = relationship(
        back_populates="worker",
        lazy="selectin",
        order_by="SubcontractorWorkerQualification.valid_until",
    )
    credentials: Mapped[list["SubcontractorWorkerCredential"]] = relationship(
        back_populates="worker",
        lazy="selectin",
        order_by="SubcontractorWorkerCredential.valid_from",
    )


class SubcontractorWorkerQualification(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_worker_qualification"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_partner_worker_qualification_tenant_worker",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_partner_worker_qualification_tenant_qualification_type",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_worker_qualification_tenant_id_id"),
        Index(
            "ix_partner_worker_qualification_worker_status",
            "tenant_id",
            "worker_id",
            "status",
            "valid_until",
        ),
        CheckConstraint(
            "valid_until IS NULL OR issued_at IS NULL OR valid_until >= issued_at",
            name="partner_worker_qualification_valid_window",
        ),
        {"schema": "partner"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    worker_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    qualification_type_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    certificate_no: Mapped[str | None] = mapped_column(String(120), nullable=True)
    issued_at: Mapped[date | None] = mapped_column(nullable=True)
    valid_until: Mapped[date | None] = mapped_column(nullable=True)
    issuing_authority: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    worker: Mapped[SubcontractorWorker] = relationship(back_populates="qualifications", lazy="selectin")
    qualification_type: Mapped[QualificationType] = relationship(lazy="selectin", overlaps="qualifications,worker")


class SubcontractorWorkerCredential(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_worker_credential"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_partner_worker_credential_tenant_worker",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "credential_no", name="uq_partner_worker_credential_tenant_credential_no"),
        UniqueConstraint("tenant_id", "encoded_value", name="uq_partner_worker_credential_tenant_encoded_value"),
        UniqueConstraint("tenant_id", "id", name="uq_partner_worker_credential_tenant_id_id"),
        CheckConstraint(
            f"credential_type IN {EMPLOYEE_CREDENTIAL_TYPES}",
            name="partner_worker_credential_type_valid",
        ),
        CheckConstraint(
            f"status IN {EMPLOYEE_CREDENTIAL_STATUSES}",
            name="partner_worker_credential_status_valid",
        ),
        CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="partner_worker_credential_window_valid",
        ),
        {"schema": "partner"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    worker_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    credential_no: Mapped[str] = mapped_column(String(120), nullable=False)
    credential_type: Mapped[str] = mapped_column(String(40), nullable=False, default="company_id")
    encoded_value: Mapped[str] = mapped_column(String(255), nullable=False)
    valid_from: Mapped[date] = mapped_column(nullable=False)
    valid_until: Mapped[date | None] = mapped_column(nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    worker: Mapped[SubcontractorWorker] = relationship(back_populates="credentials", lazy="selectin")
