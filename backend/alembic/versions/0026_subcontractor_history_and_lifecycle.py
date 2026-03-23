"""subcontractor history and lifecycle

Revision ID: 0026_subcontractor_history_and_lifecycle
Revises: 0025_subcontractor_master_foundation
Create Date: 2026-03-20 04:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0026_subcontractor_history_and_lifecycle"
down_revision = "0025_subcontractor_master_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subcontractor_history_entry",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("subcontractor_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("entry_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("related_contact_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_subcontractor_history_entry_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "subcontractor_id"], ["partner.subcontractor.tenant_id", "partner.subcontractor.id"], name="fk_partner_subcontractor_history_tenant_subcontractor", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["iam.user_account.id"], name="fk_partner_history_actor_user_account", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["related_contact_id"], ["partner.subcontractor_contact.id"], name="fk_partner_history_contact_subcontractor_contact", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subcontractor_history_entry")),
        schema="partner",
    )
    op.create_index(
        "ix_partner_subcontractor_history_company_occurred",
        "subcontractor_history_entry",
        ["tenant_id", "subcontractor_id", "occurred_at", "created_at"],
        unique=False,
        schema="partner",
    )


def downgrade() -> None:
    op.drop_index("ix_partner_subcontractor_history_company_occurred", table_name="subcontractor_history_entry", schema="partner")
    op.drop_table("subcontractor_history_entry", schema="partner")
