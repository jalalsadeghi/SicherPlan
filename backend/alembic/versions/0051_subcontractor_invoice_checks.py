"""subcontractor invoice checks

Revision ID: 0051_subcontractor_invoice_checks
Revises: 0050_finance_invoice_delivery_context
Create Date: 2026-03-20 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0051_subcontractor_invoice_checks"
down_revision = "0050_finance_invoice_delivery_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subcontractor_rate_card",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("subcontractor_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=255), server_default="active", nullable=False),
        sa.Column("status_code", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("currency_code", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id", "subcontractor_id"], ["partner.subcontractor.tenant_id", "partner.subcontractor.id"], name="fk_partner_subcontractor_rate_card_tenant_subcontractor", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", "subcontractor_id", name="uq_partner_subcontractor_rate_card_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_rate_card_tenant_id_id"),
        sa.CheckConstraint("effective_until IS NULL OR effective_until >= effective_from", name="partner_subcontractor_rate_card_window_valid"),
        sa.CheckConstraint("status_code IN ('draft','active','archived')", name="partner_subcontractor_rate_card_status_valid"),
        schema="partner",
    )
    op.create_index("ix_partner_subcontractor_rate_card_window", "subcontractor_rate_card", ["tenant_id", "subcontractor_id", "effective_from"], unique=False, schema="partner")
    op.create_table(
        "subcontractor_rate_line",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("rate_card_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("function_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("qualification_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("line_code", sa.String(length=80), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("billing_unit_code", sa.String(length=20), server_default="hour", nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("minimum_quantity", sa.Numeric(12, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=255), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "function_type_id"], ["hr.function_type.tenant_id", "hr.function_type.id"], name="fk_partner_subcontractor_rate_line_tenant_function_type", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "qualification_type_id"], ["hr.qualification_type.tenant_id", "hr.qualification_type.id"], name="fk_partner_subcontractor_rate_line_tenant_qualification_type", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "rate_card_id"], ["partner.subcontractor_rate_card.tenant_id", "partner.subcontractor_rate_card.id"], name="fk_partner_subcontractor_rate_line_tenant_rate_card", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_rate_line_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "rate_card_id", "function_type_id", "qualification_type_id", "billing_unit_code", name="uq_partner_subcontractor_rate_line_dimensions"),
        sa.CheckConstraint("billing_unit_code IN ('hour','day','flat')", name="partner_subcontractor_rate_line_billing_unit_valid"),
        sa.CheckConstraint("unit_price >= 0", name="partner_subcontractor_rate_line_unit_price_nonnegative"),
        sa.CheckConstraint("minimum_quantity IS NULL OR minimum_quantity >= 0", name="partner_subcontractor_rate_line_minimum_nonnegative"),
        schema="partner",
    )

    op.create_table(
        "subcontractor_invoice_check",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("subcontractor_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("check_no", sa.String(length=120), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("period_label", sa.String(length=120), nullable=False),
        sa.Column("status_code", sa.String(length=40), server_default="draft", nullable=False),
        sa.Column("assigned_minutes_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("actual_minutes_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("approved_minutes_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expected_amount_total", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("approved_amount_total", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("comparison_variance_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("submitted_invoice_ref", sa.String(length=120), nullable=True),
        sa.Column("submitted_invoice_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("submitted_variance_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("submitted_invoice_currency_code", sa.String(length=3), nullable=True),
        sa.Column("review_reason_codes_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("last_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=255), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "subcontractor_id"], ["partner.subcontractor.tenant_id", "partner.subcontractor.id"], name="fk_finance_subcontractor_invoice_check_tenant_subcontractor", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_subcontractor_invoice_check_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "subcontractor_id", "period_start", "period_end", name="uq_finance_subcontractor_invoice_check_period"),
        sa.CheckConstraint("period_end >= period_start", name="subcontractor_invoice_check_period_valid"),
        sa.CheckConstraint("status_code IN ('draft','review_required','approved','exception','released')", name="subcontractor_invoice_check_status_valid"),
        sa.CheckConstraint("assigned_minutes_total >= 0", name="subcontractor_invoice_check_assigned_minutes_nonnegative"),
        sa.CheckConstraint("actual_minutes_total >= 0", name="subcontractor_invoice_check_actual_minutes_nonnegative"),
        sa.CheckConstraint("approved_minutes_total >= 0", name="subcontractor_invoice_check_approved_minutes_nonnegative"),
        schema="finance",
    )
    op.create_index("ix_finance_subcontractor_invoice_check_period", "subcontractor_invoice_check", ["tenant_id", "subcontractor_id", "period_start", "period_end"], unique=False, schema="finance")
    op.create_table(
        "subcontractor_invoice_check_line",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("invoice_check_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("actual_record_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("subcontractor_worker_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("rate_card_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("rate_line_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("function_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("qualification_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("billing_unit_code", sa.String(length=20), server_default="hour", nullable=False),
        sa.Column("assigned_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("actual_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("approved_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expected_quantity", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("actual_quantity", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("approved_quantity", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("expected_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("approved_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("variance_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("comparison_state_code", sa.String(length=40), server_default="clean", nullable=False),
        sa.Column("variance_reason_codes_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("source_ref_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=255), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "actual_record_id"], ["finance.actual_record.tenant_id", "finance.actual_record.id"], name="fk_finance_subcontractor_invoice_check_line_tenant_actual", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "assignment_id"], ["ops.assignment.tenant_id", "ops.assignment.id"], name="fk_finance_subcontractor_invoice_check_line_tenant_assignment", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "function_type_id"], ["hr.function_type.tenant_id", "hr.function_type.id"], name="fk_finance_subcontractor_invoice_check_line_tenant_function", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "invoice_check_id"], ["finance.subcontractor_invoice_check.tenant_id", "finance.subcontractor_invoice_check.id"], name="fk_finance_subcontractor_invoice_check_line_tenant_check", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "qualification_type_id"], ["hr.qualification_type.tenant_id", "hr.qualification_type.id"], name="fk_fin_sic_line_tenant_qual", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "rate_card_id"], ["partner.subcontractor_rate_card.tenant_id", "partner.subcontractor_rate_card.id"], name="fk_finance_subcontractor_invoice_check_line_tenant_rate_card", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "rate_line_id"], ["partner.subcontractor_rate_line.tenant_id", "partner.subcontractor_rate_line.id"], name="fk_finance_subcontractor_invoice_check_line_tenant_rate_line", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_id"], ["ops.shift.tenant_id", "ops.shift.id"], name="fk_finance_subcontractor_invoice_check_line_tenant_shift", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "subcontractor_worker_id"], ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"], name="fk_finance_subcontractor_invoice_check_line_tenant_worker", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_subcontractor_invoice_check_line_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "invoice_check_id", "assignment_id", "actual_record_id", name="uq_finance_subcontractor_invoice_check_line_source"),
        sa.CheckConstraint("comparison_state_code IN ('clean','warning','needs_review')", name="subcontractor_invoice_check_line_comparison_state_valid"),
        sa.CheckConstraint("expected_quantity >= 0", name="subcontractor_invoice_check_line_expected_quantity_nonnegative"),
        sa.CheckConstraint("actual_quantity >= 0", name="subcontractor_invoice_check_line_actual_quantity_nonnegative"),
        sa.CheckConstraint("approved_quantity >= 0", name="subcontractor_invoice_check_line_approved_quantity_nonnegative"),
        schema="finance",
    )
    op.create_index("ix_finance_subcontractor_invoice_check_line_sort", "subcontractor_invoice_check_line", ["tenant_id", "invoice_check_id", "sort_order"], unique=False, schema="finance")
    op.create_table(
        "subcontractor_invoice_check_note",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("invoice_check_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("visibility_code", sa.String(length=40), server_default="internal", nullable=False),
        sa.Column("note_kind_code", sa.String(length=40), server_default="note", nullable=False),
        sa.Column("note_text", sa.String(length=2000), nullable=False),
        sa.Column("status", sa.String(length=255), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "invoice_check_id"], ["finance.subcontractor_invoice_check.tenant_id", "finance.subcontractor_invoice_check.id"], name="fk_finance_subcontractor_invoice_check_note_tenant_check", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_subcontractor_invoice_check_note_tenant_id_id"),
        sa.CheckConstraint("visibility_code IN ('internal')", name="subcontractor_invoice_check_note_visibility_valid"),
        sa.CheckConstraint("note_kind_code IN ('note','exception','approval')", name="subcontractor_invoice_check_note_kind_valid"),
        schema="finance",
    )


def downgrade() -> None:
    op.drop_table("subcontractor_invoice_check_note", schema="finance")
    op.drop_index("ix_finance_subcontractor_invoice_check_line_sort", table_name="subcontractor_invoice_check_line", schema="finance")
    op.drop_table("subcontractor_invoice_check_line", schema="finance")
    op.drop_index("ix_finance_subcontractor_invoice_check_period", table_name="subcontractor_invoice_check", schema="finance")
    op.drop_table("subcontractor_invoice_check", schema="finance")
    op.drop_table("subcontractor_rate_line", schema="partner")
    op.drop_index("ix_partner_subcontractor_rate_card_window", table_name="subcontractor_rate_card", schema="partner")
    op.drop_table("subcontractor_rate_card", schema="partner")
