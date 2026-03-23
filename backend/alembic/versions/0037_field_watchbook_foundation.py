"""field watchbook foundation

Revision ID: 0037_field_watchbook_foundation
Revises: 0036_assignment_validation_override
Create Date: 2026-03-20 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0037_field_watchbook_foundation"
down_revision = "0036_assignment_validation_override"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS field")
    op.create_table(
        "watchbook",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("context_type", sa.String(length=40), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("headline", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("review_status_code", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supervisor_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("supervisor_note", sa.Text(), nullable=True),
        sa.Column("closure_state_code", sa.String(length=40), server_default="open", nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("pdf_document_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("customer_visibility_released", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("subcontractor_visibility_released", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("customer_participation_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("subcontractor_participation_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("customer_personal_names_released", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("subcontractor_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint(
            "(CASE WHEN site_id IS NULL THEN 0 ELSE 1 END + CASE WHEN order_id IS NULL THEN 0 ELSE 1 END + CASE WHEN planning_record_id IS NULL THEN 0 ELSE 1 END) = 1",
            name="ck_watchbook_context_exactly_one",
        ),
        sa.CheckConstraint("context_type IN ('site','order','planning_record')", name="ck_watchbook_context_type_valid"),
        sa.CheckConstraint("review_status_code IN ('pending','reviewed')", name="ck_watchbook_review_status_valid"),
        sa.CheckConstraint("closure_state_code IN ('open','closed')", name="ck_watchbook_closure_state_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "customer_id"], ["crm.customer.tenant_id", "crm.customer.id"], name="fk_field_watchbook_tenant_customer", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "site_id"], ["ops.site.tenant_id", "ops.site.id"], name="fk_field_watchbook_tenant_site", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["ops.customer_order.tenant_id", "ops.customer_order.id"], name="fk_field_watchbook_tenant_order", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "planning_record_id"], ["ops.planning_record.tenant_id", "ops.planning_record.id"], name="fk_field_watchbook_tenant_planning_record", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_id"], ["ops.shift.tenant_id", "ops.shift.id"], name="fk_field_watchbook_tenant_shift", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "subcontractor_id"], ["partner.subcontractor.tenant_id", "partner.subcontractor.id"], name="fk_field_watchbook_tenant_subcontractor", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["supervisor_user_id"], ["iam.user_account.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["closed_by_user_id"], ["iam.user_account.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["pdf_document_id"], ["docs.document.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_field_watchbook_tenant_id_id"),
        schema="field",
    )
    op.create_index("ix_field_watchbook_context_lookup", "watchbook", ["tenant_id", "customer_id", "log_date"], unique=False, schema="field")
    op.create_index(
        "uq_field_watchbook_open_context_date",
        "watchbook",
        ["tenant_id", "log_date", "context_type", "site_id", "order_id", "planning_record_id"],
        unique=True,
        schema="field",
        postgresql_where=sa.text("closure_state_code = 'open' AND archived_at IS NULL"),
    )
    op.create_table(
        "watchbook_entry",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("watchbook_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("entry_type_code", sa.String(length=40), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=False),
        sa.Column("traffic_light_code", sa.String(length=20), nullable=True),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("author_actor_type", sa.String(length=40), server_default="internal", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("entry_type_code IN ('remark','incident','handover','status','customer_note','subcontractor_note','employee_note')", name="ck_watchbook_entry_type_valid"),
        sa.CheckConstraint("author_actor_type IN ('internal','employee','customer','subcontractor')", name="ck_watchbook_entry_author_actor_valid"),
        sa.CheckConstraint("traffic_light_code IS NULL OR traffic_light_code IN ('green','yellow','red')", name="ck_watchbook_entry_traffic_light_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "watchbook_id"], ["field.watchbook.tenant_id", "field.watchbook.id"], name="fk_field_watchbook_entry_tenant_watchbook", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "assignment_id"], ["ops.assignment.tenant_id", "ops.assignment.id"], name="fk_field_watchbook_entry_tenant_assignment", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["author_user_id"], ["iam.user_account.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        schema="field",
    )
    op.create_index("ix_field_watchbook_entry_watchbook_occurred_at", "watchbook_entry", ["watchbook_id", "occurred_at"], unique=False, schema="field")


def downgrade() -> None:
    op.drop_index("ix_field_watchbook_entry_watchbook_occurred_at", table_name="watchbook_entry", schema="field")
    op.drop_table("watchbook_entry", schema="field")
    op.drop_index("uq_field_watchbook_open_context_date", table_name="watchbook", schema="field")
    op.drop_index("ix_field_watchbook_context_lookup", table_name="watchbook", schema="field")
    op.drop_table("watchbook", schema="field")
