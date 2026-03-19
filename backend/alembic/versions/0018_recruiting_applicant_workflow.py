"""recruiting applicant workflow

Revision ID: 0018_recruiting_applicant_workflow
Revises: 0017_recruiting_applicant_intake
Create Date: 2026-03-19 20:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0018_recruiting_applicant_workflow"
down_revision = "0017_recruiting_applicant_intake"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("applicant", "status", server_default="submitted", schema="hr")
    op.create_unique_constraint("uq_hr_applicant_tenant_id_id", "applicant", ["tenant_id", "id"], schema="hr")

    op.create_table(
        "applicant_status_event",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("applicant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("from_status", sa.String(length=40), nullable=True),
        sa.Column("to_status", sa.String(length=40), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("interview_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hiring_target_date", sa.Date(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["iam.user_account.id"], name=op.f("fk_applicant_status_event_actor_user_id_user_account"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_applicant_status_event_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "applicant_id"],
            ["hr.applicant.tenant_id", "hr.applicant.id"],
            name="fk_hr_applicant_status_event_tenant_applicant",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applicant_status_event")),
        schema="hr",
    )
    op.create_index(
        "ix_hr_applicant_status_event_tenant_applicant_created",
        "applicant_status_event",
        ["tenant_id", "applicant_id", "created_at"],
        unique=False,
        schema="hr",
    )
    op.create_index(
        "ix_hr_applicant_status_event_tenant_to_status",
        "applicant_status_event",
        ["tenant_id", "to_status"],
        unique=False,
        schema="hr",
    )


def downgrade() -> None:
    op.drop_index("ix_hr_applicant_status_event_tenant_to_status", table_name="applicant_status_event", schema="hr")
    op.drop_index(
        "ix_hr_applicant_status_event_tenant_applicant_created",
        table_name="applicant_status_event",
        schema="hr",
    )
    op.drop_table("applicant_status_event", schema="hr")
    op.drop_constraint("uq_hr_applicant_tenant_id_id", "applicant", schema="hr", type_="unique")
    op.alter_column("applicant", "status", server_default="active", schema="hr")
