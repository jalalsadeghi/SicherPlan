"""staffing backbone

Revision ID: 0034_staffing_backbone
Revises: 0033_planning_board_indexes
Create Date: 2026-03-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0034_staffing_backbone"
down_revision = "0033_planning_board_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "demand_group",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("function_type_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("qualification_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("min_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_qty", sa.Integer(), nullable=False),
        sa.Column("mandatory_flag", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_demand_group")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_ops_demand_group_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_id"], ["ops.shift.tenant_id", "ops.shift.id"], name="fk_ops_demand_group_tenant_shift", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "function_type_id"], ["hr.function_type.tenant_id", "hr.function_type.id"], name="fk_ops_demand_group_tenant_function_type", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "qualification_type_id"], ["hr.qualification_type.tenant_id", "hr.qualification_type.id"], name="fk_ops_demand_group_tenant_qualification_type", ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_demand_group_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "shift_id", "sort_order", name="uq_ops_demand_group_shift_sort_order"),
        sa.CheckConstraint("min_qty >= 0", name="demand_group_min_qty_nonnegative"),
        sa.CheckConstraint("target_qty >= min_qty", name="demand_group_target_qty_ge_min"),
        schema="ops",
    )
    op.create_index("ix_ops_demand_group_tenant_shift", "demand_group", ["tenant_id", "shift_id", "sort_order"], unique=False, schema="ops")

    op.create_table(
        "team",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role_label", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_team")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_ops_team_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "planning_record_id"], ["ops.planning_record.tenant_id", "ops.planning_record.id"], name="fk_ops_team_tenant_record", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_id"], ["ops.shift.tenant_id", "ops.shift.id"], name="fk_ops_team_tenant_shift", ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_team_tenant_id_id"),
        sa.CheckConstraint("planning_record_id IS NOT NULL OR shift_id IS NOT NULL", name="team_requires_record_or_shift"),
        schema="ops",
    )
    op.create_index("ix_ops_team_tenant_record", "team", ["tenant_id", "planning_record_id"], unique=False, schema="ops")
    op.create_index("ix_ops_team_tenant_shift", "team", ["tenant_id", "shift_id"], unique=False, schema="ops")

    op.create_table(
        "team_member",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("subcontractor_worker_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("role_label", sa.String(length=120), nullable=True),
        sa.Column("is_team_lead", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_team_member")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_ops_team_member_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "team_id"], ["ops.team.tenant_id", "ops.team.id"], name="fk_ops_team_member_tenant_team", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_ops_team_member_tenant_employee", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "subcontractor_worker_id"], ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"], name="fk_ops_team_member_tenant_subcontractor_worker", ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_team_member_tenant_id_id"),
        sa.CheckConstraint("(employee_id IS NOT NULL AND subcontractor_worker_id IS NULL) OR (employee_id IS NULL AND subcontractor_worker_id IS NOT NULL)", name="team_member_exactly_one_actor"),
        sa.CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="team_member_window_valid"),
        schema="ops",
    )
    op.create_index("ix_ops_team_member_tenant_team", "team_member", ["tenant_id", "team_id", "valid_from"], unique=False, schema="ops")
    op.create_index(
        "uq_ops_team_member_single_lead",
        "team_member",
        ["tenant_id", "team_id"],
        unique=True,
        schema="ops",
        postgresql_where=sa.text("is_team_lead = true AND archived_at IS NULL"),
    )

    op.create_table(
        "assignment",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("demand_group_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("subcontractor_worker_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("assignment_status_code", sa.String(length=40), nullable=False, server_default="assigned"),
        sa.Column("assignment_source_code", sa.String(length=40), nullable=False, server_default="dispatcher"),
        sa.Column("offered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assignment")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_ops_assignment_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_id"], ["ops.shift.tenant_id", "ops.shift.id"], name="fk_ops_assignment_tenant_shift", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "demand_group_id"], ["ops.demand_group.tenant_id", "ops.demand_group.id"], name="fk_ops_assignment_tenant_demand_group", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "team_id"], ["ops.team.tenant_id", "ops.team.id"], name="fk_ops_assignment_tenant_team", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_ops_assignment_tenant_employee", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "subcontractor_worker_id"], ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"], name="fk_ops_assignment_tenant_subcontractor_worker", ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_assignment_tenant_id_id"),
        sa.CheckConstraint("(employee_id IS NOT NULL AND subcontractor_worker_id IS NULL) OR (employee_id IS NULL AND subcontractor_worker_id IS NOT NULL)", name="assignment_exactly_one_actor"),
        sa.CheckConstraint("assignment_status_code IN ('offered', 'assigned', 'confirmed', 'removed')", name="assignment_status_code_valid"),
        sa.CheckConstraint("assignment_source_code IN ('dispatcher', 'subcontractor_release', 'portal_allocation', 'manual')", name="assignment_source_code_valid"),
        schema="ops",
    )
    op.create_index("ix_ops_assignment_tenant_shift", "assignment", ["tenant_id", "shift_id", "created_at"], unique=False, schema="ops")
    op.create_index(
        "uq_ops_assignment_employee_active_per_shift",
        "assignment",
        ["tenant_id", "shift_id", "employee_id"],
        unique=True,
        schema="ops",
        postgresql_where=sa.text("employee_id IS NOT NULL AND assignment_status_code != 'removed' AND archived_at IS NULL"),
    )
    op.create_index(
        "uq_ops_assignment_worker_active_per_shift",
        "assignment",
        ["tenant_id", "shift_id", "subcontractor_worker_id"],
        unique=True,
        schema="ops",
        postgresql_where=sa.text("subcontractor_worker_id IS NOT NULL AND assignment_status_code != 'removed' AND archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_ops_assignment_worker_active_per_shift", table_name="assignment", schema="ops")
    op.drop_index("uq_ops_assignment_employee_active_per_shift", table_name="assignment", schema="ops")
    op.drop_index("ix_ops_assignment_tenant_shift", table_name="assignment", schema="ops")
    op.drop_table("assignment", schema="ops")
    op.drop_index("uq_ops_team_member_single_lead", table_name="team_member", schema="ops")
    op.drop_index("ix_ops_team_member_tenant_team", table_name="team_member", schema="ops")
    op.drop_table("team_member", schema="ops")
    op.drop_index("ix_ops_team_tenant_shift", table_name="team", schema="ops")
    op.drop_index("ix_ops_team_tenant_record", table_name="team", schema="ops")
    op.drop_table("team", schema="ops")
    op.drop_index("ix_ops_demand_group_tenant_shift", table_name="demand_group", schema="ops")
    op.drop_table("demand_group", schema="ops")
