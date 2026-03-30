"""CRM customer master, commercial settings, pricing rules, contacts, and reusable-address linkage models."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Index,
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
from app.modules.iam.models import UserAccount

if TYPE_CHECKING:
    from app.modules.employees.models import FunctionType, QualificationType


CUSTOMER_ADDRESS_TYPES = ("registered", "billing", "mailing", "service")


class Customer(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "default_branch_id"],
            ["core.branch.tenant_id", "core.branch.id"],
            name="fk_crm_customer_tenant_branch",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "default_mandate_id"],
            ["core.mandate.tenant_id", "core.mandate.id"],
            name="fk_crm_customer_tenant_mandate",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "customer_number", name="uq_crm_customer_tenant_customer_number"),
        UniqueConstraint("tenant_id", "id", name="uq_crm_customer_tenant_id_id"),
        {"schema": "crm"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    legal_form_lookup_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.lookup_value.id", ondelete="SET NULL"),
        nullable=True,
    )
    classification_lookup_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.lookup_value.id", ondelete="SET NULL"),
        nullable=True,
    )
    ranking_lookup_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.lookup_value.id", ondelete="SET NULL"),
        nullable=True,
    )
    customer_status_lookup_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.lookup_value.id", ondelete="SET NULL"),
        nullable=True,
    )
    default_branch_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    default_mandate_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    portal_person_names_released: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    portal_person_names_released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    portal_person_names_released_by_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
    )

    default_branch: Mapped[Branch | None] = relationship(foreign_keys=[default_branch_id], lazy="selectin")
    default_mandate: Mapped[Mandate | None] = relationship(foreign_keys=[default_mandate_id], lazy="selectin")
    legal_form_lookup: Mapped[LookupValue | None] = relationship(
        foreign_keys=[legal_form_lookup_id],
        lazy="selectin",
    )
    classification_lookup: Mapped[LookupValue | None] = relationship(
        foreign_keys=[classification_lookup_id],
        lazy="selectin",
    )
    ranking_lookup: Mapped[LookupValue | None] = relationship(
        foreign_keys=[ranking_lookup_id],
        lazy="selectin",
    )
    customer_status_lookup: Mapped[LookupValue | None] = relationship(
        foreign_keys=[customer_status_lookup_id],
        lazy="selectin",
    )
    contacts: Mapped[list["CustomerContact"]] = relationship(
        back_populates="customer",
        lazy="selectin",
        order_by="CustomerContact.full_name",
    )
    billing_profile: Mapped["CustomerBillingProfile | None"] = relationship(
        back_populates="customer",
        lazy="selectin",
        uselist=False,
    )
    invoice_parties: Mapped[list["CustomerInvoiceParty"]] = relationship(
        back_populates="customer",
        lazy="selectin",
        order_by="CustomerInvoiceParty.company_name",
    )
    rate_cards: Mapped[list["CustomerRateCard"]] = relationship(
        back_populates="customer",
        lazy="selectin",
        order_by="CustomerRateCard.effective_from",
    )
    addresses: Mapped[list["CustomerAddressLink"]] = relationship(
        back_populates="customer",
        lazy="selectin",
        order_by="CustomerAddressLink.address_type",
    )
    history_entries: Mapped[list["CustomerHistoryEntry"]] = relationship(
        back_populates="customer",
        lazy="selectin",
        order_by="desc(CustomerHistoryEntry.created_at)",
    )
    employee_blocks: Mapped[list["CustomerEmployeeBlock"]] = relationship(
        back_populates="customer",
        lazy="selectin",
        order_by="CustomerEmployeeBlock.effective_from",
    )


class CustomerContact(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer_contact"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_crm_customer_contact_tenant_customer",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_crm_customer_contact_tenant_id_id"),
        Index("ix_crm_customer_contact_tenant_customer", "tenant_id", "customer_id"),
        Index(
            "uq_crm_customer_contact_primary_per_customer",
            "tenant_id",
            "customer_id",
            unique=True,
            postgresql_where=text("is_primary_contact = true AND archived_at IS NULL"),
        ),
        Index(
            "uq_crm_customer_contact_tenant_user_id",
            "tenant_id",
            "user_id",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL AND archived_at IS NULL"),
        ),
        {"schema": "crm"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    function_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_primary_contact: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    is_billing_contact: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="contacts", lazy="selectin")
    user_account: Mapped[UserAccount | None] = relationship(lazy="selectin")


class CustomerBillingProfile(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer_billing_profile"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_crm_customer_billing_profile_tenant_customer",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "customer_id", name="uq_crm_customer_billing_profile_customer"),
        UniqueConstraint("tenant_id", "id", name="uq_crm_customer_billing_profile_tenant_id_id"),
        {"schema": "crm"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    invoice_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_terms_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_terms_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    vat_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tax_exempt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    tax_exemption_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bank_account_holder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bank_iban: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bank_bic: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contract_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    debtor_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    e_invoice_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    leitweg_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    invoice_layout_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    shipping_method_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    dunning_policy_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    billing_note: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="billing_profile", lazy="selectin")


class CustomerInvoiceParty(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer_invoice_party"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_crm_customer_invoice_party_tenant_customer",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_crm_customer_invoice_party_tenant_id_id"),
        Index("ix_crm_customer_invoice_party_customer", "tenant_id", "customer_id"),
        Index(
            "uq_crm_customer_invoice_party_default_per_customer",
            "tenant_id",
            "customer_id",
            unique=True,
            postgresql_where=text("is_default = true AND archived_at IS NULL"),
        ),
        {"schema": "crm"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_id: Mapped[str] = mapped_column(ForeignKey("common.address.id", ondelete="RESTRICT"), nullable=False)
    invoice_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_layout_lookup_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.lookup_value.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    note: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="invoice_parties", lazy="selectin")
    address: Mapped[Address] = relationship(lazy="selectin")
    invoice_layout_lookup: Mapped[LookupValue | None] = relationship(
        foreign_keys=[invoice_layout_lookup_id],
        lazy="selectin",
    )


class CustomerAddressLink(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer_address"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_crm_customer_address_tenant_customer",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_crm_customer_address_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "customer_id",
            "address_id",
            "address_type",
            name="uq_crm_customer_address_customer_address_type",
        ),
        CheckConstraint(
            "address_type IN ('registered', 'billing', 'mailing', 'service')",
            name="crm_customer_address_type_valid",
        ),
        Index("ix_crm_customer_address_tenant_customer_type", "tenant_id", "customer_id", "address_type"),
        Index(
            "uq_crm_customer_address_default_per_type",
            "tenant_id",
            "customer_id",
            "address_type",
            unique=True,
            postgresql_where=text("is_default = true AND archived_at IS NULL"),
        ),
        {"schema": "crm"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    address_id: Mapped[str] = mapped_column(
        ForeignKey("common.address.id", ondelete="RESTRICT"),
        nullable=False,
    )
    address_type: Mapped[str] = mapped_column(String(40), nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    customer: Mapped[Customer] = relationship(back_populates="addresses", lazy="selectin")
    address: Mapped[Address] = relationship(lazy="selectin")


class CustomerRateCard(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer_rate_card"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_crm_customer_rate_card_tenant_customer",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_crm_customer_rate_card_tenant_id_id"),
        Index("ix_crm_customer_rate_card_customer_effective", "tenant_id", "customer_id", "effective_from"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="crm_customer_rate_card_effective_window_valid",
        ),
        {"schema": "crm"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    rate_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    effective_from: Mapped[date] = mapped_column(nullable=False)
    effective_to: Mapped[date | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="rate_cards", lazy="selectin")
    rate_lines: Mapped[list["CustomerRateLine"]] = relationship(
        back_populates="rate_card",
        lazy="selectin",
        order_by="CustomerRateLine.sort_order",
    )
    surcharge_rules: Mapped[list["CustomerSurchargeRule"]] = relationship(
        back_populates="rate_card",
        lazy="selectin",
        order_by="CustomerSurchargeRule.sort_order",
    )


class CustomerRateLine(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer_rate_line"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "rate_card_id"],
            ["crm.customer_rate_card.tenant_id", "crm.customer_rate_card.id"],
            name="fk_crm_customer_rate_line_tenant_rate_card",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "function_type_id"],
            ["hr.function_type.tenant_id", "hr.function_type.id"],
            name="fk_crm_customer_rate_line_tenant_function_type",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_crm_customer_rate_line_tenant_qualification_type",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_crm_customer_rate_line_tenant_id_id"),
        Index("ix_crm_customer_rate_line_rate_card", "tenant_id", "rate_card_id"),
        CheckConstraint("unit_price >= 0", name="crm_customer_rate_line_unit_price_non_negative"),
        CheckConstraint(
            "minimum_quantity IS NULL OR minimum_quantity >= 0",
            name="crm_customer_rate_line_minimum_quantity_non_negative",
        ),
        {"schema": "crm"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rate_card_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    line_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    function_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    qualification_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    planning_mode_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    billing_unit: Mapped[str] = mapped_column(String(40), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    minimum_quantity: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    rate_card: Mapped[CustomerRateCard] = relationship(back_populates="rate_lines", lazy="selectin")
    function_type: Mapped["FunctionType | None"] = relationship(
        "FunctionType",
        lazy="selectin",
        foreign_keys=[function_type_id],
    )
    qualification_type: Mapped["QualificationType | None"] = relationship(
        "QualificationType",
        lazy="selectin",
        foreign_keys=[qualification_type_id],
    )


class CustomerSurchargeRule(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer_surcharge_rule"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "rate_card_id"],
            ["crm.customer_rate_card.tenant_id", "crm.customer_rate_card.id"],
            name="fk_crm_customer_surcharge_rule_tenant_rate_card",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_crm_customer_surcharge_rule_tenant_id_id"),
        Index("ix_crm_customer_surcharge_rule_rate_card", "tenant_id", "rate_card_id"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="crm_customer_surcharge_rule_effective_window_valid",
        ),
        CheckConstraint(
            "weekday_mask IS NULL OR char_length(weekday_mask) = 7",
            name="crm_customer_surcharge_rule_weekday_mask_length",
        ),
        CheckConstraint(
            "time_from_minute IS NULL OR (time_from_minute >= 0 AND time_from_minute <= 1439)",
            name="crm_customer_surcharge_rule_time_from_range",
        ),
        CheckConstraint(
            "time_to_minute IS NULL OR (time_to_minute >= 1 AND time_to_minute <= 1440)",
            name="crm_customer_surcharge_rule_time_to_range",
        ),
        CheckConstraint(
            "percent_value IS NULL OR percent_value >= 0",
            name="crm_customer_surcharge_rule_percent_non_negative",
        ),
        CheckConstraint(
            "fixed_amount IS NULL OR fixed_amount >= 0",
            name="crm_customer_surcharge_rule_fixed_amount_non_negative",
        ),
        {"schema": "crm"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rate_card_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    surcharge_type: Mapped[str] = mapped_column(String(40), nullable=False)
    effective_from: Mapped[date] = mapped_column(nullable=False)
    effective_to: Mapped[date | None] = mapped_column(nullable=True)
    weekday_mask: Mapped[str | None] = mapped_column(String(7), nullable=True)
    time_from_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_to_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    percent_value: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    fixed_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    rate_card: Mapped[CustomerRateCard] = relationship(back_populates="surcharge_rules", lazy="selectin")


class CustomerHistoryEntry(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "customer_history_entry"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_crm_customer_history_entry_tenant_customer",
            ondelete="RESTRICT",
        ),
        Index("ix_crm_customer_history_entry_customer_created_at", "tenant_id", "customer_id", "created_at"),
        {"schema": "crm"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text(), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "iam.user_account.id",
            name="fk_crm_history_actor_user_account",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    related_contact_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "crm.customer_contact.id",
            name="fk_crm_history_contact_customer_contact",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    related_address_link_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "crm.customer_address.id",
            name="fk_crm_history_addr_link_customer_address",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    integration_job_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "integration.import_export_job.id",
            name="fk_crm_history_job_import_export_job",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    before_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    after_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    customer: Mapped[Customer] = relationship(back_populates="history_entries", lazy="selectin")
    actor_user: Mapped[UserAccount | None] = relationship(foreign_keys=[actor_user_id], lazy="selectin")


class CustomerEmployeeBlock(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer_employee_block"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_crm_customer_employee_block_tenant_customer",
            ondelete="RESTRICT",
        ),
        Index("ix_crm_customer_employee_block_customer_effective", "tenant_id", "customer_id", "effective_from"),
        Index("ix_crm_customer_employee_block_employee", "tenant_id", "employee_id"),
        {"schema": "crm"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    # The FK to hr.employee is intentionally deferred until the employees module lands.
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    effective_from: Mapped[date] = mapped_column(nullable=False)
    effective_to: Mapped[date | None] = mapped_column(nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="employee_blocks", lazy="selectin")
