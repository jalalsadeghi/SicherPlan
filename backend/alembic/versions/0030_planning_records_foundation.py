"""planning records foundation

Revision ID: 0030_planning_records_foundation
Revises: 0029_customer_orders_foundation
Create Date: 2026-03-20 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0030_planning_records_foundation"
down_revision = "0029_customer_orders_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ops.trade_fair_zone (
            tenant_id UUID NOT NULL,
            trade_fair_id UUID NOT NULL,
            zone_type_code VARCHAR(80) NOT NULL,
            zone_code VARCHAR(80) NOT NULL,
            label VARCHAR(255) NOT NULL,
            notes TEXT,
            id UUID NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by_user_id UUID,
            updated_by_user_id UUID,
            archived_at TIMESTAMP WITH TIME ZONE,
            version_no INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT pk_trade_fair_zone PRIMARY KEY (id),
            CONSTRAINT fk_trade_fair_zone_tenant_id_tenant
                FOREIGN KEY (tenant_id) REFERENCES core.tenant (id) ON DELETE RESTRICT,
            CONSTRAINT fk_ops_trade_fair_zone_tenant_fair
                FOREIGN KEY (tenant_id, trade_fair_id) REFERENCES ops.trade_fair (tenant_id, id) ON DELETE RESTRICT,
            CONSTRAINT uq_ops_trade_fair_zone_tuple
                UNIQUE (tenant_id, trade_fair_id, zone_type_code, zone_code),
            CONSTRAINT uq_ops_trade_fair_zone_tenant_id_id UNIQUE (tenant_id, id)
        )
        """
    )

    op.create_table(
        "planning_record",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("parent_planning_record_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("dispatcher_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("planning_mode_code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("planning_from", sa.Date(), nullable=False),
        sa.Column("planning_to", sa.Date(), nullable=False),
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
        sa.CheckConstraint("planning_to >= planning_from", name="planning_record_window_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_planning_record_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["ops.customer_order.tenant_id", "ops.customer_order.id"], name="fk_ops_planning_record_tenant_order", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "parent_planning_record_id"], ["ops.planning_record.tenant_id", "ops.planning_record.id"], name="fk_ops_planning_record_tenant_parent", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dispatcher_user_id"], ["iam.user_account.id"], name="fk_ops_planning_record_dispatcher_user", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_planning_record"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_planning_record_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "order_id", "name", name="uq_ops_planning_record_order_name"),
        schema="ops",
    )
    op.create_index("ix_ops_planning_record_order_window", "planning_record", ["tenant_id", "order_id", "planning_from", "planning_to"], unique=False, schema="ops")
    op.create_index("ix_ops_planning_record_dispatcher_release", "planning_record", ["tenant_id", "dispatcher_user_id", "release_state"], unique=False, schema="ops")

    op.create_table(
        "event_plan_detail",
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("event_venue_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("setup_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_event_plan_detail_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "planning_record_id"], ["ops.planning_record.tenant_id", "ops.planning_record.id"], name="fk_ops_event_plan_detail_tenant_record", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "event_venue_id"], ["ops.event_venue.tenant_id", "ops.event_venue.id"], name="fk_ops_event_plan_detail_tenant_venue", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("planning_record_id", name="pk_event_plan_detail"),
        schema="ops",
    )

    op.create_table(
        "site_plan_detail",
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("watchbook_scope_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_site_plan_detail_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "planning_record_id"], ["ops.planning_record.tenant_id", "ops.planning_record.id"], name="fk_ops_site_plan_detail_tenant_record", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "site_id"], ["ops.site.tenant_id", "ops.site.id"], name="fk_ops_site_plan_detail_tenant_site", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("planning_record_id", name="pk_site_plan_detail"),
        schema="ops",
    )

    op.create_table(
        "trade_fair_plan_detail",
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("trade_fair_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("trade_fair_zone_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("stand_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_trade_fair_plan_detail_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "planning_record_id"], ["ops.planning_record.tenant_id", "ops.planning_record.id"], name="fk_ops_trade_fair_plan_detail_tenant_record", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "trade_fair_id"], ["ops.trade_fair.tenant_id", "ops.trade_fair.id"], name="fk_ops_trade_fair_plan_detail_tenant_fair", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "trade_fair_zone_id"], ["ops.trade_fair_zone.tenant_id", "ops.trade_fair_zone.id"], name="fk_ops_trade_fair_plan_detail_tenant_zone", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("planning_record_id", name="pk_trade_fair_plan_detail"),
        schema="ops",
    )

    op.create_table(
        "patrol_plan_detail",
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("patrol_route_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("execution_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_patrol_plan_detail_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "planning_record_id"], ["ops.planning_record.tenant_id", "ops.planning_record.id"], name="fk_ops_patrol_plan_detail_tenant_record", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "patrol_route_id"], ["ops.patrol_route.tenant_id", "ops.patrol_route.id"], name="fk_ops_patrol_plan_detail_tenant_route", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("planning_record_id", name="pk_patrol_plan_detail"),
        schema="ops",
    )


def downgrade() -> None:
    op.drop_table("patrol_plan_detail", schema="ops")
    op.drop_table("trade_fair_plan_detail", schema="ops")
    op.drop_table("site_plan_detail", schema="ops")
    op.drop_table("event_plan_detail", schema="ops")
    op.drop_index("ix_ops_planning_record_dispatcher_release", table_name="planning_record", schema="ops")
    op.drop_index("ix_ops_planning_record_order_window", table_name="planning_record", schema="ops")
    op.drop_table("planning_record", schema="ops")
