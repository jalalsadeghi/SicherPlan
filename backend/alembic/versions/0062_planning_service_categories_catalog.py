"""Add planning service categories catalog.

Revision ID: 0062_planning_service_categories_catalog
Revises: 0061_planning_catalogs_tenant_scope
Create Date: 2026-04-22 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0062_planning_service_categories_catalog"
down_revision = "0061_planning_catalogs_tenant_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_category",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_ops_service_category_tenant_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_service_category_tenant_id_id"),
        schema="ops",
    )
    op.execute(
        """
        INSERT INTO ops.service_category (
            id,
            tenant_id,
            code,
            label,
            description,
            sort_order,
            status,
            created_at,
            updated_at,
            version_no
        )
        SELECT
            gen_random_uuid(),
            tenant.id,
            lookup.code,
            lookup.label,
            lookup.description,
            lookup.sort_order,
            'active',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            1
        FROM core.tenant AS tenant
        CROSS JOIN core.lookup_value AS lookup
        WHERE lookup.tenant_id IS NULL
          AND lookup.domain = 'service_category'
          AND lookup.archived_at IS NULL
        ON CONFLICT ON CONSTRAINT uq_ops_service_category_tenant_code DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("service_category", schema="ops")
