"""employee compensation and credentials

Revision ID: 0024_employee_compensation_and_credentials
Revises: 0023_employee_availability_absence_foundation
Create Date: 2026-03-20 00:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0024_employee_compensation_and_credentials"
down_revision = "0023_employee_availability_absence_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employee_time_account",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("account_type", sa.String(length=40), nullable=False, server_default="work_time"),
        sa.Column("unit_code", sa.String(length=20), nullable=False, server_default="minutes"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("account_type IN ('work_time', 'overtime', 'flextime')", name="employee_time_account_type_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_time_account_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_hr_employee_time_account_tenant_employee", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_time_account")),
        sa.UniqueConstraint("tenant_id", "employee_id", "account_type", name="uq_hr_employee_time_account_employee_type"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_time_account_tenant_id_id"),
        schema="hr",
    )
    op.create_table(
        "employee_time_account_txn",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("time_account_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("txn_type", sa.String(length=20), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("amount_minutes", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(length=80), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("txn_type IN ('opening', 'credit', 'debit', 'correction')", name="employee_time_account_txn_type_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_time_account_txn_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "time_account_id"], ["hr.employee_time_account.tenant_id", "hr.employee_time_account.id"], name="fk_hr_employee_time_account_txn_tenant_account", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_time_account_txn")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_time_account_txn_tenant_id_id"),
        schema="hr",
    )
    op.create_table(
        "employee_allowance",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("basis_code", sa.String(length=80), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("function_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("qualification_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("effective_until IS NULL OR effective_until >= effective_from", name="employee_allowance_window_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_allowance_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_hr_employee_allowance_tenant_employee", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "function_type_id"], ["hr.function_type.tenant_id", "hr.function_type.id"], name="fk_hr_employee_allowance_tenant_function_type", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "qualification_type_id"], ["hr.qualification_type.tenant_id", "hr.qualification_type.id"], name="fk_hr_employee_allowance_tenant_qualification_type", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_allowance")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_allowance_tenant_id_id"),
        schema="hr",
    )
    op.create_table(
        "employee_advance",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("advance_no", sa.String(length=80), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("outstanding_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="requested"),
        sa.Column("requested_on", sa.Date(), nullable=False),
        sa.Column("disbursed_on", sa.Date(), nullable=True),
        sa.Column("settled_on", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("status IN ('requested', 'approved', 'disbursed', 'settled', 'cancelled')", name="employee_advance_status_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_advance_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_hr_employee_advance_tenant_employee", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_advance")),
        sa.UniqueConstraint("tenant_id", "advance_no", name="uq_hr_employee_advance_tenant_advance_no"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_advance_tenant_id_id"),
        schema="hr",
    )
    op.create_table(
        "employee_id_credential",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("credential_no", sa.String(length=120), nullable=False),
        sa.Column("credential_type", sa.String(length=40), nullable=False, server_default="company_id"),
        sa.Column("encoded_value", sa.String(length=255), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("credential_type IN ('company_id', 'work_badge')", name="employee_id_credential_type_valid"),
        sa.CheckConstraint("status IN ('draft', 'issued', 'revoked', 'expired')", name="employee_id_credential_status_valid"),
        sa.CheckConstraint("valid_until IS NULL OR valid_until >= valid_from", name="employee_id_credential_window_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_id_credential_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_hr_employee_id_credential_tenant_employee", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_id_credential")),
        sa.UniqueConstraint("tenant_id", "credential_no", name="uq_hr_employee_id_credential_tenant_credential_no"),
        sa.UniqueConstraint("tenant_id", "encoded_value", name="uq_hr_employee_id_credential_tenant_encoded_value"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_id_credential_tenant_id_id"),
        schema="hr",
    )


def downgrade() -> None:
    op.drop_table("employee_id_credential", schema="hr")
    op.drop_table("employee_advance", schema="hr")
    op.drop_table("employee_allowance", schema="hr")
    op.drop_table("employee_time_account_txn", schema="hr")
    op.drop_table("employee_time_account", schema="hr")
