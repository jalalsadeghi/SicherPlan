"""subcontractor releases

Revision ID: 0035_subcontractor_releases
Revises: 0034_staffing_backbone
Create Date: 2026-03-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0035_subcontractor_releases"
down_revision = "0034_staffing_backbone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subcontractor_release",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("demand_group_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("subcontractor_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("released_qty", sa.Integer(), nullable=False),
        sa.Column("release_status_code", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subcontractor_release")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_ops_subcontractor_release_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_id"], ["ops.shift.tenant_id", "ops.shift.id"], name="fk_ops_subcontractor_release_tenant_shift", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "demand_group_id"], ["ops.demand_group.tenant_id", "ops.demand_group.id"], name="fk_ops_subcontractor_release_tenant_demand_group", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "subcontractor_id"], ["partner.subcontractor.tenant_id", "partner.subcontractor.id"], name="fk_ops_subcontractor_release_tenant_subcontractor", ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_subcontractor_release_tenant_id_id"),
        sa.CheckConstraint("released_qty >= 1", name="subcontractor_release_qty_positive"),
        sa.CheckConstraint("release_status_code IN ('draft', 'released', 'revoked')", name="subcontractor_release_status_code_valid"),
        schema="ops",
    )
    op.create_index(
        "uq_ops_subcontractor_release_active_tuple",
        "subcontractor_release",
        ["tenant_id", "shift_id", "demand_group_id", "subcontractor_id"],
        unique=True,
        schema="ops",
        postgresql_where=sa.text("release_status_code != 'revoked' AND archived_at IS NULL"),
    )
    op.create_index("ix_ops_subcontractor_release_tenant_shift", "subcontractor_release", ["tenant_id", "shift_id", "created_at"], unique=False, schema="ops")


def downgrade() -> None:
    op.drop_index("ix_ops_subcontractor_release_tenant_shift", table_name="subcontractor_release", schema="ops")
    op.drop_index("uq_ops_subcontractor_release_active_tuple", table_name="subcontractor_release", schema="ops")
    op.drop_table("subcontractor_release", schema="ops")
