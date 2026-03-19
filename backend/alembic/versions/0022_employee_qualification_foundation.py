"""employee qualification foundation

Revision ID: 0022_employee_qualification_foundation
Revises: 0021_employee_file_notes
Create Date: 2026-03-19 23:40:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0022_employee_qualification_foundation"
down_revision = "0021_employee_file_notes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "function_type",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("planning_relevant", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_function_type_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_function_type")),
        sa.UniqueConstraint("tenant_id", "code", name="uq_hr_function_type_tenant_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_function_type_tenant_id_id"),
        schema="hr",
    )
    op.create_table(
        "qualification_type",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("planning_relevant", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("compliance_relevant", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("expiry_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("default_validity_days", sa.Integer(), nullable=True),
        sa.Column("proof_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint(
            "default_validity_days IS NULL OR default_validity_days > 0",
            name="qualification_type_default_validity_positive",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["core.tenant.id"],
            name=op.f("fk_qualification_type_tenant_id_tenant"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qualification_type")),
        sa.UniqueConstraint("tenant_id", "code", name="uq_hr_qualification_type_tenant_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_qualification_type_tenant_id_id"),
        schema="hr",
    )
    op.create_table(
        "employee_qualification",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("record_kind", sa.String(length=40), nullable=False, server_default="qualification"),
        sa.Column("function_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("qualification_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("certificate_no", sa.String(length=120), nullable=True),
        sa.Column("issued_at", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("issuing_authority", sa.String(length=255), nullable=True),
        sa.Column("granted_internally", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint(
            "record_kind IN ('function', 'qualification')",
            name="employee_qualification_record_kind_valid",
        ),
        sa.CheckConstraint(
            "(record_kind = 'function' AND function_type_id IS NOT NULL AND qualification_type_id IS NULL) OR "
            "(record_kind = 'qualification' AND function_type_id IS NULL AND qualification_type_id IS NOT NULL)",
            name="employee_qualification_target_matches_kind",
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR issued_at IS NULL OR valid_until >= issued_at",
            name="employee_qualification_valid_window",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_qualification_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_qualification_tenant_employee",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "function_type_id"],
            ["hr.function_type.tenant_id", "hr.function_type.id"],
            name="fk_hr_employee_qualification_tenant_function_type",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_hr_employee_qualification_tenant_qualification_type",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_qualification")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_qualification_tenant_id_id"),
        schema="hr",
    )
    op.create_index(
        "ix_hr_employee_qualification_employee_kind_status",
        "employee_qualification",
        ["tenant_id", "employee_id", "record_kind", "status"],
        unique=False,
        schema="hr",
    )


def downgrade() -> None:
    op.drop_index("ix_hr_employee_qualification_employee_kind_status", table_name="employee_qualification", schema="hr")
    op.drop_table("employee_qualification", schema="hr")
    op.drop_table("qualification_type", schema="hr")
    op.drop_table("function_type", schema="hr")
