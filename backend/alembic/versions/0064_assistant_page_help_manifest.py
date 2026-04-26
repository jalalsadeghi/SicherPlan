"""Add assistant page help manifest table.

Revision ID: 0064_assistant_page_help_manifest
Revises: 0063_assistant_persistence_baseline
Create Date: 2026-04-26 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0064_assistant_page_help_manifest"
down_revision = "0063_assistant_persistence_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "page_help_manifest",
        sa.Column("page_id", sa.String(length=120), nullable=False),
        sa.Column("route_name", sa.String(length=255), nullable=True),
        sa.Column("path_template", sa.String(length=500), nullable=True),
        sa.Column("module_key", sa.String(length=120), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("manifest_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("manifest_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("verified_from", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'draft', 'unverified')",
            name="assistant_page_help_manifest_status_valid",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_page_help_manifest"),
        sa.UniqueConstraint(
            "page_id",
            "language_code",
            "manifest_version",
            name="uq_assistant_page_help_manifest_page_lang_version",
        ),
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_page_help_manifest_page_active",
        "page_help_manifest",
        ["page_id", "status"],
        unique=False,
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_page_help_manifest_module",
        "page_help_manifest",
        ["module_key"],
        unique=False,
        schema="assistant",
    )


def downgrade() -> None:
    op.drop_index("ix_assistant_page_help_manifest_module", table_name="page_help_manifest", schema="assistant")
    op.drop_index("ix_assistant_page_help_manifest_page_active", table_name="page_help_manifest", schema="assistant")
    op.drop_table("page_help_manifest", schema="assistant")
