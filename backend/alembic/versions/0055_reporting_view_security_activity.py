"""US-32-T3 security activity reporting view."""

from __future__ import annotations

from alembic import op


revision = "0055_reporting_view_security_activity"
down_revision = "0054_reporting_views_compliance_and_qm"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.security_activity_v AS
        WITH login_failure AS (
            SELECT
                le.tenant_id,
                'audit.login_event'::text AS source_table,
                le.id AS source_id,
                le.created_at AS occurred_at,
                'login_failure'::text AS category_code,
                'warning'::text AS severity_code,
                'failure'::text AS result_status_code,
                le.user_account_id AS actor_user_id,
                COALESCE(ua.full_name, le.identifier) AS actor_display_name,
                NULL::uuid AS branch_id,
                NULL::uuid AS mandate_id,
                le.request_id,
                'iam.user_account'::text AS entity_type,
                COALESCE(le.user_account_id::text, le.id::text) AS entity_id,
                'iam.auth.login'::text AS event_type,
                NULL::text AS role_key,
                NULL::text AS scope_type,
                COALESCE(le.failure_reason, 'login_failed') AS summary_text,
                jsonb_build_object(
                    'identifier', le.identifier,
                    'failure_reason', le.failure_reason,
                    'ip_address', le.ip_address,
                    'auth_method', le.auth_method
                ) AS trace_json
            FROM audit.login_event AS le
            LEFT JOIN iam.user_account AS ua
              ON ua.id = le.user_account_id
            WHERE le.outcome = 'failure'
        ),
        role_change AS (
            SELECT
                ae.tenant_id,
                'audit.audit_event'::text AS source_table,
                ae.id AS source_id,
                ae.created_at AS occurred_at,
                'role_change'::text AS category_code,
                'high'::text AS severity_code,
                'success'::text AS result_status_code,
                ae.actor_user_id,
                actor.full_name AS actor_display_name,
                NULL::uuid AS branch_id,
                NULL::uuid AS mandate_id,
                ae.request_id,
                ae.entity_type,
                ae.entity_id::text AS entity_id,
                ae.event_type,
                'employee_user'::text AS role_key,
                'tenant'::text AS scope_type,
                ae.event_type AS summary_text,
                jsonb_build_object(
                    'before_json', ae.before_json,
                    'after_json', ae.after_json,
                    'metadata_json', ae.metadata_json
                ) AS trace_json
            FROM audit.audit_event AS ae
            LEFT JOIN iam.user_account AS actor
              ON actor.id = ae.actor_user_id
            WHERE ae.event_type IN (
                'employees.access.user_created_and_linked',
                'employees.access.user_attached',
                'employees.access.user_detached',
                'employees.access.user_reconciled'
            )
        ),
        watchbook_closure AS (
            SELECT
                ae.tenant_id,
                'audit.audit_event'::text AS source_table,
                ae.id AS source_id,
                ae.created_at AS occurred_at,
                'watchbook_closure'::text AS category_code,
                'medium'::text AS severity_code,
                'success'::text AS result_status_code,
                ae.actor_user_id,
                actor.full_name AS actor_display_name,
                NULL::uuid AS branch_id,
                NULL::uuid AS mandate_id,
                ae.request_id,
                ae.entity_type,
                ae.entity_id::text AS entity_id,
                ae.event_type,
                NULL::text AS role_key,
                NULL::text AS scope_type,
                'watchbook closed'::text AS summary_text,
                jsonb_build_object(
                    'before_json', ae.before_json,
                    'after_json', ae.after_json,
                    'metadata_json', ae.metadata_json
                ) AS trace_json
            FROM audit.audit_event AS ae
            LEFT JOIN iam.user_account AS actor
              ON actor.id = ae.actor_user_id
            WHERE ae.event_type = 'field.watchbook.closed'
        ),
        sensitive_edit AS (
            SELECT
                ae.tenant_id,
                'audit.audit_event'::text AS source_table,
                ae.id AS source_id,
                ae.created_at AS occurred_at,
                'sensitive_edit'::text AS category_code,
                CASE
                    WHEN ae.event_type LIKE 'finance.%' THEN 'critical'
                    WHEN ae.event_type LIKE 'employees.private_profile.%' THEN 'critical'
                    WHEN ae.event_type LIKE 'employees.address_history.%' THEN 'high'
                    WHEN ae.event_type LIKE 'customers.billing_profile.%' THEN 'high'
                    ELSE 'medium'
                END AS severity_code,
                'success'::text AS result_status_code,
                ae.actor_user_id,
                actor.full_name AS actor_display_name,
                CASE
                    WHEN ae.entity_type = 'hr.employee' THEN e.default_branch_id
                    ELSE NULL::uuid
                END AS branch_id,
                CASE
                    WHEN ae.entity_type = 'hr.employee' THEN e.default_mandate_id
                    ELSE NULL::uuid
                END AS mandate_id,
                ae.request_id,
                ae.entity_type,
                ae.entity_id::text AS entity_id,
                ae.event_type,
                NULL::text AS role_key,
                NULL::text AS scope_type,
                ae.event_type AS summary_text,
                jsonb_build_object(
                    'before_json', ae.before_json,
                    'after_json', ae.after_json,
                    'metadata_json', ae.metadata_json
                ) AS trace_json
            FROM audit.audit_event AS ae
            LEFT JOIN iam.user_account AS actor
              ON actor.id = ae.actor_user_id
            LEFT JOIN hr.employee AS e
              ON e.tenant_id = ae.tenant_id
             AND ae.entity_type = 'hr.employee'
             AND e.id::text = ae.entity_id
            WHERE (
                ae.event_type LIKE 'employees.private_profile.%'
                OR ae.event_type LIKE 'employees.address_history.%'
                OR ae.event_type LIKE 'finance.actual.%'
                OR ae.event_type LIKE 'finance.customer_invoice.%'
                OR ae.event_type LIKE 'customers.billing_profile.%'
                OR ae.event_type LIKE 'customers.invoice_party.%'
                OR ae.event_type LIKE 'subcontractors.company.%'
            )
              AND ae.event_type <> 'field.watchbook.closed'
        )
        SELECT * FROM login_failure
        UNION ALL
        SELECT * FROM role_change
        UNION ALL
        SELECT * FROM watchbook_closure
        UNION ALL
        SELECT * FROM sensitive_edit;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS rpt.security_activity_v")
