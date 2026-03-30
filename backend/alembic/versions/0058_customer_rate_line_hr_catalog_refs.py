"""Normalize customer rate-line HR catalog references to UUID foreign keys.

Legacy test-stage rows could still contain provisional string values like
``func-guard`` or ``qual-34a-basic``. This migration keeps only values that can
be resolved to real HR catalog UUIDs inside the same tenant and safely nulls
everything else before adding the tenant-safe foreign keys.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0058_customer_rate_line_hr_catalog_refs"
down_revision = "0057_optional_rls_high_risk_tables"
branch_labels = None
depends_on = None


UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"


def upgrade() -> None:
    op.add_column(
        "customer_rate_line",
        sa.Column("function_type_id_uuid", postgresql.UUID(as_uuid=False), nullable=True),
        schema="crm",
    )
    op.add_column(
        "customer_rate_line",
        sa.Column("qualification_type_id_uuid", postgresql.UUID(as_uuid=False), nullable=True),
        schema="crm",
    )

    op.execute(
        sa.text(
            f"""
            UPDATE crm.customer_rate_line AS line
            SET function_type_id_uuid = line.function_type_id::uuid
            WHERE line.function_type_id IS NOT NULL
              AND line.function_type_id ~* '{UUID_PATTERN}'
              AND EXISTS (
                SELECT 1
                FROM hr.function_type AS function_type
                WHERE function_type.tenant_id = line.tenant_id
                  AND function_type.id = line.function_type_id::uuid
              )
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            UPDATE crm.customer_rate_line AS line
            SET qualification_type_id_uuid = line.qualification_type_id::uuid
            WHERE line.qualification_type_id IS NOT NULL
              AND line.qualification_type_id ~* '{UUID_PATTERN}'
              AND EXISTS (
                SELECT 1
                FROM hr.qualification_type AS qualification_type
                WHERE qualification_type.tenant_id = line.tenant_id
                  AND qualification_type.id = line.qualification_type_id::uuid
              )
            """
        )
    )

    op.drop_column("customer_rate_line", "function_type_id", schema="crm")
    op.drop_column("customer_rate_line", "qualification_type_id", schema="crm")
    op.alter_column(
        "customer_rate_line",
        "function_type_id_uuid",
        new_column_name="function_type_id",
        existing_type=postgresql.UUID(as_uuid=False),
        schema="crm",
    )
    op.alter_column(
        "customer_rate_line",
        "qualification_type_id_uuid",
        new_column_name="qualification_type_id",
        existing_type=postgresql.UUID(as_uuid=False),
        schema="crm",
    )

    op.create_foreign_key(
        "fk_crm_customer_rate_line_tenant_function_type",
        "customer_rate_line",
        "function_type",
        ["tenant_id", "function_type_id"],
        ["tenant_id", "id"],
        source_schema="crm",
        referent_schema="hr",
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_crm_customer_rate_line_tenant_qualification_type",
        "customer_rate_line",
        "qualification_type",
        ["tenant_id", "qualification_type_id"],
        ["tenant_id", "id"],
        source_schema="crm",
        referent_schema="hr",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_crm_customer_rate_line_tenant_function_type",
        "customer_rate_line",
        schema="crm",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_crm_customer_rate_line_tenant_qualification_type",
        "customer_rate_line",
        schema="crm",
        type_="foreignkey",
    )

    op.add_column(
        "customer_rate_line",
        sa.Column("function_type_id_legacy", sa.String(length=36), nullable=True),
        schema="crm",
    )
    op.add_column(
        "customer_rate_line",
        sa.Column("qualification_type_id_legacy", sa.String(length=36), nullable=True),
        schema="crm",
    )
    op.execute(
        sa.text(
            """
            UPDATE crm.customer_rate_line
            SET function_type_id_legacy = function_type_id::text,
                qualification_type_id_legacy = qualification_type_id::text
            """
        )
    )
    op.drop_column("customer_rate_line", "function_type_id", schema="crm")
    op.drop_column("customer_rate_line", "qualification_type_id", schema="crm")
    op.alter_column(
        "customer_rate_line",
        "function_type_id_legacy",
        new_column_name="function_type_id",
        existing_type=sa.String(length=36),
        schema="crm",
    )
    op.alter_column(
        "customer_rate_line",
        "qualification_type_id_legacy",
        new_column_name="qualification_type_id",
        existing_type=sa.String(length=36),
        schema="crm",
    )
