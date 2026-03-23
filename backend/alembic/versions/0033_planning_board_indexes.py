"""planning board indexes

Revision ID: 0033_planning_board_indexes
Revises: 0032_shift_series_exceptions
Create Date: 2026-03-20
"""

from __future__ import annotations

from alembic import op


revision = "0033_planning_board_indexes"
down_revision = "0032_shift_series_exceptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_ops_planning_record_tenant_order_window_mode",
        "planning_record",
        ["tenant_id", "order_id", "planning_from", "planning_to", "planning_mode_code"],
        unique=False,
        schema="ops",
    )
    op.create_index(
        "ix_ops_customer_order_tenant_customer_window_release",
        "customer_order",
        ["tenant_id", "customer_id", "service_from", "service_to", "release_state"],
        unique=False,
        schema="ops",
    )
    op.create_index(
        "ix_ops_shift_tenant_release_starts_at",
        "shift",
        ["tenant_id", "release_state", "starts_at"],
        unique=False,
        schema="ops",
    )
    op.create_index(
        "ix_ops_shift_plan_tenant_workforce_window",
        "shift_plan",
        ["tenant_id", "workforce_scope_code", "planning_from", "planning_to"],
        unique=False,
        schema="ops",
    )


def downgrade() -> None:
    op.drop_index("ix_ops_shift_plan_tenant_workforce_window", table_name="shift_plan", schema="ops")
    op.drop_index("ix_ops_shift_tenant_release_starts_at", table_name="shift", schema="ops")
    op.drop_index("ix_ops_customer_order_tenant_customer_window_release", table_name="customer_order", schema="ops")
    op.drop_index("ix_ops_planning_record_tenant_order_window_mode", table_name="planning_record", schema="ops")
