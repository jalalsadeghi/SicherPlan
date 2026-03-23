"""create reporting views for employee activity, customer revenue, and subcontractor control

Revision ID: 0052_reporting_views_operational_commercial
Revises: 0051_subcontractor_invoice_checks
Create Date: 2026-03-20 10:00:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "0052_reporting_views_operational_commercial"
down_revision = "0051_subcontractor_invoice_checks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS rpt")
    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.employee_activity_v AS
        WITH shift_stats AS (
            SELECT
                a.tenant_id,
                a.employee_id,
                date_trunc('month', s.starts_at)::date AS activity_month,
                COUNT(*) FILTER (WHERE a.assignment_status_code = 'confirmed') AS confirmed_shift_count,
                COUNT(*) FILTER (WHERE a.assignment_status_code <> 'confirmed' AND a.assignment_status_code <> 'removed') AS unconfirmed_shift_count,
                COUNT(ar.id) FILTER (WHERE ar.is_current = true AND ar.archived_at IS NULL) AS approved_actual_count,
                COALESCE(SUM(ar.payable_minutes) FILTER (WHERE ar.is_current = true AND ar.archived_at IS NULL), 0) AS payable_minutes_total
            FROM ops.assignment AS a
            JOIN ops.shift AS s
              ON s.tenant_id = a.tenant_id
             AND s.id = a.shift_id
            LEFT JOIN finance.actual_record AS ar
              ON ar.tenant_id = a.tenant_id
             AND ar.assignment_id = a.id
             AND ar.employee_id = a.employee_id
             AND ar.approval_stage_code = 'finance_signed_off'
            WHERE a.employee_id IS NOT NULL
              AND a.archived_at IS NULL
              AND s.archived_at IS NULL
            GROUP BY a.tenant_id, a.employee_id, date_trunc('month', s.starts_at)::date
        ),
        application_stats AS (
            SELECT
                tenant_id,
                employee_id,
                date_trunc('month', applied_at)::date AS activity_month,
                COUNT(*) AS application_count,
                COUNT(*) FILTER (WHERE status = 'pending') AS pending_application_count
            FROM hr.employee_event_application
            WHERE archived_at IS NULL
            GROUP BY tenant_id, employee_id, date_trunc('month', applied_at)::date
        ),
        absence_stats AS (
            SELECT
                tenant_id,
                employee_id,
                date_trunc('month', starts_on)::date AS activity_month,
                COALESCE(SUM(quantity_days) FILTER (WHERE status = 'approved'), 0) AS approved_absence_days,
                COALESCE(SUM(quantity_days) FILTER (WHERE status = 'pending'), 0) AS pending_absence_days
            FROM hr.employee_absence
            WHERE archived_at IS NULL
            GROUP BY tenant_id, employee_id, date_trunc('month', starts_on)::date
        ),
        login_stats AS (
            SELECT
                e.tenant_id,
                e.id AS employee_id,
                date_trunc('month', le.created_at)::date AS activity_month,
                COUNT(*) FILTER (WHERE le.outcome = 'success') AS login_count,
                MAX(le.created_at) FILTER (WHERE le.outcome = 'success') AS last_login_at
            FROM hr.employee AS e
            JOIN audit.login_event AS le
              ON le.tenant_id = e.tenant_id
             AND le.user_account_id = e.user_id
            WHERE e.archived_at IS NULL
            GROUP BY e.tenant_id, e.id, date_trunc('month', le.created_at)::date
        ),
        time_account_balance AS (
            SELECT
                ta.tenant_id,
                ta.employee_id,
                COALESCE(SUM(CASE WHEN ta.account_type = 'overtime' THEN txn.amount_minutes ELSE 0 END), 0) AS overtime_balance_minutes,
                COALESCE(SUM(CASE WHEN ta.account_type = 'work_time' THEN txn.amount_minutes ELSE 0 END), 0) AS work_time_balance_minutes
            FROM hr.employee_time_account AS ta
            LEFT JOIN hr.employee_time_account_txn AS txn
              ON txn.tenant_id = ta.tenant_id
             AND txn.time_account_id = ta.id
            WHERE ta.archived_at IS NULL
            GROUP BY ta.tenant_id, ta.employee_id
        ),
        months AS (
            SELECT tenant_id, employee_id, activity_month FROM shift_stats
            UNION
            SELECT tenant_id, employee_id, activity_month FROM application_stats
            UNION
            SELECT tenant_id, employee_id, activity_month FROM absence_stats
            UNION
            SELECT tenant_id, employee_id, activity_month FROM login_stats
        )
        SELECT
            e.tenant_id,
            e.id AS employee_id,
            e.personnel_no,
            TRIM(CONCAT(e.first_name, ' ', e.last_name)) AS display_name,
            months.activity_month,
            COALESCE(ss.confirmed_shift_count, 0) AS confirmed_shift_count,
            COALESCE(ss.unconfirmed_shift_count, 0) AS unconfirmed_shift_count,
            COALESCE(ss.approved_actual_count, 0) AS approved_actual_count,
            COALESCE(ss.payable_minutes_total, 0) AS payable_minutes_total,
            COALESCE(ls.login_count, 0) AS login_count,
            ls.last_login_at,
            COALESCE(app.application_count, 0) AS application_count,
            COALESCE(app.pending_application_count, 0) AS pending_application_count,
            COALESCE(abs.approved_absence_days, 0)::numeric(8,2) AS approved_absence_days,
            COALESCE(abs.pending_absence_days, 0)::numeric(8,2) AS pending_absence_days,
            COALESCE(tab.overtime_balance_minutes, 0) AS overtime_balance_minutes,
            COALESCE(tab.work_time_balance_minutes, 0) AS work_time_balance_minutes,
            e.hire_date,
            e.termination_date
        FROM months
        JOIN hr.employee AS e
          ON e.tenant_id = months.tenant_id
         AND e.id = months.employee_id
        LEFT JOIN shift_stats AS ss
          ON ss.tenant_id = months.tenant_id
         AND ss.employee_id = months.employee_id
         AND ss.activity_month = months.activity_month
        LEFT JOIN application_stats AS app
          ON app.tenant_id = months.tenant_id
         AND app.employee_id = months.employee_id
         AND app.activity_month = months.activity_month
        LEFT JOIN absence_stats AS abs
          ON abs.tenant_id = months.tenant_id
         AND abs.employee_id = months.employee_id
         AND abs.activity_month = months.activity_month
        LEFT JOIN login_stats AS ls
          ON ls.tenant_id = months.tenant_id
         AND ls.employee_id = months.employee_id
         AND ls.activity_month = months.activity_month
        LEFT JOIN time_account_balance AS tab
          ON tab.tenant_id = months.tenant_id
         AND tab.employee_id = months.employee_id
        WHERE e.archived_at IS NULL
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.customer_revenue_v AS
        SELECT
            inv.tenant_id,
            inv.customer_id,
            c.customer_number,
            c.name AS customer_name,
            ts.order_id,
            o.order_no,
            ts.planning_record_id,
            pr.name AS planning_record_name,
            pr.planning_mode_code,
            inv.id AS invoice_id,
            inv.invoice_no,
            inv.issue_date,
            inv.due_date,
            inv.invoice_status_code,
            inv.delivery_status_code,
            inv.period_start,
            inv.period_end,
            inv.released_at,
            inv.timesheet_id,
            ts.release_state_code AS timesheet_release_state_code,
            COUNT(DISTINCT til.actual_record_id) AS actual_record_count,
            COALESCE(SUM(til.billable_minutes), 0) AS billable_minutes_total,
            COALESCE(SUM(ar.payable_minutes), 0) AS payable_minutes_total,
            inv.subtotal_amount,
            inv.tax_amount,
            inv.total_amount,
            inv.source_document_id
        FROM finance.customer_invoice AS inv
        JOIN crm.customer AS c
          ON c.tenant_id = inv.tenant_id
         AND c.id = inv.customer_id
        LEFT JOIN finance.timesheet AS ts
          ON ts.tenant_id = inv.tenant_id
         AND ts.id = inv.timesheet_id
        LEFT JOIN ops.customer_order AS o
          ON o.tenant_id = ts.tenant_id
         AND o.id = ts.order_id
        LEFT JOIN ops.planning_record AS pr
          ON pr.tenant_id = ts.tenant_id
         AND pr.id = ts.planning_record_id
        LEFT JOIN finance.timesheet_line AS til
          ON til.tenant_id = ts.tenant_id
         AND til.timesheet_id = ts.id
        LEFT JOIN finance.actual_record AS ar
          ON ar.tenant_id = til.tenant_id
         AND ar.id = til.actual_record_id
         AND ar.is_current = true
         AND ar.archived_at IS NULL
        WHERE inv.archived_at IS NULL
        GROUP BY
            inv.tenant_id, inv.customer_id, c.customer_number, c.name, ts.order_id, o.order_no,
            ts.planning_record_id, pr.name, pr.planning_mode_code, inv.id, inv.invoice_no,
            inv.issue_date, inv.due_date, inv.invoice_status_code, inv.delivery_status_code,
            inv.period_start, inv.period_end, inv.released_at, inv.timesheet_id, ts.release_state_code,
            inv.subtotal_amount, inv.tax_amount, inv.total_amount, inv.source_document_id
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.subcontractor_control_v AS
        WITH worker_compliance AS (
            SELECT
                w.tenant_id,
                w.subcontractor_id,
                w.id AS subcontractor_worker_id,
                CASE
                    WHEN COUNT(q.id) FILTER (WHERE q.archived_at IS NULL AND q.status = 'active' AND (q.valid_until IS NULL OR q.valid_until >= CURRENT_DATE)) > 0
                    THEN 1 ELSE 0
                END AS compliance_complete
            FROM partner.subcontractor_worker AS w
            LEFT JOIN partner.subcontractor_worker_qualification AS q
              ON q.tenant_id = w.tenant_id
             AND q.worker_id = w.id
            WHERE w.archived_at IS NULL
            GROUP BY w.tenant_id, w.subcontractor_id, w.id
        )
        SELECT
            ic.tenant_id,
            ic.subcontractor_id,
            s.subcontractor_number,
            COALESCE(s.display_name, s.legal_name) AS subcontractor_name,
            ic.id AS invoice_check_id,
            ic.check_no,
            ic.period_start,
            ic.period_end,
            ic.status_code,
            COUNT(DISTINCT icl.shift_id) FILTER (WHERE sh.released_at IS NOT NULL) AS released_shift_count,
            COUNT(DISTINCT icl.shift_id) AS assigned_shift_count,
            ic.actual_minutes_total,
            ic.approved_minutes_total,
            COUNT(icl.id) FILTER (WHERE icl.actual_quantity > 0) AS attendance_marker_count,
            COUNT(icl.id) FILTER (WHERE icl.comparison_state_code = 'warning') AS variance_warning_count,
            COUNT(icl.id) FILTER (WHERE icl.comparison_state_code = 'needs_review') AS variance_review_count,
            ic.expected_amount_total,
            ic.approved_amount_total,
            ic.comparison_variance_amount,
            COUNT(DISTINCT icl.subcontractor_worker_id) FILTER (WHERE wc.compliance_complete = 1) AS compliance_complete_worker_count,
            COUNT(DISTINCT icl.subcontractor_worker_id) FILTER (WHERE COALESCE(wc.compliance_complete, 0) = 0) AS compliance_gap_worker_count,
            ic.released_at,
            ic.approved_at
        FROM finance.subcontractor_invoice_check AS ic
        JOIN partner.subcontractor AS s
          ON s.tenant_id = ic.tenant_id
         AND s.id = ic.subcontractor_id
        LEFT JOIN finance.subcontractor_invoice_check_line AS icl
          ON icl.tenant_id = ic.tenant_id
         AND icl.invoice_check_id = ic.id
        LEFT JOIN ops.shift AS sh
          ON sh.tenant_id = icl.tenant_id
         AND sh.id = icl.shift_id
        LEFT JOIN worker_compliance AS wc
          ON wc.tenant_id = icl.tenant_id
         AND wc.subcontractor_id = ic.subcontractor_id
         AND wc.subcontractor_worker_id = icl.subcontractor_worker_id
        WHERE ic.archived_at IS NULL
        GROUP BY
            ic.tenant_id, ic.subcontractor_id, s.subcontractor_number, COALESCE(s.display_name, s.legal_name),
            ic.id, ic.check_no, ic.period_start, ic.period_end, ic.status_code,
            ic.actual_minutes_total, ic.approved_minutes_total, ic.expected_amount_total,
            ic.approved_amount_total, ic.comparison_variance_amount, ic.released_at, ic.approved_at
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS rpt.subcontractor_control_v")
    op.execute("DROP VIEW IF EXISTS rpt.customer_revenue_v")
    op.execute("DROP VIEW IF EXISTS rpt.employee_activity_v")
