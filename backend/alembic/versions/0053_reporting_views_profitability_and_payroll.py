"""create reporting views for planning performance, payroll basis, and profitability

Revision ID: 0053_reporting_views_profitability_and_payroll
Revises: 0052_reporting_views_operational_commercial
Create Date: 2026-03-20 10:30:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "0053_reporting_views_profitability_and_payroll"
down_revision = "0052_reporting_views_operational_commercial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS rpt")
    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.planning_performance_v AS
        WITH demand_totals AS (
            SELECT
                dg.tenant_id,
                dg.shift_id,
                COALESCE(SUM(dg.target_qty), 0) AS target_qty_total,
                COALESCE(SUM(dg.min_qty), 0) AS min_qty_total
            FROM ops.demand_group AS dg
            WHERE dg.archived_at IS NULL
            GROUP BY dg.tenant_id, dg.shift_id
        ),
        assignment_totals AS (
            SELECT
                a.tenant_id,
                a.shift_id,
                COUNT(*) FILTER (WHERE a.assignment_status_code <> 'removed') AS assigned_qty_total,
                COUNT(*) FILTER (WHERE a.assignment_status_code = 'confirmed') AS confirmed_assignment_count
            FROM ops.assignment AS a
            WHERE a.archived_at IS NULL
            GROUP BY a.tenant_id, a.shift_id
        ),
        actual_totals AS (
            SELECT
                ar.tenant_id,
                ar.shift_id,
                COUNT(*) FILTER (WHERE ar.is_current = true AND ar.archived_at IS NULL) AS approved_actual_count,
                COALESCE(SUM(ar.billable_minutes) FILTER (WHERE ar.is_current = true AND ar.archived_at IS NULL), 0) AS billable_minutes_total,
                COALESCE(SUM(ar.payable_minutes) FILTER (WHERE ar.is_current = true AND ar.archived_at IS NULL), 0) AS payable_minutes_total
            FROM finance.actual_record AS ar
            WHERE ar.approval_stage_code = 'finance_signed_off'
            GROUP BY ar.tenant_id, ar.shift_id
        )
        SELECT
            sh.tenant_id,
            sh.id AS shift_id,
            sh.shift_plan_id,
            sp.planning_record_id,
            pr.order_id,
            o.customer_id,
            c.customer_number,
            c.name AS customer_name,
            o.order_no,
            pr.name AS planning_record_name,
            pr.planning_mode_code,
            sh.starts_at::date AS shift_date,
            sh.starts_at,
            sh.ends_at,
            sh.release_state,
            COALESCE(dt.target_qty_total, 0) AS target_qty_total,
            COALESCE(dt.min_qty_total, 0) AS min_qty_total,
            COALESCE(at.assigned_qty_total, 0) AS assigned_qty_total,
            COALESCE(at.confirmed_assignment_count, 0) AS confirmed_assignment_count,
            COALESCE(act.approved_actual_count, 0) AS approved_actual_count,
            COALESCE(act.billable_minutes_total, 0) AS billable_minutes_total,
            COALESCE(act.payable_minutes_total, 0) AS payable_minutes_total,
            GREATEST(COALESCE(dt.target_qty_total, 0) - COALESCE(at.assigned_qty_total, 0), 0) AS coverage_gap_qty,
            CASE
                WHEN COALESCE(dt.target_qty_total, 0) = 0 THEN 1.0::numeric(10,4)
                ELSE ROUND(COALESCE(at.assigned_qty_total, 0)::numeric / NULLIF(dt.target_qty_total, 0)::numeric, 4)
            END AS fill_rate_ratio
        FROM ops.shift AS sh
        JOIN ops.shift_plan AS sp
          ON sp.tenant_id = sh.tenant_id
         AND sp.id = sh.shift_plan_id
        JOIN ops.planning_record AS pr
          ON pr.tenant_id = sp.tenant_id
         AND pr.id = sp.planning_record_id
        JOIN ops.customer_order AS o
          ON o.tenant_id = pr.tenant_id
         AND o.id = pr.order_id
        JOIN crm.customer AS c
          ON c.tenant_id = o.tenant_id
         AND c.id = o.customer_id
        LEFT JOIN demand_totals AS dt
          ON dt.tenant_id = sh.tenant_id
         AND dt.shift_id = sh.id
        LEFT JOIN assignment_totals AS at
          ON at.tenant_id = sh.tenant_id
         AND at.shift_id = sh.id
        LEFT JOIN actual_totals AS act
          ON act.tenant_id = sh.tenant_id
         AND act.shift_id = sh.id
        WHERE sh.archived_at IS NULL
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.payroll_basis_v AS
        WITH allowance_totals AS (
            SELECT
                ar.tenant_id,
                ar.id AS actual_record_id,
                COALESCE(SUM(aa.amount), 0)::numeric(12,2) AS allowance_amount_total
            FROM finance.actual_record AS ar
            LEFT JOIN hr.employee_allowance AS aa
              ON aa.tenant_id = ar.tenant_id
             AND aa.employee_id = ar.employee_id
             AND ar.planned_start_at::date >= aa.effective_from
             AND (aa.effective_until IS NULL OR ar.planned_start_at::date <= aa.effective_until)
             AND aa.archived_at IS NULL
            WHERE ar.employee_id IS NOT NULL
            GROUP BY ar.tenant_id, ar.id
        ),
        advance_totals AS (
            SELECT
                ar.tenant_id,
                ar.id AS actual_record_id,
                COALESCE(SUM(ad.outstanding_amount), 0)::numeric(12,2) AS advance_outstanding_total
            FROM finance.actual_record AS ar
            LEFT JOIN hr.employee_advance AS ad
              ON ad.tenant_id = ar.tenant_id
             AND ad.employee_id = ar.employee_id
             AND ad.status IN ('approved', 'disbursed', 'settled')
             AND ad.archived_at IS NULL
            WHERE ar.employee_id IS NOT NULL
            GROUP BY ar.tenant_id, ar.id
        ),
        export_state AS (
            SELECT
                pei.tenant_id,
                pei.actual_record_id,
                MAX(peb.batch_status_code) AS export_state_code,
                MAX(peb.batch_no) AS export_batch_no,
                MAX(peb.generated_at) AS export_generated_at
            FROM finance.payroll_export_item AS pei
            JOIN finance.payroll_export_batch AS peb
              ON peb.tenant_id = pei.tenant_id
             AND peb.id = pei.batch_id
            GROUP BY pei.tenant_id, pei.actual_record_id
        ),
        active_payslip AS (
            SELECT
                ppa.tenant_id,
                ppa.employee_id,
                MAX(ppa.archive_status_code) AS payslip_archive_status_code
            FROM finance.payroll_payslip_archive AS ppa
            WHERE ppa.archive_status_code = 'active'
              AND ppa.archived_at IS NULL
            GROUP BY ppa.tenant_id, ppa.employee_id
        ),
        effective_profile AS (
            SELECT
                ar.tenant_id,
                ar.id AS actual_record_id,
                pp.payroll_region_code,
                pp.employment_type_code,
                pp.pay_cycle_code,
                COALESCE(pp.base_rate_override, tr.base_amount, 0)::numeric(12,2) AS base_rate_resolved
            FROM finance.actual_record AS ar
            JOIN hr.employee AS e
              ON e.tenant_id = ar.tenant_id
             AND e.id = ar.employee_id
            LEFT JOIN LATERAL (
                SELECT *
                FROM finance.employee_pay_profile AS pp
                WHERE pp.tenant_id = ar.tenant_id
                  AND pp.employee_id = ar.employee_id
                  AND pp.archived_at IS NULL
                  AND pp.effective_from <= ar.planned_start_at::date
                  AND (pp.effective_until IS NULL OR pp.effective_until >= ar.planned_start_at::date)
                ORDER BY pp.effective_from DESC
                LIMIT 1
            ) AS pp ON TRUE
            LEFT JOIN LATERAL (
                SELECT tr.base_amount
                FROM finance.payroll_tariff_rate AS tr
                WHERE pp.tariff_table_id IS NOT NULL
                  AND tr.tenant_id = pp.tenant_id
                  AND tr.tariff_table_id = pp.tariff_table_id
                  AND (tr.function_type_id IS NULL OR tr.function_type_id = (
                        SELECT dg.function_type_id FROM ops.assignment AS a
                        JOIN ops.demand_group AS dg ON dg.tenant_id = a.tenant_id AND dg.id = a.demand_group_id
                        WHERE a.tenant_id = ar.tenant_id AND a.id = ar.assignment_id
                  ))
                ORDER BY tr.function_type_id NULLS LAST, tr.qualification_type_id NULLS LAST
                LIMIT 1
            ) AS tr ON TRUE
        )
        SELECT
            ar.tenant_id,
            ar.id AS actual_record_id,
            ar.employee_id,
            e.personnel_no,
            TRIM(CONCAT(e.first_name, ' ', e.last_name)) AS display_name,
            ar.shift_id,
            ar.planned_start_at::date AS service_date,
            ep.payroll_region_code,
            ep.employment_type_code,
            ep.pay_cycle_code,
            COALESCE(es.export_state_code, 'not_exported') AS export_state_code,
            ar.approval_stage_code,
            ar.payable_minutes,
            ar.billable_minutes,
            COALESCE(ep.base_rate_resolved, 0)::numeric(12,2) AS base_rate_resolved,
            COALESCE(at.allowance_amount_total, 0)::numeric(12,2) AS allowance_amount_total,
            COALESCE(ad.advance_outstanding_total, 0)::numeric(12,2) AS advance_outstanding_total,
            ROUND(((COALESCE(ep.base_rate_resolved, 0)::numeric * ar.payable_minutes::numeric) / 60.0) + COALESCE(at.allowance_amount_total, 0)::numeric, 2) AS payroll_cost_basis_amount,
            es.export_batch_no,
            es.export_generated_at,
            ap.payslip_archive_status_code
        FROM finance.actual_record AS ar
        JOIN hr.employee AS e
          ON e.tenant_id = ar.tenant_id
         AND e.id = ar.employee_id
        LEFT JOIN effective_profile AS ep
          ON ep.tenant_id = ar.tenant_id
         AND ep.actual_record_id = ar.id
        LEFT JOIN allowance_totals AS at
          ON at.tenant_id = ar.tenant_id
         AND at.actual_record_id = ar.id
        LEFT JOIN advance_totals AS ad
          ON ad.tenant_id = ar.tenant_id
         AND ad.actual_record_id = ar.id
        LEFT JOIN export_state AS es
          ON es.tenant_id = ar.tenant_id
         AND es.actual_record_id = ar.id
        LEFT JOIN active_payslip AS ap
          ON ap.tenant_id = ar.tenant_id
         AND ap.employee_id = ar.employee_id
        WHERE ar.employee_id IS NOT NULL
          AND ar.is_current = true
          AND ar.archived_at IS NULL
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.customer_profitability_v AS
        WITH payroll_cost AS (
            SELECT
                pb.tenant_id,
                pb.actual_record_id,
                pb.payroll_cost_basis_amount,
                pb.allowance_amount_total
            FROM rpt.payroll_basis_v AS pb
        ),
        expense_totals AS (
            SELECT
                tenant_id,
                actual_record_id,
                COALESCE(SUM(amount_total), 0)::numeric(12,2) AS expense_cost_amount
            FROM finance.actual_expense
            WHERE archived_at IS NULL
            GROUP BY tenant_id, actual_record_id
        )
        SELECT
            inv.tenant_id,
            inv.customer_id,
            c.customer_number,
            c.name AS customer_name,
            ts.order_id,
            o.order_no,
            ts.planning_record_id,
            pr.name AS planning_record_name,
            date_trunc('month', inv.issue_date)::date AS service_month,
            COUNT(DISTINCT inv.id) AS invoice_count,
            COALESCE(SUM(il.net_amount), 0)::numeric(12,2) AS revenue_net_amount,
            COALESCE(SUM(pc.payroll_cost_basis_amount), 0)::numeric(12,2) AS payroll_cost_basis_amount,
            COALESCE(SUM(pc.allowance_amount_total), 0)::numeric(12,2) AS allowance_cost_amount,
            COALESCE(SUM(et.expense_cost_amount), 0)::numeric(12,2) AS expense_cost_amount,
            (COALESCE(SUM(il.net_amount), 0)::numeric(12,2) - COALESCE(SUM(pc.payroll_cost_basis_amount), 0)::numeric(12,2) - COALESCE(SUM(et.expense_cost_amount), 0)::numeric(12,2))::numeric(12,2) AS contribution_margin_amount,
            CASE
                WHEN COALESCE(SUM(il.net_amount), 0) = 0 THEN 0::numeric(10,4)
                ELSE ROUND(
                    (
                        COALESCE(SUM(il.net_amount), 0)::numeric
                        - COALESCE(SUM(pc.payroll_cost_basis_amount), 0)::numeric
                        - COALESCE(SUM(et.expense_cost_amount), 0)::numeric
                    ) / NULLIF(COALESCE(SUM(il.net_amount), 0)::numeric, 0),
                    4
                )
            END AS contribution_margin_ratio
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
        LEFT JOIN finance.customer_invoice_line AS il
          ON il.tenant_id = inv.tenant_id
         AND il.invoice_id = inv.id
        LEFT JOIN payroll_cost AS pc
          ON pc.tenant_id = il.tenant_id
         AND pc.actual_record_id = il.source_actual_id
        LEFT JOIN expense_totals AS et
          ON et.tenant_id = il.tenant_id
         AND et.actual_record_id = il.source_actual_id
        WHERE inv.archived_at IS NULL
        GROUP BY
            inv.tenant_id, inv.customer_id, c.customer_number, c.name, ts.order_id, o.order_no,
            ts.planning_record_id, pr.name, date_trunc('month', inv.issue_date)::date
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS rpt.customer_profitability_v")
    op.execute("DROP VIEW IF EXISTS rpt.payroll_basis_v")
    op.execute("DROP VIEW IF EXISTS rpt.planning_performance_v")
