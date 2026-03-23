"""subcontractor worker foundation

Revision ID: 0027_subcontractor_worker_foundation
Revises: 0026_subcontractor_history_and_lifecycle
Create Date: 2026-03-19 18:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0027_subcontractor_worker_foundation"
down_revision = "0026_subcontractor_history_and_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subcontractor_worker",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("subcontractor_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("worker_no", sa.String(length=80), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("preferred_name", sa.String(length=120), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("mobile", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "subcontractor_id"],
            ["partner.subcontractor.tenant_id", "partner.subcontractor.id"],
            name="fk_partner_subcontractor_worker_tenant_subcontractor",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_worker_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "subcontractor_id", "worker_no", name="uq_partner_subcontractor_worker_company_worker_no"),
        schema="partner",
    )
    op.create_table(
        "subcontractor_worker_qualification",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("worker_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("qualification_type_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("certificate_no", sa.String(length=120), nullable=True),
        sa.Column("issued_at", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("issuing_authority", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_partner_worker_qualification_tenant_qualification_type",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_partner_worker_qualification_tenant_worker",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_worker_qualification_tenant_id_id"),
        sa.CheckConstraint(
            "valid_until IS NULL OR issued_at IS NULL OR valid_until >= issued_at",
            name="ck_partner_worker_qualification_valid_window",
        ),
        schema="partner",
    )
    op.create_index(
        "ix_partner_worker_qualification_worker_status",
        "subcontractor_worker_qualification",
        ["tenant_id", "worker_id", "status", "valid_until"],
        unique=False,
        schema="partner",
    )
    op.create_table(
        "subcontractor_worker_credential",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("worker_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("credential_no", sa.String(length=120), nullable=False),
        sa.Column("credential_type", sa.String(length=40), nullable=False),
        sa.Column("encoded_value", sa.String(length=255), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_partner_worker_credential_tenant_worker",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "credential_no", name="uq_partner_worker_credential_tenant_credential_no"),
        sa.UniqueConstraint("tenant_id", "encoded_value", name="uq_partner_worker_credential_tenant_encoded_value"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_partner_worker_credential_tenant_id_id"),
        sa.CheckConstraint(
            "credential_type IN ('company_id', 'work_badge')",
            name="ck_partner_worker_credential_type_valid",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'issued', 'revoked', 'expired')",
            name="ck_partner_worker_credential_status_valid",
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="ck_partner_worker_credential_window_valid",
        ),
        schema="partner",
    )


def downgrade() -> None:
    op.drop_table("subcontractor_worker_credential", schema="partner")
    op.drop_index("ix_partner_worker_qualification_worker_status", table_name="subcontractor_worker_qualification", schema="partner")
    op.drop_table("subcontractor_worker_qualification", schema="partner")
    op.drop_table("subcontractor_worker", schema="partner")
