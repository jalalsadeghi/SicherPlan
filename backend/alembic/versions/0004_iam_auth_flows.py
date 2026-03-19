"""IAM auth flow support tables.

Revision ID: 0004_iam_auth_flows
Revises: 0003_iam_foundation
Create Date: 2026-03-19 00:00:03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_iam_auth_flows"
down_revision = "0003_iam_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_token",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_account_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_ip", sa.String(length=64), nullable=True),
        sa.Column("requested_user_agent", sa.Text(), nullable=True),
        sa.Column("delivery_channel", sa.String(length=40), nullable=False, server_default="email"),
        sa.Column("delivery_reference", sa.String(length=255), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_password_reset_token_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_account_id"], ["iam.user_account.id"], name="fk_password_reset_token_user_account_id_user_account", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_password_reset_token"),
        sa.UniqueConstraint("token_hash", name="uq_iam_password_reset_token_hash"),
        schema="iam",
    )
    op.create_index(
        "ix_iam_password_reset_token_user_account_used_at",
        "password_reset_token",
        ["user_account_id", "used_at"],
        unique=False,
        schema="iam",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_iam_password_reset_token_user_account_used_at",
        table_name="password_reset_token",
        schema="iam",
    )
    op.drop_table("password_reset_token", schema="iam")
