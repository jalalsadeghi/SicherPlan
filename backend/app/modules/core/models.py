"""Core backbone models for tenant, branch, mandate, settings, and lookups."""

from __future__ import annotations

from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditLifecycleMixin, Base, UUIDPrimaryKeyMixin


class Address(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "address"
    __table_args__ = {"schema": "common"}

    street_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    street_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(32), nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)

    branches: Mapped[list["Branch"]] = relationship(back_populates="address")


class Tenant(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "tenant"
    __table_args__ = (
        UniqueConstraint("code", name="uq_core_tenant_code"),
        {"schema": "core"},
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_locale: Mapped[str] = mapped_column(String(10), nullable=False, default="de")
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Berlin")

    branches: Mapped[list["Branch"]] = relationship(back_populates="tenant")
    mandates: Mapped[list["Mandate"]] = relationship(back_populates="tenant")
    settings: Mapped[list["TenantSetting"]] = relationship(back_populates="tenant")
    lookup_values: Mapped[list["LookupValue"]] = relationship(back_populates="tenant")


class Branch(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "branch"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_core_branch_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_core_branch_tenant_id_id"),
        {"schema": "core"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address_id: Mapped[str | None] = mapped_column(
        ForeignKey("common.address.id", ondelete="SET NULL"),
        nullable=True,
    )
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="branches")
    address: Mapped[Address | None] = relationship(back_populates="branches")
    mandates: Mapped[list["Mandate"]] = relationship(
        back_populates="branch",
        overlaps="tenant,mandates",
    )


class Mandate(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "mandate"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "branch_id"],
            ["core.branch.tenant_id", "core.branch.id"],
            ondelete="RESTRICT",
            name="fk_core_mandate_tenant_branch",
        ),
        UniqueConstraint("tenant_id", "code", name="uq_core_mandate_tenant_code"),
        {"schema": "core"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    branch_id: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    tenant: Mapped["Tenant"] = relationship(
        back_populates="mandates",
        overlaps="branch,mandates",
    )
    branch: Mapped["Branch"] = relationship(
        back_populates="mandates",
        overlaps="mandates,tenant",
    )


class TenantSetting(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "tenant_setting"
    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_core_tenant_setting_tenant_key"),
        {"schema": "core"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="settings")


class LookupValue(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "lookup_value"
    __table_args__ = (
        Index(
            "uq_core_lookup_value_system_domain_code",
            "domain",
            "code",
            unique=True,
            postgresql_where=text("tenant_id IS NULL"),
        ),
        Index(
            "uq_core_lookup_value_tenant_domain_code",
            "tenant_id",
            "domain",
            "code",
            unique=True,
            postgresql_where=text("tenant_id IS NOT NULL"),
        ),
        {"schema": "core"},
    )

    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=True,
    )
    domain: Mapped[str] = mapped_column(String(80), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        server_default="100",
    )

    tenant: Mapped["Tenant | None"] = relationship(back_populates="lookup_values")
