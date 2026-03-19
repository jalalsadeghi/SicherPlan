"""employee master foundation

Revision ID: 0019_employee_master_foundation
Revises: 0018_recruiting_applicant_workflow
Create Date: 2026-03-19 22:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0019_employee_master_foundation"
down_revision = "0018_recruiting_applicant_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employee",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("personnel_no", sa.String(length=50), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("preferred_name", sa.String(length=120), nullable=True),
        sa.Column("work_email", sa.String(length=255), nullable=True),
        sa.Column("work_phone", sa.String(length=64), nullable=True),
        sa.Column("mobile_phone", sa.String(length=64), nullable=True),
        sa.Column("default_branch_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("default_mandate_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("hire_date", sa.Date(), nullable=True),
        sa.Column("termination_date", sa.Date(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=True),
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
            "termination_date IS NULL OR hire_date IS NULL OR termination_date >= hire_date",
            name="employee_hire_termination_valid",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "default_branch_id"], ["core.branch.tenant_id", "core.branch.id"], name="fk_hr_employee_tenant_branch", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "default_mandate_id"], ["core.mandate.tenant_id", "core.mandate.id"], name="fk_hr_employee_tenant_mandate", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["iam.user_account.id"], name=op.f("fk_employee_user_id_user_account"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee")),
        sa.UniqueConstraint("tenant_id", "personnel_no", name="uq_hr_employee_tenant_personnel_no"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_tenant_id_id"),
        schema="hr",
    )
    op.create_index(
        "uq_hr_employee_tenant_user_id",
        "employee",
        ["tenant_id", "user_id"],
        unique=True,
        schema="hr",
        postgresql_where=sa.text("user_id IS NOT NULL AND archived_at IS NULL"),
    )

    op.create_table(
        "employee_private_profile",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("private_email", sa.String(length=255), nullable=True),
        sa.Column("private_phone", sa.String(length=64), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("place_of_birth", sa.String(length=255), nullable=True),
        sa.Column("nationality_country_code", sa.String(length=2), nullable=True),
        sa.Column("marital_status", sa.String(length=80), nullable=True),
        sa.Column("tax_id", sa.String(length=80), nullable=True),
        sa.Column("social_security_no", sa.String(length=80), nullable=True),
        sa.Column("bank_account_holder", sa.String(length=255), nullable=True),
        sa.Column("bank_iban", sa.String(length=64), nullable=True),
        sa.Column("bank_bic", sa.String(length=64), nullable=True),
        sa.Column("emergency_contact_name", sa.String(length=255), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_private_profile_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_hr_employee_private_profile_tenant_employee", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_private_profile")),
        sa.UniqueConstraint("tenant_id", "employee_id", name="uq_hr_employee_private_profile_employee"),
        schema="hr",
    )

    op.create_table(
        "employee_address_history",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("address_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("address_type", sa.String(length=40), nullable=False, server_default="home"),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("address_type IN ('home', 'mailing')", name="employee_address_type_valid"),
        sa.CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="employee_address_window_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_address_history_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_hr_employee_address_history_tenant_employee", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["address_id"], ["common.address.id"], name=op.f("fk_employee_address_history_address_id_address"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_address_history")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_address_history_tenant_id_id"),
        schema="hr",
    )
    op.create_index(
        "ix_hr_employee_address_history_employee_window",
        "employee_address_history",
        ["tenant_id", "employee_id", "address_type", "valid_from"],
        unique=False,
        schema="hr",
    )

    op.create_table(
        "employee_group",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_group_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_group")),
        sa.UniqueConstraint("tenant_id", "code", name="uq_hr_employee_group_tenant_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_group_tenant_id_id"),
        schema="hr",
    )

    op.create_table(
        "employee_group_member",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("valid_until IS NULL OR valid_until >= valid_from", name="employee_group_member_window_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_group_member_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_hr_employee_group_member_tenant_employee", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "group_id"], ["hr.employee_group.tenant_id", "hr.employee_group.id"], name="fk_hr_employee_group_member_tenant_group", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_group_member")),
        sa.UniqueConstraint("tenant_id", "employee_id", "group_id", "valid_from", name="uq_hr_employee_group_member_assignment"),
        schema="hr",
    )


def downgrade() -> None:
    op.drop_table("employee_group_member", schema="hr")
    op.drop_table("employee_group", schema="hr")
    op.drop_index("ix_hr_employee_address_history_employee_window", table_name="employee_address_history", schema="hr")
    op.drop_table("employee_address_history", schema="hr")
    op.drop_table("employee_private_profile", schema="hr")
    op.drop_index("uq_hr_employee_tenant_user_id", table_name="employee", schema="hr")
    op.drop_table("employee", schema="hr")
