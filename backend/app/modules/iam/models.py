"""IAM foundation models for users, roles, scopes, identities, and sessions."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditLifecycleMixin, Base, TimestampedMixin, UUIDPrimaryKeyMixin


ROLE_SCOPE_TYPES = ("tenant", "branch", "mandate", "customer", "subcontractor")


class UserAccount(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "user_account"
    __table_args__ = (
        UniqueConstraint("tenant_id", "username", name="uq_iam_user_account_tenant_username"),
        UniqueConstraint("tenant_id", "email", name="uq_iam_user_account_tenant_email"),
        {"schema": "iam"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    username: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="de", server_default="de")
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="Europe/Berlin",
        server_default="Europe/Berlin",
    )
    is_platform_user: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    is_password_login_enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)

    external_identities: Mapped[list["ExternalIdentity"]] = relationship(back_populates="user_account")
    role_assignments: Mapped[list["UserRoleAssignment"]] = relationship(back_populates="user_account")
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user_account")


class ExternalIdentity(UUIDPrimaryKeyMixin, TimestampedMixin, Base):
    __tablename__ = "external_identity"
    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_iam_external_identity_provider_subject"),
        UniqueConstraint("provider", "provider_user_name", name="uq_iam_external_identity_provider_username"),
        {"schema": "iam"},
    )

    user_account_id: Mapped[str] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_user_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    claims_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    linked_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user_account: Mapped["UserAccount"] = relationship(back_populates="external_identities")


class Role(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "role"
    __table_args__ = (
        UniqueConstraint("key", name="uq_iam_role_key"),
        {"schema": "iam"},
    )

    key: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_portal_role: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    is_system_role: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))

    permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role")
    assignments: Mapped[list["UserRoleAssignment"]] = relationship(back_populates="role")


class Permission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "permission"
    __table_args__ = (
        UniqueConstraint("key", name="uq_iam_permission_key"),
        {"schema": "iam"},
    )

    key: Mapped[str] = mapped_column(String(160), nullable=False)
    module: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    role_links: Mapped[list["RolePermission"]] = relationship(back_populates="permission")


class RolePermission(Base):
    __tablename__ = "role_permission"
    __table_args__ = {"schema": "iam"}

    role_id: Mapped[str] = mapped_column(
        ForeignKey("iam.role.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[str] = mapped_column(
        ForeignKey("iam.permission.id", ondelete="CASCADE"),
        primary_key=True,
    )
    granted_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    role: Mapped["Role"] = relationship(back_populates="permissions")
    permission: Mapped["Permission"] = relationship(back_populates="role_links")


class UserRoleAssignment(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "user_role_assignment"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "branch_id"],
            ["core.branch.tenant_id", "core.branch.id"],
            name="fk_iam_user_role_assignment_tenant_branch",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "mandate_id"],
            ["core.mandate.tenant_id", "core.mandate.id"],
            name="fk_iam_user_role_assignment_tenant_mandate",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "user_account_id",
            "role_id",
            "scope_type",
            "tenant_id",
            "branch_id",
            "mandate_id",
            "customer_id",
            "subcontractor_id",
            name="uq_iam_user_role_assignment_scope_tuple",
        ),
        CheckConstraint(
            "scope_type IN ('tenant', 'branch', 'mandate', 'customer', 'subcontractor')",
            name="scope_type_valid",
        ),
        CheckConstraint(
            "(scope_type = 'tenant' AND branch_id IS NULL AND mandate_id IS NULL AND customer_id IS NULL AND subcontractor_id IS NULL) OR "
            "(scope_type = 'branch' AND branch_id IS NOT NULL AND mandate_id IS NULL AND customer_id IS NULL AND subcontractor_id IS NULL) OR "
            "(scope_type = 'mandate' AND branch_id IS NULL AND mandate_id IS NOT NULL AND customer_id IS NULL AND subcontractor_id IS NULL) OR "
            "(scope_type = 'customer' AND branch_id IS NULL AND mandate_id IS NULL AND customer_id IS NOT NULL AND subcontractor_id IS NULL) OR "
            "(scope_type = 'subcontractor' AND branch_id IS NULL AND mandate_id IS NULL AND customer_id IS NULL AND subcontractor_id IS NOT NULL)",
            name="scope_target_matches_type",
        ),
        {"schema": "iam"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_account_id: Mapped[str] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[str] = mapped_column(
        ForeignKey("iam.role.id", ondelete="CASCADE"),
        nullable=False,
    )
    scope_type: Mapped[str] = mapped_column(String(40), nullable=False, default="tenant", server_default="tenant")
    branch_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    mandate_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    customer_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    subcontractor_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    valid_from: Mapped[datetime | None] = mapped_column(nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(nullable=True)

    user_account: Mapped["UserAccount"] = relationship(back_populates="role_assignments")
    role: Mapped["Role"] = relationship(back_populates="assignments")


class UserSession(UUIDPrimaryKeyMixin, TimestampedMixin, Base):
    __tablename__ = "user_session"
    __table_args__ = (
        UniqueConstraint("session_token_hash", name="uq_iam_user_session_token_hash"),
        Index("ix_iam_user_session_user_account_revoked_at", "user_account_id", "revoked_at"),
        {"schema": "iam"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_account_id: Mapped[str] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    refresh_token_family: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="active", server_default="active")
    issued_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    device_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text(), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    user_account: Mapped["UserAccount"] = relationship(back_populates="sessions")


class PasswordResetToken(UUIDPrimaryKeyMixin, TimestampedMixin, Base):
    __tablename__ = "password_reset_token"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_iam_password_reset_token_hash"),
        Index("ix_iam_password_reset_token_user_account_used_at", "user_account_id", "used_at"),
        {"schema": "iam"},
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_account_id: Mapped[str] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    requested_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    requested_user_agent: Mapped[str | None] = mapped_column(Text(), nullable=True)
    delivery_channel: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="email",
        server_default="email",
    )
    delivery_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
