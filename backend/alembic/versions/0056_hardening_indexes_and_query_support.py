"""US-33-T1 hardening indexes for reporting, docs, and evidence-heavy paths."""

from __future__ import annotations

from alembic import op


revision = "0056_hardening_indexes_and_query_support"
down_revision = "0055_reporting_view_security_activity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_audit_login_event_failure_tenant_created
            ON audit.login_event (tenant_id, created_at DESC)
            WHERE outcome = 'failure';

        CREATE INDEX IF NOT EXISTS ix_audit_audit_event_tenant_event_created
            ON audit.audit_event (tenant_id, event_type, created_at DESC);

        CREATE INDEX IF NOT EXISTS ix_audit_audit_event_tenant_request_created
            ON audit.audit_event (tenant_id, request_id, created_at DESC)
            WHERE request_id IS NOT NULL;

        CREATE INDEX IF NOT EXISTS ix_field_time_event_tenant_employee_occurred
            ON field.time_event (tenant_id, employee_id, occurred_at DESC)
            WHERE employee_id IS NOT NULL;

        CREATE INDEX IF NOT EXISTS ix_field_time_event_tenant_worker_occurred
            ON field.time_event (tenant_id, subcontractor_worker_id, occurred_at DESC)
            WHERE subcontractor_worker_id IS NOT NULL;

        CREATE INDEX IF NOT EXISTS ix_finance_actual_record_tenant_stage_current
            ON finance.actual_record (tenant_id, approval_stage_code, derived_at DESC)
            WHERE is_current = true AND archived_at IS NULL;

        CREATE INDEX IF NOT EXISTS ix_docs_document_link_owner_relation_lookup
            ON docs.document_link (tenant_id, owner_type, owner_id, relation_type);

        CREATE INDEX IF NOT EXISTS ix_integration_job_reporting_export_report_key
            ON integration.import_export_job (
                tenant_id,
                ((request_payload_json ->> 'report_key')),
                created_at DESC
            )
            WHERE job_type = 'reporting_export';
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS integration.ix_integration_job_reporting_export_report_key;
        DROP INDEX IF EXISTS docs.ix_docs_document_link_owner_relation_lookup;
        DROP INDEX IF EXISTS finance.ix_finance_actual_record_tenant_stage_current;
        DROP INDEX IF EXISTS field.ix_field_time_event_tenant_worker_occurred;
        DROP INDEX IF EXISTS field.ix_field_time_event_tenant_employee_occurred;
        DROP INDEX IF EXISTS audit.ix_audit_audit_event_tenant_request_created;
        DROP INDEX IF EXISTS audit.ix_audit_audit_event_tenant_event_created;
        DROP INDEX IF EXISTS audit.ix_audit_login_event_failure_tenant_created;
        """
    )
