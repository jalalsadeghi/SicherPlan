"""Add customer pricing backbone tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0013_customer_pricing_rules"
down_revision = "0012_customer_billing_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_rate_card",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("rate_kind", sa.String(length=40), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="crm_customer_rate_card_effective_window_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_crm_customer_rate_card_tenant_customer",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_crm_customer_rate_card_tenant_id_id"),
        schema="crm",
    )
    op.create_index(
        "ix_crm_customer_rate_card_customer_effective",
        "customer_rate_card",
        ["tenant_id", "customer_id", "effective_from"],
        unique=False,
        schema="crm",
    )

    op.create_table(
        "customer_rate_line",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("rate_card_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("line_kind", sa.String(length=40), nullable=False),
        sa.Column("function_type_id", sa.String(length=36), nullable=True),
        sa.Column("qualification_type_id", sa.String(length=36), nullable=True),
        sa.Column("planning_mode_code", sa.String(length=40), nullable=True),
        sa.Column("billing_unit", sa.String(length=40), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("minimum_quantity", sa.Numeric(12, 2), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("100"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("unit_price >= 0", name="crm_customer_rate_line_unit_price_non_negative"),
        sa.CheckConstraint(
            "minimum_quantity IS NULL OR minimum_quantity >= 0",
            name="crm_customer_rate_line_minimum_quantity_non_negative",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "rate_card_id"],
            ["crm.customer_rate_card.tenant_id", "crm.customer_rate_card.id"],
            name="fk_crm_customer_rate_line_tenant_rate_card",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_crm_customer_rate_line_tenant_id_id"),
        schema="crm",
    )
    op.create_index(
        "ix_crm_customer_rate_line_rate_card",
        "customer_rate_line",
        ["tenant_id", "rate_card_id"],
        unique=False,
        schema="crm",
    )

    op.create_table(
        "customer_surcharge_rule",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("rate_card_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("surcharge_type", sa.String(length=40), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("weekday_mask", sa.String(length=7), nullable=True),
        sa.Column("time_from_minute", sa.Integer(), nullable=True),
        sa.Column("time_to_minute", sa.Integer(), nullable=True),
        sa.Column("region_code", sa.String(length=80), nullable=True),
        sa.Column("percent_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("fixed_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency_code", sa.String(length=3), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("100"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="crm_customer_surcharge_rule_effective_window_valid",
        ),
        sa.CheckConstraint(
            "weekday_mask IS NULL OR char_length(weekday_mask) = 7",
            name="crm_customer_surcharge_rule_weekday_mask_length",
        ),
        sa.CheckConstraint(
            "time_from_minute IS NULL OR (time_from_minute >= 0 AND time_from_minute <= 1439)",
            name="crm_customer_surcharge_rule_time_from_range",
        ),
        sa.CheckConstraint(
            "time_to_minute IS NULL OR (time_to_minute >= 1 AND time_to_minute <= 1440)",
            name="crm_customer_surcharge_rule_time_to_range",
        ),
        sa.CheckConstraint(
            "percent_value IS NULL OR percent_value >= 0",
            name="crm_customer_surcharge_rule_percent_non_negative",
        ),
        sa.CheckConstraint(
            "fixed_amount IS NULL OR fixed_amount >= 0",
            name="crm_customer_surcharge_rule_fixed_amount_non_negative",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "rate_card_id"],
            ["crm.customer_rate_card.tenant_id", "crm.customer_rate_card.id"],
            name="fk_crm_customer_surcharge_rule_tenant_rate_card",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_crm_customer_surcharge_rule_tenant_id_id"),
        schema="crm",
    )
    op.create_index(
        "ix_crm_customer_surcharge_rule_rate_card",
        "customer_surcharge_rule",
        ["tenant_id", "rate_card_id"],
        unique=False,
        schema="crm",
    )


def downgrade() -> None:
    op.drop_index("ix_crm_customer_surcharge_rule_rate_card", table_name="customer_surcharge_rule", schema="crm")
    op.drop_table("customer_surcharge_rule", schema="crm")
    op.drop_index("ix_crm_customer_rate_line_rate_card", table_name="customer_rate_line", schema="crm")
    op.drop_table("customer_rate_line", schema="crm")
    op.drop_index("ix_crm_customer_rate_card_customer_effective", table_name="customer_rate_card", schema="crm")
    op.drop_table("customer_rate_card", schema="crm")
