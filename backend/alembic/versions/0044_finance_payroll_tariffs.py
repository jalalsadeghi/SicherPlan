"""finance payroll tariffs

Revision ID: 0044_finance_payroll_tariffs
Revises: 0043_finance_actual_approvals_and_adjustments
Create Date: 2026-03-20 00:00:05.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0044_finance_payroll_tariffs"
down_revision = "0043_finance_actual_approvals_and_adjustments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payroll_tariff_table",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("region_code", sa.String(length=32), nullable=False),
        sa.Column("tariff_status_code", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("effective_until IS NULL OR effective_until >= effective_from", name="payroll_tariff_table_window_valid"),
        sa.CheckConstraint("tariff_status_code IN ('draft','active','archived')", name="payroll_tariff_table_status_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_payroll_tariff_table_tenant", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_finance_payroll_tariff_table_tenant_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_tariff_table_tenant_id_id"),
        schema="finance",
    )
    op.create_index(
        "ix_finance_payroll_tariff_table_region_window",
        "payroll_tariff_table",
        ["tenant_id", "region_code", "effective_from"],
        unique=False,
        schema="finance",
    )
    op.create_table(
        "payroll_tariff_rate",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tariff_table_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("function_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("qualification_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("employment_type_code", sa.String(length=40), nullable=True),
        sa.Column("pay_unit_code", sa.String(length=20), nullable=False, server_default="hour"),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("base_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payroll_code", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("base_amount >= 0", name="payroll_tariff_rate_amount_nonnegative"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_payroll_tariff_rate_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "tariff_table_id"], ["finance.payroll_tariff_table.tenant_id", "finance.payroll_tariff_table.id"], name="fk_finance_payroll_tariff_rate_tenant_table", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "function_type_id"], ["hr.function_type.tenant_id", "hr.function_type.id"], name="fk_finance_payroll_tariff_rate_tenant_function_type", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "qualification_type_id"], ["hr.qualification_type.tenant_id", "hr.qualification_type.id"], name="fk_finance_payroll_tariff_rate_tenant_qualification_type", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_tariff_rate_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "tariff_table_id", "function_type_id", "qualification_type_id", "employment_type_code", "pay_unit_code", name="uq_finance_payroll_tariff_rate_dimensions"),
        schema="finance",
    )
    op.create_table(
        "payroll_surcharge_rule",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tariff_table_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("surcharge_type_code", sa.String(length=40), nullable=False),
        sa.Column("custom_code", sa.String(length=80), nullable=True),
        sa.Column("weekday_mask", sa.Integer(), nullable=False, server_default="127"),
        sa.Column("start_minute_local", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("end_minute_local", sa.Integer(), nullable=False, server_default="1440"),
        sa.Column("holiday_region_code", sa.String(length=32), nullable=True),
        sa.Column("function_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("qualification_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("employment_type_code", sa.String(length=40), nullable=True),
        sa.Column("percent_value", sa.Numeric(8, 2), nullable=True),
        sa.Column("fixed_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency_code", sa.String(length=3), nullable=True),
        sa.Column("payroll_code", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("weekday_mask >= 0 AND weekday_mask <= 127", name="payroll_surcharge_rule_weekday_mask_valid"),
        sa.CheckConstraint("start_minute_local >= 0 AND start_minute_local <= 1439", name="payroll_surcharge_rule_start_minute_valid"),
        sa.CheckConstraint("end_minute_local >= 0 AND end_minute_local <= 1440", name="payroll_surcharge_rule_end_minute_valid"),
        sa.CheckConstraint("percent_value IS NOT NULL OR fixed_amount IS NOT NULL", name="payroll_surcharge_rule_amount_required"),
        sa.CheckConstraint("percent_value IS NULL OR percent_value >= 0", name="payroll_surcharge_rule_percent_nonnegative"),
        sa.CheckConstraint("fixed_amount IS NULL OR fixed_amount >= 0", name="payroll_surcharge_rule_fixed_amount_nonnegative"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_payroll_surcharge_rule_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "tariff_table_id"], ["finance.payroll_tariff_table.tenant_id", "finance.payroll_tariff_table.id"], name="fk_finance_payroll_surcharge_rule_tenant_table", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "function_type_id"], ["hr.function_type.tenant_id", "hr.function_type.id"], name="fk_finance_payroll_surcharge_rule_tenant_function_type", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "qualification_type_id"], ["hr.qualification_type.tenant_id", "hr.qualification_type.id"], name="fk_finance_payroll_surcharge_rule_tenant_qualification_type", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_surcharge_rule_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "tariff_table_id", "surcharge_type_code", "custom_code", "weekday_mask", "start_minute_local", "end_minute_local", "function_type_id", "qualification_type_id", "employment_type_code", "holiday_region_code", name="uq_finance_payroll_surcharge_rule_dimensions"),
        schema="finance",
    )


def downgrade() -> None:
    op.drop_table("payroll_surcharge_rule", schema="finance")
    op.drop_table("payroll_tariff_rate", schema="finance")
    op.drop_index("ix_finance_payroll_tariff_table_region_window", table_name="payroll_tariff_table", schema="finance")
    op.drop_table("payroll_tariff_table", schema="finance")
