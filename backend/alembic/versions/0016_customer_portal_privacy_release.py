"""Add explicit portal person-name release controls to customers.

Revision ID: 0016_customer_portal_privacy_release
Revises: 0015_customer_collaboration_controls
Create Date: 2026-03-19 18:55:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0016_customer_portal_privacy_release"
down_revision = "0015_customer_collaboration_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customer",
        sa.Column("portal_person_names_released", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        schema="crm",
    )
    op.add_column(
        "customer",
        sa.Column("portal_person_names_released_at", sa.DateTime(timezone=True), nullable=True),
        schema="crm",
    )
    op.add_column(
        "customer",
        sa.Column("portal_person_names_released_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        schema="crm",
    )


def downgrade() -> None:
    op.drop_column("customer", "portal_person_names_released_by_user_id", schema="crm")
    op.drop_column("customer", "portal_person_names_released_at", schema="crm")
    op.drop_column("customer", "portal_person_names_released", schema="crm")
