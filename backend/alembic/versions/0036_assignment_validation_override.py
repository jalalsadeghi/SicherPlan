"""US-20-T4 assignment validation override evidence."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0036_assignment_validation_override"
down_revision = "0035_subcontractor_releases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assignment_validation_override",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("rule_code", sa.String(length=120), nullable=False),
        sa.Column("reason_text", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assignment_validation_override")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["ops.assignment.tenant_id", "ops.assignment.id"],
            name="fk_ops_assignment_validation_override_tenant_assignment",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["iam.user_account.id"],
            name="fk_ops_assignment_validation_override_actor_user",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_assignment_validation_override_tenant_id_id"),
        schema="ops",
    )
    op.create_index(
        "ix_ops_assignment_validation_override_assignment_created",
        "assignment_validation_override",
        ["tenant_id", "assignment_id", "created_at"],
        unique=False,
        schema="ops",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ops_assignment_validation_override_assignment_created",
        table_name="assignment_validation_override",
        schema="ops",
    )
    op.drop_table("assignment_validation_override", schema="ops")
