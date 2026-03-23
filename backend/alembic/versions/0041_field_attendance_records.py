"""field attendance records

Revision ID: 0041_field_attendance_records
Revises: 0040_field_time_events
Create Date: 2026-03-20 00:00:02.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0041_field_attendance_records"
down_revision = "0040_field_time_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attendance_record",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("actor_type_code", sa.String(length=40), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("subcontractor_worker_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("break_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("worked_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_time_event_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("last_time_event_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("source_event_ids_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("discrepancy_state_code", sa.String(length=40), nullable=False, server_default="clean"),
        sa.Column("discrepancy_codes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("discrepancy_details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("derivation_status_code", sa.String(length=40), nullable=False, server_default="derived"),
        sa.Column("derived_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_by_attendance_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "actor_type_code IN ('employee','subcontractor_worker')",
            name=op.f("ck_attendance_record_attendance_record_actor_type_valid"),
        ),
        sa.CheckConstraint(
            "(employee_id IS NOT NULL AND subcontractor_worker_id IS NULL AND actor_type_code = 'employee') OR "
            "(employee_id IS NULL AND subcontractor_worker_id IS NOT NULL AND actor_type_code = 'subcontractor_worker')",
            name=op.f("ck_attendance_record_attendance_record_actor_reference_valid"),
        ),
        sa.CheckConstraint(
            "discrepancy_state_code IN ('clean','warning','needs_review')",
            name=op.f("ck_attendance_record_attendance_record_discrepancy_state_valid"),
        ),
        sa.CheckConstraint(
            "derivation_status_code IN ('derived','needs_review','superseded')",
            name=op.f("ck_attendance_record_attendance_record_derivation_status_valid"),
        ),
        sa.CheckConstraint("source_event_count >= 0", name=op.f("ck_attendance_record_attendance_record_source_event_count_nonnegative")),
        sa.CheckConstraint("break_minutes >= 0", name=op.f("ck_attendance_record_attendance_record_break_minutes_nonnegative")),
        sa.CheckConstraint("worked_minutes >= 0", name=op.f("ck_attendance_record_attendance_record_worked_minutes_nonnegative")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_field_attendance_record_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_field_attendance_record_tenant_employee",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "subcontractor_worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_field_attendance_record_tenant_worker",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_field_attendance_record_tenant_shift",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["ops.assignment.tenant_id", "ops.assignment.id"],
            name="fk_field_attendance_record_tenant_assignment",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "first_time_event_id"],
            ["field.time_event.tenant_id", "field.time_event.id"],
            name="fk_field_attendance_record_tenant_first_event",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "last_time_event_id"],
            ["field.time_event.tenant_id", "field.time_event.id"],
            name="fk_field_attendance_record_tenant_last_event",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "superseded_by_attendance_id"],
            ["field.attendance_record.tenant_id", "field.attendance_record.id"],
            name="fk_field_attendance_record_tenant_superseded_by",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attendance_record")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_field_attendance_record_tenant_id_id"),
        schema="field",
    )
    op.create_index(
        "ix_field_attendance_record_shift_derived",
        "attendance_record",
        ["tenant_id", "shift_id", "derived_at"],
        unique=False,
        schema="field",
    )
    op.create_index(
        "ix_field_attendance_record_assignment_current",
        "attendance_record",
        ["tenant_id", "assignment_id", "is_current"],
        unique=False,
        schema="field",
    )
    op.create_index(
        "uq_field_attendance_record_employee_current",
        "attendance_record",
        ["tenant_id", "shift_id", "employee_id"],
        unique=True,
        schema="field",
        postgresql_where=sa.text("employee_id IS NOT NULL AND is_current = true AND archived_at IS NULL"),
    )
    op.create_index(
        "uq_field_attendance_record_worker_current",
        "attendance_record",
        ["tenant_id", "shift_id", "subcontractor_worker_id"],
        unique=True,
        schema="field",
        postgresql_where=sa.text("subcontractor_worker_id IS NOT NULL AND is_current = true AND archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_field_attendance_record_worker_current", table_name="attendance_record", schema="field")
    op.drop_index("uq_field_attendance_record_employee_current", table_name="attendance_record", schema="field")
    op.drop_index("ix_field_attendance_record_assignment_current", table_name="attendance_record", schema="field")
    op.drop_index("ix_field_attendance_record_shift_derived", table_name="attendance_record", schema="field")
    op.drop_table("attendance_record", schema="field")
