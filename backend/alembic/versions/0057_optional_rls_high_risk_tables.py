"""US-33-T2 optional PostgreSQL RLS on high-risk tenant-owned tables."""

from __future__ import annotations

from alembic import op


revision = "0057_optional_rls_high_risk_tables"
down_revision = "0056_hardening_indexes_and_query_support"
branch_labels = None
depends_on = None


_POLICY_PREDICATE = """
(
    COALESCE(current_setting('app.rls_mode', true), 'off') <> 'enforce'
    OR COALESCE(current_setting('app.rls_bypass', true), 'off') = 'on'
    OR tenant_id::text = COALESCE(current_setting('app.tenant_id', true), '')
)
"""


def upgrade() -> None:
    for table_name in (
        "docs.document",
        "docs.document_version",
        "docs.document_link",
        "finance.actual_record",
    ):
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")

    op.execute(
        f"""
        DROP POLICY IF EXISTS rls_docs_document_tenant_guard ON docs.document;
        CREATE POLICY rls_docs_document_tenant_guard
            ON docs.document
            FOR ALL
            USING {_POLICY_PREDICATE}
            WITH CHECK {_POLICY_PREDICATE};

        DROP POLICY IF EXISTS rls_docs_document_version_tenant_guard ON docs.document_version;
        CREATE POLICY rls_docs_document_version_tenant_guard
            ON docs.document_version
            FOR ALL
            USING {_POLICY_PREDICATE}
            WITH CHECK {_POLICY_PREDICATE};

        DROP POLICY IF EXISTS rls_docs_document_link_tenant_guard ON docs.document_link;
        CREATE POLICY rls_docs_document_link_tenant_guard
            ON docs.document_link
            FOR ALL
            USING {_POLICY_PREDICATE}
            WITH CHECK {_POLICY_PREDICATE};

        DROP POLICY IF EXISTS rls_finance_actual_record_tenant_guard ON finance.actual_record;
        CREATE POLICY rls_finance_actual_record_tenant_guard
            ON finance.actual_record
            FOR ALL
            USING {_POLICY_PREDICATE}
            WITH CHECK {_POLICY_PREDICATE};
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP POLICY IF EXISTS rls_finance_actual_record_tenant_guard ON finance.actual_record;
        DROP POLICY IF EXISTS rls_docs_document_link_tenant_guard ON docs.document_link;
        DROP POLICY IF EXISTS rls_docs_document_version_tenant_guard ON docs.document_version;
        DROP POLICY IF EXISTS rls_docs_document_tenant_guard ON docs.document;

        ALTER TABLE finance.actual_record DISABLE ROW LEVEL SECURITY;
        ALTER TABLE docs.document_link DISABLE ROW LEVEL SECURITY;
        ALTER TABLE docs.document_version DISABLE ROW LEVEL SECURITY;
        ALTER TABLE docs.document DISABLE ROW LEVEL SECURITY;
        """
    )
