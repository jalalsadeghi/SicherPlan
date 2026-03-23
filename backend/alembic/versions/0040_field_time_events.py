"""field time events

Revision ID: 0040_field_time_events
Revises: 0039_field_time_capture_foundation
Create Date: 2026-03-20 00:00:01.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0040_field_time_events"
down_revision = "0039_field_time_capture_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "time_event",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("actor_type_code", sa.String(length=40), nullable=False, server_default="unresolved"),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("subcontractor_worker_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("site_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("patrol_route_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("policy_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("source_channel_code", sa.String(length=20), nullable=False),
        sa.Column("event_code", sa.String(length=20), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("source_ip", sa.String(length=80), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("scan_medium_code", sa.String(length=40), nullable=True),
        sa.Column("raw_token_hash", sa.String(length=128), nullable=True),
        sa.Column("raw_token_suffix", sa.String(length=12), nullable=True),
        sa.Column("client_event_id", sa.String(length=120), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("validation_status_code", sa.String(length=20), nullable=False, server_default="accepted"),
        sa.Column("validation_message_key", sa.String(length=255), nullable=True),
        sa.Column("validation_details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "actor_type_code IN ('employee','subcontractor_worker','unresolved')",
            name=op.f("ck_time_event_time_event_actor_type_valid"),
        ),
        sa.CheckConstraint(
            "(employee_id IS NOT NULL AND subcontractor_worker_id IS NULL AND actor_type_code = 'employee') OR "
            "(employee_id IS NULL AND subcontractor_worker_id IS NOT NULL AND actor_type_code = 'subcontractor_worker') OR "
            "(employee_id IS NULL AND subcontractor_worker_id IS NULL AND actor_type_code = 'unresolved')",
            name=op.f("ck_time_event_time_event_actor_reference_valid"),
        ),
        sa.CheckConstraint(
            "source_channel_code IN ('browser','mobile','terminal')",
            name=op.f("ck_time_event_time_event_source_channel_valid"),
        ),
        sa.CheckConstraint(
            "event_code IN ('clock_in','clock_out','break_start','break_end')",
            name=op.f("ck_time_event_time_event_event_code_valid"),
        ),
        sa.CheckConstraint(
            "validation_status_code IN ('accepted','flagged','rejected')",
            name=op.f("ck_time_event_time_event_validation_status_valid"),
        ),
        sa.CheckConstraint(
            "scan_medium_code IS NULL OR scan_medium_code IN ('manual','qr','barcode','rfid','nfc','app_badge')",
            name=op.f("ck_time_event_time_event_scan_medium_valid"),
        ),
        sa.CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)",
            name=op.f("ck_time_event_time_event_coordinates_valid"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_field_time_event_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_field_time_event_tenant_employee",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "subcontractor_worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_field_time_event_tenant_worker",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_field_time_event_tenant_shift",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["ops.assignment.tenant_id", "ops.assignment.id"],
            name="fk_field_time_event_tenant_assignment",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "site_id"],
            ["ops.site.tenant_id", "ops.site.id"],
            name="fk_field_time_event_tenant_site",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_field_time_event_tenant_planning_record",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "patrol_route_id"],
            ["ops.patrol_route.tenant_id", "ops.patrol_route.id"],
            name="fk_field_time_event_tenant_route",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "device_id"],
            ["field.time_capture_device.tenant_id", "field.time_capture_device.id"],
            name="fk_field_time_event_tenant_device",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "policy_id"],
            ["field.time_capture_policy.tenant_id", "field.time_capture_policy.id"],
            name="fk_field_time_event_tenant_policy",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_time_event")),
        sa.UniqueConstraint("tenant_id", "client_event_id", name="uq_field_time_event_tenant_client_event"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_field_time_event_tenant_id_id"),
        schema="field",
    )
    op.create_index("ix_field_time_event_tenant_occurred_at", "time_event", ["tenant_id", "occurred_at"], unique=False, schema="field")
    op.create_index(
        "ix_field_time_event_tenant_shift_occurred_at",
        "time_event",
        ["tenant_id", "shift_id", "occurred_at"],
        unique=False,
        schema="field",
    )
    op.create_index(
        "ix_field_time_event_tenant_validation_status",
        "time_event",
        ["tenant_id", "validation_status_code", "occurred_at"],
        unique=False,
        schema="field",
    )


def downgrade() -> None:
    op.drop_index("ix_field_time_event_tenant_validation_status", table_name="time_event", schema="field")
    op.drop_index("ix_field_time_event_tenant_shift_occurred_at", table_name="time_event", schema="field")
    op.drop_index("ix_field_time_event_tenant_occurred_at", table_name="time_event", schema="field")
    op.drop_table("time_event", schema="field")
