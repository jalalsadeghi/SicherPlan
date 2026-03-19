"""Extend customer billing profile with advanced invoice configuration."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0014_customer_invoice_configuration"
down_revision = "0013_customer_pricing_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customer_billing_profile",
        sa.Column("e_invoice_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        schema="crm",
    )
    op.add_column(
        "customer_billing_profile",
        sa.Column("leitweg_id", sa.String(length=120), nullable=True),
        schema="crm",
    )
    op.add_column(
        "customer_billing_profile",
        sa.Column("invoice_layout_code", sa.String(length=80), nullable=True),
        schema="crm",
    )
    op.add_column(
        "customer_billing_profile",
        sa.Column("shipping_method_code", sa.String(length=80), nullable=True),
        schema="crm",
    )
    op.add_column(
        "customer_billing_profile",
        sa.Column("dunning_policy_code", sa.String(length=80), nullable=True),
        schema="crm",
    )


def downgrade() -> None:
    op.drop_column("customer_billing_profile", "dunning_policy_code", schema="crm")
    op.drop_column("customer_billing_profile", "shipping_method_code", schema="crm")
    op.drop_column("customer_billing_profile", "invoice_layout_code", schema="crm")
    op.drop_column("customer_billing_profile", "leitweg_id", schema="crm")
    op.drop_column("customer_billing_profile", "e_invoice_enabled", schema="crm")
