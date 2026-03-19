"""recruiting applicant intake

Revision ID: 0017_recruiting_applicant_intake
Revises: 0016_customer_portal_privacy_release
Create Date: 2026-03-19 18:25:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0017_recruiting_applicant_intake"
down_revision = "0016_customer_portal_privacy_release"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS hr")

    op.create_table(
        "applicant",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("application_no", sa.String(length=40), nullable=False),
        sa.Column("submission_key", sa.String(length=80), nullable=False),
        sa.Column("source_channel", sa.String(length=80), nullable=False, server_default="public_form"),
        sa.Column("source_detail", sa.String(length=255), nullable=True),
        sa.Column("locale", sa.String(length=10), nullable=False, server_default="de"),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("desired_role", sa.String(length=255), nullable=True),
        sa.Column("availability_date", sa.Date(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("gdpr_consent_granted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("gdpr_consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("gdpr_policy_ref", sa.String(length=255), nullable=False),
        sa.Column("gdpr_policy_version", sa.String(length=80), nullable=False),
        sa.Column("custom_fields_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("submitted_ip", sa.String(length=64), nullable=True),
        sa.Column("submitted_origin", sa.String(length=255), nullable=True),
        sa.Column("submitted_user_agent", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_applicant_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applicant")),
        sa.UniqueConstraint("tenant_id", "application_no", name="uq_hr_applicant_tenant_application_no"),
        sa.UniqueConstraint("tenant_id", "submission_key", name="uq_hr_applicant_tenant_submission_key"),
        schema="hr",
    )
    op.create_index("ix_hr_applicant_tenant_status", "applicant", ["tenant_id", "status"], unique=False, schema="hr")
    op.create_index("ix_hr_applicant_tenant_email", "applicant", ["tenant_id", "email"], unique=False, schema="hr")


def downgrade() -> None:
    op.drop_index("ix_hr_applicant_tenant_email", table_name="applicant", schema="hr")
    op.drop_index("ix_hr_applicant_tenant_status", table_name="applicant", schema="hr")
    op.drop_table("applicant", schema="hr")
