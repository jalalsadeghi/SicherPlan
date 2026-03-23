"""US-32-T1/T2 compliance and QM reporting views."""

from __future__ import annotations

from alembic import op


revision = "0054_reporting_views_compliance_and_qm"
down_revision = "0053_reporting_views_profitability_and_payroll"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS rpt")

    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.compliance_status_v AS
        WITH employee_proof AS (
            SELECT
                l.tenant_id,
                l.owner_id AS qualification_id,
                COUNT(DISTINCT d.id)::int AS proof_document_count,
                MIN(dt.key) AS document_type_key
            FROM docs.document_link AS l
            JOIN docs.document AS d
              ON d.tenant_id = l.tenant_id
             AND d.id = l.document_id
             AND d.archived_at IS NULL
            LEFT JOIN docs.document_type AS dt
              ON dt.id = d.document_type_id
            WHERE l.owner_type = 'hr.employee_qualification'
            GROUP BY l.tenant_id, l.owner_id
        ),
        worker_proof AS (
            SELECT
                l.tenant_id,
                l.owner_id AS qualification_id,
                COUNT(DISTINCT d.id)::int AS proof_document_count,
                MIN(dt.key) AS document_type_key
            FROM docs.document_link AS l
            JOIN docs.document AS d
              ON d.tenant_id = l.tenant_id
             AND d.id = l.document_id
             AND d.archived_at IS NULL
            LEFT JOIN docs.document_type AS dt
              ON dt.id = d.document_type_id
            WHERE l.owner_type = 'partner.subcontractor_worker_qualification'
            GROUP BY l.tenant_id, l.owner_id
        ),
        active_worker_scope AS (
            SELECT
                sw.tenant_id,
                sw.id AS subcontractor_worker_id,
                sw.subcontractor_id,
                ss.branch_id,
                ss.mandate_id
            FROM partner.subcontractor_worker AS sw
            LEFT JOIN partner.subcontractor_scope AS ss
              ON ss.tenant_id = sw.tenant_id
             AND ss.subcontractor_id = sw.subcontractor_id
             AND ss.archived_at IS NULL
             AND ss.status = 'active'
             AND ss.valid_from <= CURRENT_DATE
             AND (ss.valid_to IS NULL OR ss.valid_to >= CURRENT_DATE)
            WHERE sw.archived_at IS NULL
              AND sw.status = 'active'
        ),
        employee_expiry AS (
            SELECT
                eq.tenant_id,
                'employee'::text AS actor_type_code,
                e.id AS actor_id,
                e.personnel_no AS actor_number,
                TRIM(CONCAT(e.first_name, ' ', e.last_name)) AS actor_display_name,
                e.id AS employee_id,
                NULL::uuid AS subcontractor_id,
                NULL::uuid AS subcontractor_worker_id,
                e.default_branch_id AS branch_id,
                e.default_mandate_id AS mandate_id,
                'hr.employee_qualification'::text AS source_entity_type,
                eq.id AS source_entity_id,
                'qualification_expiry'::text AS rule_family_code,
                qt.code AS rule_code,
                qt.label AS rule_label,
                ep.document_type_key,
                CASE
                    WHEN eq.valid_until IS NULL THEN 'missing_expiry'
                    WHEN eq.valid_until < CURRENT_DATE THEN 'expired'
                    WHEN eq.valid_until <= CURRENT_DATE + 30 THEN 'expiring'
                    ELSE 'valid'
                END AS status_code,
                CASE
                    WHEN eq.valid_until IS NULL OR eq.valid_until < CURRENT_DATE THEN 'critical'
                    WHEN eq.valid_until <= CURRENT_DATE + 30 THEN 'warning'
                    ELSE 'info'
                END AS severity_code,
                (qt.compliance_relevant OR qt.planning_relevant)::boolean AS release_relevant_flag,
                eq.valid_until,
                CASE
                    WHEN eq.valid_until IS NULL THEN NULL
                    ELSE (eq.valid_until - CURRENT_DATE)::int
                END AS days_until_expiry,
                COALESCE(ep.proof_document_count, 0) AS proof_document_count
            FROM hr.employee_qualification AS eq
            JOIN hr.employee AS e
              ON e.tenant_id = eq.tenant_id
             AND e.id = eq.employee_id
            JOIN hr.qualification_type AS qt
              ON qt.tenant_id = eq.tenant_id
             AND qt.id = eq.qualification_type_id
            LEFT JOIN employee_proof AS ep
              ON ep.tenant_id = eq.tenant_id
             AND ep.qualification_id = eq.id::text
            WHERE eq.archived_at IS NULL
              AND eq.status = 'active'
              AND e.archived_at IS NULL
              AND e.status = 'active'
              AND eq.record_kind = 'qualification'
              AND qt.expiry_required = true
        ),
        employee_document AS (
            SELECT
                eq.tenant_id,
                'employee'::text AS actor_type_code,
                e.id AS actor_id,
                e.personnel_no AS actor_number,
                TRIM(CONCAT(e.first_name, ' ', e.last_name)) AS actor_display_name,
                e.id AS employee_id,
                NULL::uuid AS subcontractor_id,
                NULL::uuid AS subcontractor_worker_id,
                e.default_branch_id AS branch_id,
                e.default_mandate_id AS mandate_id,
                'hr.employee_qualification'::text AS source_entity_type,
                eq.id AS source_entity_id,
                'mandatory_document'::text AS rule_family_code,
                qt.code AS rule_code,
                qt.label AS rule_label,
                ep.document_type_key,
                CASE
                    WHEN COALESCE(ep.proof_document_count, 0) = 0 THEN 'missing_document'
                    ELSE 'document_present'
                END AS status_code,
                CASE
                    WHEN COALESCE(ep.proof_document_count, 0) = 0 THEN 'critical'
                    ELSE 'info'
                END AS severity_code,
                (qt.compliance_relevant OR qt.planning_relevant)::boolean AS release_relevant_flag,
                eq.valid_until,
                CASE
                    WHEN eq.valid_until IS NULL THEN NULL
                    ELSE (eq.valid_until - CURRENT_DATE)::int
                END AS days_until_expiry,
                COALESCE(ep.proof_document_count, 0) AS proof_document_count
            FROM hr.employee_qualification AS eq
            JOIN hr.employee AS e
              ON e.tenant_id = eq.tenant_id
             AND e.id = eq.employee_id
            JOIN hr.qualification_type AS qt
              ON qt.tenant_id = eq.tenant_id
             AND qt.id = eq.qualification_type_id
            LEFT JOIN employee_proof AS ep
              ON ep.tenant_id = eq.tenant_id
             AND ep.qualification_id = eq.id::text
            WHERE eq.archived_at IS NULL
              AND eq.status = 'active'
              AND e.archived_at IS NULL
              AND e.status = 'active'
              AND eq.record_kind = 'qualification'
              AND qt.proof_required = true
        ),
        worker_expiry AS (
            SELECT
                wq.tenant_id,
                'subcontractor_worker'::text AS actor_type_code,
                sw.id AS actor_id,
                sw.worker_no AS actor_number,
                TRIM(CONCAT(sw.first_name, ' ', sw.last_name)) AS actor_display_name,
                NULL::uuid AS employee_id,
                aws.subcontractor_id,
                sw.id AS subcontractor_worker_id,
                aws.branch_id,
                aws.mandate_id,
                'partner.subcontractor_worker_qualification'::text AS source_entity_type,
                wq.id AS source_entity_id,
                'qualification_expiry'::text AS rule_family_code,
                qt.code AS rule_code,
                qt.label AS rule_label,
                wp.document_type_key,
                CASE
                    WHEN wq.valid_until IS NULL THEN 'missing_expiry'
                    WHEN wq.valid_until < CURRENT_DATE THEN 'expired'
                    WHEN wq.valid_until <= CURRENT_DATE + 30 THEN 'expiring'
                    ELSE 'valid'
                END AS status_code,
                CASE
                    WHEN wq.valid_until IS NULL OR wq.valid_until < CURRENT_DATE THEN 'critical'
                    WHEN wq.valid_until <= CURRENT_DATE + 30 THEN 'warning'
                    ELSE 'info'
                END AS severity_code,
                (qt.compliance_relevant OR qt.planning_relevant)::boolean AS release_relevant_flag,
                wq.valid_until,
                CASE
                    WHEN wq.valid_until IS NULL THEN NULL
                    ELSE (wq.valid_until - CURRENT_DATE)::int
                END AS days_until_expiry,
                COALESCE(wp.proof_document_count, 0) AS proof_document_count
            FROM partner.subcontractor_worker_qualification AS wq
            JOIN partner.subcontractor_worker AS sw
              ON sw.tenant_id = wq.tenant_id
             AND sw.id = wq.worker_id
            JOIN hr.qualification_type AS qt
              ON qt.tenant_id = wq.tenant_id
             AND qt.id = wq.qualification_type_id
            LEFT JOIN worker_proof AS wp
              ON wp.tenant_id = wq.tenant_id
             AND wp.qualification_id = wq.id::text
            LEFT JOIN active_worker_scope AS aws
              ON aws.tenant_id = sw.tenant_id
             AND aws.subcontractor_worker_id = sw.id
            WHERE wq.archived_at IS NULL
              AND wq.status = 'active'
              AND sw.archived_at IS NULL
              AND sw.status = 'active'
              AND qt.expiry_required = true
        ),
        worker_document AS (
            SELECT
                wq.tenant_id,
                'subcontractor_worker'::text AS actor_type_code,
                sw.id AS actor_id,
                sw.worker_no AS actor_number,
                TRIM(CONCAT(sw.first_name, ' ', sw.last_name)) AS actor_display_name,
                NULL::uuid AS employee_id,
                aws.subcontractor_id,
                sw.id AS subcontractor_worker_id,
                aws.branch_id,
                aws.mandate_id,
                'partner.subcontractor_worker_qualification'::text AS source_entity_type,
                wq.id AS source_entity_id,
                'mandatory_document'::text AS rule_family_code,
                qt.code AS rule_code,
                qt.label AS rule_label,
                wp.document_type_key,
                CASE
                    WHEN COALESCE(wp.proof_document_count, 0) = 0 THEN 'missing_document'
                    ELSE 'document_present'
                END AS status_code,
                CASE
                    WHEN COALESCE(wp.proof_document_count, 0) = 0 THEN 'critical'
                    ELSE 'info'
                END AS severity_code,
                (qt.compliance_relevant OR qt.planning_relevant)::boolean AS release_relevant_flag,
                wq.valid_until,
                CASE
                    WHEN wq.valid_until IS NULL THEN NULL
                    ELSE (wq.valid_until - CURRENT_DATE)::int
                END AS days_until_expiry,
                COALESCE(wp.proof_document_count, 0) AS proof_document_count
            FROM partner.subcontractor_worker_qualification AS wq
            JOIN partner.subcontractor_worker AS sw
              ON sw.tenant_id = wq.tenant_id
             AND sw.id = wq.worker_id
            JOIN hr.qualification_type AS qt
              ON qt.tenant_id = wq.tenant_id
             AND qt.id = wq.qualification_type_id
            LEFT JOIN worker_proof AS wp
              ON wp.tenant_id = wq.tenant_id
             AND wp.qualification_id = wq.id::text
            LEFT JOIN active_worker_scope AS aws
              ON aws.tenant_id = sw.tenant_id
             AND aws.subcontractor_worker_id = sw.id
            WHERE wq.archived_at IS NULL
              AND wq.status = 'active'
              AND sw.archived_at IS NULL
              AND sw.status = 'active'
              AND qt.proof_required = true
        )
        SELECT * FROM employee_expiry
        UNION ALL
        SELECT * FROM employee_document
        UNION ALL
        SELECT * FROM worker_expiry
        UNION ALL
        SELECT * FROM worker_document;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.notice_read_stats_v AS
        WITH active_users AS (
            SELECT ua.tenant_id, ua.id AS user_account_id
            FROM iam.user_account AS ua
            WHERE ua.archived_at IS NULL
              AND ua.status = 'active'
        ),
        audience_users AS (
            SELECT DISTINCT na.tenant_id, na.notice_id, au.user_account_id
            FROM info.notice_audience AS na
            JOIN iam.user_role_assignment AS ura
              ON ura.tenant_id = na.tenant_id
             AND ura.archived_at IS NULL
             AND ura.status = 'active'
            JOIN iam.role AS r
              ON r.id = ura.role_id
             AND r.archived_at IS NULL
             AND r.status = 'active'
            JOIN active_users AS au
              ON au.tenant_id = ura.tenant_id
             AND au.user_account_id = ura.user_account_id
            WHERE na.archived_at IS NULL
              AND na.status = 'active'
              AND na.audience_kind = 'role'
              AND r.key = na.target_value

            UNION

            SELECT DISTINCT na.tenant_id, na.notice_id, e.user_id
            FROM info.notice_audience AS na
            JOIN hr.employee AS e
              ON e.tenant_id = na.tenant_id
             AND e.archived_at IS NULL
             AND e.status = 'active'
             AND e.user_id IS NOT NULL
            WHERE na.archived_at IS NULL
              AND na.status = 'active'
              AND na.audience_kind = 'all_employees'

            UNION

            SELECT DISTINCT na.tenant_id, na.notice_id, cc.user_id
            FROM info.notice_audience AS na
            JOIN crm.customer_contact AS cc
              ON cc.tenant_id = na.tenant_id
             AND cc.archived_at IS NULL
             AND cc.status = 'active'
             AND cc.user_id IS NOT NULL
            WHERE na.archived_at IS NULL
              AND na.status = 'active'
              AND na.audience_kind = 'all_customers'

            UNION

            SELECT DISTINCT na.tenant_id, na.notice_id, sc.user_id
            FROM info.notice_audience AS na
            JOIN partner.subcontractor_contact AS sc
              ON sc.tenant_id = na.tenant_id
             AND sc.archived_at IS NULL
             AND sc.status = 'active'
             AND sc.user_id IS NOT NULL
             AND sc.portal_enabled = true
            WHERE na.archived_at IS NULL
              AND na.status = 'active'
              AND na.audience_kind = 'all_subcontractors'

            UNION

            SELECT DISTINCT na.tenant_id, na.notice_id, e.user_id
            FROM info.notice_audience AS na
            JOIN hr.employee_group AS eg
              ON eg.tenant_id = na.tenant_id
             AND eg.archived_at IS NULL
             AND eg.status = 'active'
             AND eg.code = na.target_value
            JOIN hr.employee_group_member AS gm
              ON gm.tenant_id = eg.tenant_id
             AND gm.group_id = eg.id
             AND gm.archived_at IS NULL
             AND gm.status = 'active'
            JOIN hr.employee AS e
              ON e.tenant_id = gm.tenant_id
             AND e.id = gm.employee_id
             AND e.archived_at IS NULL
             AND e.status = 'active'
             AND e.user_id IS NOT NULL
            WHERE na.archived_at IS NULL
              AND na.status = 'active'
              AND na.audience_kind = 'employee_group'

            UNION

            SELECT DISTINCT na.tenant_id, na.notice_id, e.user_id
            FROM info.notice_audience AS na
            JOIN hr.employee_qualification AS eq
              ON eq.tenant_id = na.tenant_id
             AND eq.archived_at IS NULL
             AND eq.status = 'active'
             AND eq.record_kind = 'qualification'
            JOIN hr.qualification_type AS qt
              ON qt.tenant_id = eq.tenant_id
             AND qt.id = eq.qualification_type_id
             AND qt.code = na.target_value
            JOIN hr.employee AS e
              ON e.tenant_id = eq.tenant_id
             AND e.id = eq.employee_id
             AND e.archived_at IS NULL
             AND e.status = 'active'
             AND e.user_id IS NOT NULL
            WHERE na.archived_at IS NULL
              AND na.status = 'active'
              AND na.audience_kind = 'qualification'
              AND (eq.valid_until IS NULL OR eq.valid_until >= CURRENT_DATE)

            UNION

            SELECT DISTINCT na.tenant_id, na.notice_id, e.user_id
            FROM info.notice_audience AS na
            JOIN hr.employee_qualification AS eq
              ON eq.tenant_id = na.tenant_id
             AND eq.archived_at IS NULL
             AND eq.status = 'active'
             AND eq.record_kind = 'function'
            JOIN hr.function_type AS ft
              ON ft.tenant_id = eq.tenant_id
             AND ft.id = eq.function_type_id
             AND ft.code = na.target_value
            JOIN hr.employee AS e
              ON e.tenant_id = eq.tenant_id
             AND e.id = eq.employee_id
             AND e.archived_at IS NULL
             AND e.status = 'active'
             AND e.user_id IS NOT NULL
            WHERE na.archived_at IS NULL
              AND na.status = 'active'
              AND na.audience_kind = 'function'
        ),
        audience_totals AS (
            SELECT tenant_id, notice_id, COUNT(DISTINCT user_account_id)::int AS audience_count
            FROM audience_users
            GROUP BY tenant_id, notice_id
        ),
        read_totals AS (
            SELECT
                nr.tenant_id,
                nr.notice_id,
                COUNT(DISTINCT nr.user_account_id)::int AS opened_count,
                COUNT(DISTINCT CASE WHEN nr.acknowledged_at IS NOT NULL THEN nr.user_account_id END)::int AS acknowledged_count,
                MAX(nr.last_opened_at) AS last_opened_at,
                MAX(nr.acknowledged_at) AS last_acknowledged_at
            FROM info.notice_read AS nr
            GROUP BY nr.tenant_id, nr.notice_id
        )
        SELECT
            n.tenant_id,
            n.id AS notice_id,
            n.title,
            n.language_code,
            n.mandatory_acknowledgement,
            n.published_at,
            n.publish_until,
            COALESCE(audience_totals.audience_count, 0) AS audience_count,
            COALESCE(read_totals.opened_count, 0) AS opened_count,
            COALESCE(read_totals.acknowledged_count, 0) AS acknowledged_count,
            GREATEST(COALESCE(audience_totals.audience_count, 0) - COALESCE(read_totals.opened_count, 0), 0) AS unread_count,
            CASE
                WHEN n.mandatory_acknowledgement = true AND n.publish_until IS NOT NULL AND n.publish_until < CURRENT_TIMESTAMP
                THEN GREATEST(COALESCE(audience_totals.audience_count, 0) - COALESCE(read_totals.acknowledged_count, 0), 0)
                ELSE 0
            END AS overdue_unread_count,
            CASE
                WHEN COALESCE(audience_totals.audience_count, 0) = 0 THEN 0::numeric(10,4)
                ELSE ROUND(COALESCE(read_totals.opened_count, 0)::numeric / audience_totals.audience_count::numeric, 4)
            END AS completion_ratio,
            read_totals.last_opened_at,
            read_totals.last_acknowledged_at,
            CASE
                WHEN COALESCE(audience_totals.audience_count, 0) = 0 THEN 'no_audience'
                WHEN n.mandatory_acknowledgement = true AND n.publish_until IS NOT NULL AND n.publish_until < CURRENT_TIMESTAMP
                    AND COALESCE(read_totals.acknowledged_count, 0) < COALESCE(audience_totals.audience_count, 0)
                    THEN 'overdue'
                WHEN COALESCE(read_totals.opened_count, 0) < COALESCE(audience_totals.audience_count, 0) THEN 'open'
                ELSE 'complete'
            END AS status_code,
            CASE
                WHEN COALESCE(audience_totals.audience_count, 0) = 0 THEN 'info'
                WHEN n.mandatory_acknowledgement = true AND n.publish_until IS NOT NULL AND n.publish_until < CURRENT_TIMESTAMP
                    AND COALESCE(read_totals.acknowledged_count, 0) < COALESCE(audience_totals.audience_count, 0)
                    THEN 'critical'
                WHEN COALESCE(read_totals.opened_count, 0) < COALESCE(audience_totals.audience_count, 0) THEN 'warning'
                ELSE 'info'
            END AS severity_code
        FROM info.notice AS n
        LEFT JOIN audience_totals
          ON audience_totals.tenant_id = n.tenant_id
         AND audience_totals.notice_id = n.id
        LEFT JOIN read_totals
          ON read_totals.tenant_id = n.tenant_id
         AND read_totals.notice_id = n.id
        WHERE n.archived_at IS NULL;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.free_sundays_v AS
        WITH sunday_work AS (
            SELECT
                ar.tenant_id,
                ar.employee_id,
                date_trunc('month', ar.planned_start_at)::date AS service_month,
                ar.planned_start_at::date AS sunday_date
            FROM finance.actual_record AS ar
            WHERE ar.employee_id IS NOT NULL
              AND ar.archived_at IS NULL
              AND ar.is_current = true
              AND ar.approval_stage_code IN ('operational_confirmed', 'finance_signed_off')
              AND EXTRACT(DOW FROM ar.planned_start_at) = 0
        ),
        approved_absence_sunday AS (
            SELECT
                ea.tenant_id,
                ea.employee_id,
                date_trunc('month', gs.day)::date AS service_month,
                COUNT(*)::int AS approved_absence_sunday_count
            FROM hr.employee_absence AS ea
            JOIN LATERAL generate_series(ea.starts_on::timestamp, ea.ends_on::timestamp, interval '1 day') AS gs(day)
              ON TRUE
            WHERE ea.archived_at IS NULL
              AND ea.status = 'approved'
              AND EXTRACT(DOW FROM gs.day) = 0
            GROUP BY ea.tenant_id, ea.employee_id, date_trunc('month', gs.day)::date
        ),
        month_scope AS (
            SELECT DISTINCT tenant_id, employee_id, service_month
            FROM sunday_work
            UNION
            SELECT DISTINCT tenant_id, employee_id, service_month
            FROM approved_absence_sunday
        ),
        worked_totals AS (
            SELECT tenant_id, employee_id, service_month, COUNT(DISTINCT sunday_date)::int AS worked_sunday_count
            FROM sunday_work
            GROUP BY tenant_id, employee_id, service_month
        ),
        sunday_calendar AS (
            SELECT
                ms.tenant_id,
                ms.employee_id,
                ms.service_month,
                COUNT(*) FILTER (WHERE EXTRACT(DOW FROM day) = 0)::int AS sunday_count_in_month
            FROM month_scope AS ms
            JOIN LATERAL generate_series(
                ms.service_month::timestamp,
                (ms.service_month + INTERVAL '1 month - 1 day')::timestamp,
                interval '1 day'
            ) AS day ON TRUE
            GROUP BY ms.tenant_id, ms.employee_id, ms.service_month
        )
        SELECT
            ms.tenant_id,
            e.id AS employee_id,
            e.personnel_no,
            TRIM(CONCAT(e.first_name, ' ', e.last_name)) AS display_name,
            e.default_branch_id AS branch_id,
            e.default_mandate_id AS mandate_id,
            ms.service_month,
            COALESCE(sc.sunday_count_in_month, 0) AS sunday_count_in_month,
            COALESCE(wt.worked_sunday_count, 0) AS worked_sunday_count,
            GREATEST(COALESCE(sc.sunday_count_in_month, 0) - COALESCE(wt.worked_sunday_count, 0), 0) AS free_sunday_count,
            COALESCE(aas.approved_absence_sunday_count, 0) AS approved_absence_sunday_count,
            1 AS threshold_days_or_count,
            CASE
                WHEN GREATEST(COALESCE(sc.sunday_count_in_month, 0) - COALESCE(wt.worked_sunday_count, 0), 0) >= 1 THEN 'compliant'
                ELSE 'non_compliant'
            END AS status_code,
            CASE
                WHEN GREATEST(COALESCE(sc.sunday_count_in_month, 0) - COALESCE(wt.worked_sunday_count, 0), 0) >= 1 THEN 'info'
                ELSE 'warning'
            END AS severity_code
        FROM month_scope AS ms
        JOIN hr.employee AS e
          ON e.tenant_id = ms.tenant_id
         AND e.id = ms.employee_id
         AND e.archived_at IS NULL
         AND e.status = 'active'
        LEFT JOIN worked_totals AS wt
          ON wt.tenant_id = ms.tenant_id
         AND wt.employee_id = ms.employee_id
         AND wt.service_month = ms.service_month
        LEFT JOIN sunday_calendar AS sc
          ON sc.tenant_id = ms.tenant_id
         AND sc.employee_id = ms.employee_id
         AND sc.service_month = ms.service_month
        LEFT JOIN approved_absence_sunday AS aas
          ON aas.tenant_id = ms.tenant_id
         AND aas.employee_id = ms.employee_id
         AND aas.service_month = ms.service_month;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.absence_visibility_v AS
        SELECT
            ea.tenant_id,
            ea.id AS absence_id,
            e.id AS employee_id,
            e.personnel_no,
            TRIM(CONCAT(e.first_name, ' ', e.last_name)) AS display_name,
            e.default_branch_id AS branch_id,
            e.default_mandate_id AS mandate_id,
            ea.absence_type,
            ea.status AS status_code,
            ea.starts_on,
            ea.ends_on,
            ea.quantity_days,
            ea.approved_at,
            ea.approved_by_user_id
        FROM hr.employee_absence AS ea
        JOIN hr.employee AS e
          ON e.tenant_id = ea.tenant_id
         AND e.id = ea.employee_id
        WHERE ea.archived_at IS NULL
          AND e.archived_at IS NULL;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW rpt.inactivity_signals_v AS
        WITH latest_login_failure AS (
            SELECT
                le.tenant_id,
                le.user_account_id,
                MAX(le.created_at) AS last_login_failure_at
            FROM audit.login_event AS le
            WHERE le.outcome = 'failure'
            GROUP BY le.tenant_id, le.user_account_id
        ),
        active_roles AS (
            SELECT
                ura.tenant_id,
                ura.user_account_id,
                STRING_AGG(DISTINCT r.key, ',' ORDER BY r.key) AS role_keys
            FROM iam.user_role_assignment AS ura
            JOIN iam.role AS r
              ON r.id = ura.role_id
            WHERE ura.archived_at IS NULL
              AND ura.status = 'active'
              AND r.archived_at IS NULL
              AND r.status = 'active'
            GROUP BY ura.tenant_id, ura.user_account_id
        )
        SELECT
            ua.tenant_id,
            ua.id AS user_account_id,
            CASE
                WHEN e.id IS NOT NULL THEN 'employee'
                WHEN cc.id IS NOT NULL THEN 'customer_contact'
                WHEN sc.id IS NOT NULL THEN 'subcontractor_contact'
                ELSE 'internal_user'
            END AS actor_type_code,
            COALESCE(e.id, cc.id, sc.id, ua.id) AS actor_id,
            COALESCE(TRIM(CONCAT(e.first_name, ' ', e.last_name)), cc.full_name, sc.full_name, ua.full_name) AS actor_display_name,
            COALESCE(ar.role_keys, '') AS role_keys,
            ua.status AS account_status,
            e.default_branch_id AS branch_id,
            e.default_mandate_id AS mandate_id,
            ua.last_login_at,
            llf.last_login_failure_at,
            CASE
                WHEN ua.last_login_at IS NULL THEN NULL
                ELSE (CURRENT_DATE - ua.last_login_at::date)::int
            END AS days_since_last_login,
            30 AS inactivity_threshold_days,
            CASE
                WHEN ua.archived_at IS NOT NULL OR ua.status <> 'active' THEN 'inactive_account'
                WHEN ua.last_login_at IS NULL THEN 'never_logged_in'
                WHEN (CURRENT_DATE - ua.last_login_at::date) >= 30 THEN 'inactive'
                ELSE 'active'
            END AS status_code,
            CASE
                WHEN ua.archived_at IS NOT NULL OR ua.status <> 'active' THEN 'critical'
                WHEN ua.last_login_at IS NULL THEN 'warning'
                WHEN (CURRENT_DATE - ua.last_login_at::date) >= 30 THEN 'warning'
                ELSE 'info'
            END AS severity_code
        FROM iam.user_account AS ua
        LEFT JOIN active_roles AS ar
          ON ar.tenant_id = ua.tenant_id
         AND ar.user_account_id = ua.id
        LEFT JOIN latest_login_failure AS llf
          ON llf.tenant_id = ua.tenant_id
         AND llf.user_account_id = ua.id
        LEFT JOIN hr.employee AS e
          ON e.tenant_id = ua.tenant_id
         AND e.user_id = ua.id
         AND e.archived_at IS NULL
        LEFT JOIN crm.customer_contact AS cc
          ON cc.tenant_id = ua.tenant_id
         AND cc.user_id = ua.id
         AND cc.archived_at IS NULL
        LEFT JOIN partner.subcontractor_contact AS sc
          ON sc.tenant_id = ua.tenant_id
         AND sc.user_id = ua.id
         AND sc.archived_at IS NULL
        WHERE ua.archived_at IS NULL;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS rpt.inactivity_signals_v")
    op.execute("DROP VIEW IF EXISTS rpt.absence_visibility_v")
    op.execute("DROP VIEW IF EXISTS rpt.free_sundays_v")
    op.execute("DROP VIEW IF EXISTS rpt.notice_read_stats_v")
    op.execute("DROP VIEW IF EXISTS rpt.compliance_status_v")
