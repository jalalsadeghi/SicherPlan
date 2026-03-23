"""field time capture foundation

Revision ID: 0039_field_time_capture_foundation
Revises: 0038_field_patrol_rounds
Create Date: 2026-03-20 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0039_field_time_capture_foundation"
down_revision = "0038_field_patrol_rounds"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "time_capture_device",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("device_code", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("device_type_code", sa.String(length=40), nullable=False, server_default="shared_terminal"),
        sa.Column("site_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("access_key_hash", sa.String(length=128), nullable=True),
        sa.Column("fixed_ip_cidr", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "device_type_code IN ('shared_terminal','browser_station','scanner_station','mobile_shared')",
            name=op.f("ck_time_capture_device_time_capture_device_type_valid"),
        ),
        sa.CheckConstraint(
            "status IN ('active','inactive')",
            name=op.f("ck_time_capture_device_time_capture_device_status_valid"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_field_time_capture_device_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "site_id"],
            ["ops.site.tenant_id", "ops.site.id"],
            name="fk_field_time_capture_device_tenant_site",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_time_capture_device")),
        sa.UniqueConstraint("tenant_id", "device_code", name="uq_field_time_capture_device_tenant_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_field_time_capture_device_tenant_id_id"),
        schema="field",
    )
    op.create_index(
        "ix_field_time_capture_device_site_status",
        "time_capture_device",
        ["tenant_id", "site_id", "status"],
        unique=False,
        schema="field",
    )

    op.create_table(
        "time_capture_policy",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("policy_code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("context_type_code", sa.String(length=40), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("patrol_route_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("allowed_device_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("allowed_device_type_code", sa.String(length=40), nullable=True),
        sa.Column("allow_browser_capture", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("allow_mobile_capture", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("allow_terminal_capture", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("allowed_ip_cidr", sa.String(length=80), nullable=True),
        sa.Column("geofence_latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("geofence_longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("geofence_radius_meters", sa.Integer(), nullable=True),
        sa.Column("enforce_mode_code", sa.String(length=20), nullable=False, server_default="reject"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "context_type_code IN ('site','shift','planning_record','patrol_route')",
            name=op.f("ck_time_capture_policy_time_capture_policy_context_type_valid"),
        ),
        sa.CheckConstraint(
            "(CASE WHEN site_id IS NULL THEN 0 ELSE 1 END + "
            "CASE WHEN shift_id IS NULL THEN 0 ELSE 1 END + "
            "CASE WHEN planning_record_id IS NULL THEN 0 ELSE 1 END + "
            "CASE WHEN patrol_route_id IS NULL THEN 0 ELSE 1 END) = 1",
            name=op.f("ck_time_capture_policy_time_capture_policy_context_exactly_one"),
        ),
        sa.CheckConstraint(
            "enforce_mode_code IN ('flag','reject')",
            name=op.f("ck_time_capture_policy_time_capture_policy_enforce_mode_valid"),
        ),
        sa.CheckConstraint(
            "status IN ('active','inactive')",
            name=op.f("ck_time_capture_policy_time_capture_policy_status_valid"),
        ),
        sa.CheckConstraint(
            "(geofence_latitude IS NULL AND geofence_longitude IS NULL AND geofence_radius_meters IS NULL) OR "
            "(geofence_latitude BETWEEN -90 AND 90 AND geofence_longitude BETWEEN -180 AND 180 AND geofence_radius_meters > 0)",
            name=op.f("ck_time_capture_policy_time_capture_policy_geofence_valid"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_field_time_capture_policy_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "site_id"],
            ["ops.site.tenant_id", "ops.site.id"],
            name="fk_field_time_capture_policy_tenant_site",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_field_time_capture_policy_tenant_shift",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_field_time_capture_policy_tenant_planning_record",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "patrol_route_id"],
            ["ops.patrol_route.tenant_id", "ops.patrol_route.id"],
            name="fk_field_time_capture_policy_tenant_route",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "allowed_device_id"],
            ["field.time_capture_device.tenant_id", "field.time_capture_device.id"],
            name="fk_field_time_capture_policy_tenant_device",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_time_capture_policy")),
        sa.UniqueConstraint("tenant_id", "policy_code", name="uq_field_time_capture_policy_tenant_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_field_time_capture_policy_tenant_id_id"),
        schema="field",
    )
    op.create_index(
        "uq_field_time_capture_policy_active_context",
        "time_capture_policy",
        ["tenant_id", "context_type_code", "site_id", "shift_id", "planning_record_id", "patrol_route_id"],
        unique=True,
        schema="field",
        postgresql_where=sa.text("archived_at IS NULL AND status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_field_time_capture_policy_active_context", table_name="time_capture_policy", schema="field")
    op.drop_table("time_capture_policy", schema="field")
    op.drop_index("ix_field_time_capture_device_site_status", table_name="time_capture_device", schema="field")
    op.drop_table("time_capture_device", schema="field")
