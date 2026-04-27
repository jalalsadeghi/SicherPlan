"""Add assistant knowledge chunk metadata.

Revision ID: 0065_assistant_knowledge_chunk_metadata
Revises: 0064_assistant_page_help_manifest
Create Date: 2026-04-27 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0065_assistant_knowledge_chunk_metadata"
down_revision = "0064_assistant_page_help_manifest"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "knowledge_source",
        sa.Column("source_language", sa.String(length=16), nullable=True),
        schema="assistant",
    )
    op.add_column(
        "knowledge_chunk",
        sa.Column("content_preview", sa.String(length=255), nullable=True),
        schema="assistant",
    )
    op.add_column(
        "knowledge_chunk",
        sa.Column("workflow_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="assistant",
    )
    op.add_column(
        "knowledge_chunk",
        sa.Column("api_families", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="assistant",
    )
    op.add_column(
        "knowledge_chunk",
        sa.Column("domain_terms", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="assistant",
    )
    op.add_column(
        "knowledge_chunk",
        sa.Column("language_aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="assistant",
    )


def downgrade() -> None:
    op.drop_column("knowledge_chunk", "language_aliases", schema="assistant")
    op.drop_column("knowledge_chunk", "domain_terms", schema="assistant")
    op.drop_column("knowledge_chunk", "api_families", schema="assistant")
    op.drop_column("knowledge_chunk", "workflow_keys", schema="assistant")
    op.drop_column("knowledge_chunk", "content_preview", schema="assistant")
    op.drop_column("knowledge_source", "source_language", schema="assistant")
