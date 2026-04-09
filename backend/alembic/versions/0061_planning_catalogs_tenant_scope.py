"""Relax planning catalog customer scope for tenant-level reuse.

Revision ID: 0061_planning_catalogs_tenant_scope
Revises: 0060_seed_employee_document_types
Create Date: 2026-04-09 00:00:00
"""

from __future__ import annotations
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0061_planning_catalogs_tenant_scope"
down_revision = "0060_seed_employee_document_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "requirement_type",
        "customer_id",
        schema="ops",
        existing_type=postgresql.UUID(as_uuid=False),
        nullable=True,
    )
    op.alter_column(
        "equipment_item",
        "customer_id",
        schema="ops",
        existing_type=postgresql.UUID(as_uuid=False),
        nullable=True,
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE ops.requirement_type
        SET customer_id = seed.customer_id
        FROM (
          SELECT t.id AS tenant_id, MIN(c.id) AS customer_id
          FROM core.tenant AS t
          JOIN crm.customer AS c
            ON c.tenant_id = t.id
          GROUP BY t.id
        ) AS seed
        WHERE ops.requirement_type.customer_id IS NULL
          AND seed.tenant_id = ops.requirement_type.tenant_id
        """
    )
    op.execute(
        """
        UPDATE ops.equipment_item
        SET customer_id = seed.customer_id
        FROM (
          SELECT t.id AS tenant_id, MIN(c.id) AS customer_id
          FROM core.tenant AS t
          JOIN crm.customer AS c
            ON c.tenant_id = t.id
          GROUP BY t.id
        ) AS seed
        WHERE ops.equipment_item.customer_id IS NULL
          AND seed.tenant_id = ops.equipment_item.tenant_id
        """
    )
    op.alter_column(
        "requirement_type",
        "customer_id",
        schema="ops",
        existing_type=postgresql.UUID(as_uuid=False),
        nullable=False,
    )
    op.alter_column(
        "equipment_item",
        "customer_id",
        schema="ops",
        existing_type=postgresql.UUID(as_uuid=False),
        nullable=False,
    )
