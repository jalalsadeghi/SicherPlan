"""Customer history entries.

Revision ID: 0011_customer_history_and_exports
Revises: 0010_customer_master_backbone
Create Date: 2026-03-19 05:05:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0011_customer_history_and_exports"
down_revision = "0010_customer_master_backbone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=32),
        type_=sa.String(length=255),
        nullable=False,
    )
    op.create_table(
        "customer_history_entry",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("entry_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("related_contact_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("related_address_link_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("integration_job_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("before_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("after_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["actor_user_id"], ["iam.user_account.id"], name="fk_crm_history_actor_user_account", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["integration_job_id"], ["integration.import_export_job.id"], name="fk_crm_history_job_import_export_job", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["related_address_link_id"], ["crm.customer_address.id"], name="fk_crm_history_addr_link_customer_address", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["related_contact_id"], ["crm.customer_contact.id"], name="fk_crm_history_contact_customer_contact", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_customer_history_entry_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "customer_id"], ["crm.customer.tenant_id", "crm.customer.id"], name="fk_crm_customer_history_entry_tenant_customer", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_customer_history_entry"),
        schema="crm",
    )
    op.create_index(
        "ix_crm_customer_history_entry_customer_created_at",
        "customer_history_entry",
        ["tenant_id", "customer_id", "created_at"],
        unique=False,
        schema="crm",
    )


def downgrade() -> None:
    op.drop_index("ix_crm_customer_history_entry_customer_created_at", table_name="customer_history_entry", schema="crm")
    op.drop_table("customer_history_entry", schema="crm")
