"""employee file notes

Revision ID: 0021_employee_file_notes
Revises: 0020_recruiting_applicant_conversion
Create Date: 2026-03-19 23:05:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0021_employee_file_notes"
down_revision = "0020_recruiting_applicant_conversion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employee_note",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("note_type", sa.String(length=40), nullable=False, server_default="operational_note"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("reminder_at", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.Date(), nullable=True),
        sa.Column("completed_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint(
            "note_type IN ('operational_note', 'positive_activity', 'reminder')",
            name="employee_note_type_valid",
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR reminder_at IS NOT NULL OR note_type <> 'reminder'",
            name="employee_note_completion_requires_reminder",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_note_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_note_tenant_employee",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_note")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_note_tenant_id_id"),
        schema="hr",
    )


def downgrade() -> None:
    op.drop_table("employee_note", schema="hr")
