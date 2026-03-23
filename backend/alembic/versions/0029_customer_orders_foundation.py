"""customer orders foundation

Revision ID: 0029_customer_orders_foundation
Revises: 0028_planning_ops_master_foundation
Create Date: 2026-03-20 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0029_customer_orders_foundation"
down_revision = "0028_planning_ops_master_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_order",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("requirement_type_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("patrol_route_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("order_no", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("service_category_code", sa.String(length=80), nullable=False),
        sa.Column("security_concept_text", sa.Text(), nullable=True),
        sa.Column("service_from", sa.Date(), nullable=False),
        sa.Column("service_to", sa.Date(), nullable=False),
        sa.Column("release_state", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("service_to >= service_from", name="customer_order_service_window_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_customer_order_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "customer_id"], ["crm.customer.tenant_id", "crm.customer.id"], name="fk_ops_customer_order_tenant_customer", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "requirement_type_id"], ["ops.requirement_type.tenant_id", "ops.requirement_type.id"], name="fk_ops_customer_order_tenant_requirement_type", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "patrol_route_id"], ["ops.patrol_route.tenant_id", "ops.patrol_route.id"], name="fk_ops_customer_order_tenant_patrol_route", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_customer_order"),
        sa.UniqueConstraint("tenant_id", "order_no", name="uq_ops_customer_order_tenant_order_no"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_customer_order_tenant_id_id"),
        schema="ops",
    )
    op.create_index("ix_ops_customer_order_customer_window", "customer_order", ["tenant_id", "customer_id", "service_from", "service_to"], unique=False, schema="ops")
    op.create_index("ix_ops_customer_order_release_state", "customer_order", ["tenant_id", "release_state", "status"], unique=False, schema="ops")

    op.create_table(
        "order_equipment",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("equipment_item_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("required_qty", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("required_qty >= 1", name="order_equipment_required_qty_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_order_equipment_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["ops.customer_order.tenant_id", "ops.customer_order.id"], name="fk_ops_order_equipment_tenant_order", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "equipment_item_id"], ["ops.equipment_item.tenant_id", "ops.equipment_item.id"], name="fk_ops_order_equipment_tenant_item", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_order_equipment"),
        sa.UniqueConstraint("tenant_id", "order_id", "equipment_item_id", name="uq_ops_order_equipment_order_item"),
        schema="ops",
    )

    op.create_table(
        "order_requirement_line",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("requirement_type_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("function_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("qualification_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("min_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_qty", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("min_qty >= 0", name="order_requirement_line_min_qty_nonnegative"),
        sa.CheckConstraint("target_qty >= min_qty", name="order_requirement_line_target_ge_min"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_order_requirement_line_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["ops.customer_order.tenant_id", "ops.customer_order.id"], name="fk_ops_order_requirement_line_tenant_order", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "requirement_type_id"], ["ops.requirement_type.tenant_id", "ops.requirement_type.id"], name="fk_ops_order_requirement_line_tenant_requirement_type", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "function_type_id"], ["hr.function_type.tenant_id", "hr.function_type.id"], name="fk_ops_order_requirement_line_tenant_function_type", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "qualification_type_id"], ["hr.qualification_type.tenant_id", "hr.qualification_type.id"], name="fk_ops_order_requirement_line_tenant_qualification_type", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_order_requirement_line"),
        schema="ops",
    )
    op.create_index("ix_ops_order_requirement_line_order", "order_requirement_line", ["tenant_id", "order_id"], unique=False, schema="ops")


def downgrade() -> None:
    op.drop_index("ix_ops_order_requirement_line_order", table_name="order_requirement_line", schema="ops")
    op.drop_table("order_requirement_line", schema="ops")
    op.drop_table("order_equipment", schema="ops")
    op.drop_index("ix_ops_customer_order_release_state", table_name="customer_order", schema="ops")
    op.drop_index("ix_ops_customer_order_customer_window", table_name="customer_order", schema="ops")
    op.drop_table("customer_order", schema="ops")
