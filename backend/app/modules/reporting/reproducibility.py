"""Internal reporting reproducibility helpers for QA and tests."""

from __future__ import annotations

import csv
from io import StringIO


REPORT_TRACEABILITY = {
    "employee-activity": {
        "view": "rpt.employee_activity_v",
        "source_chain": [
            "hr.employee",
            "ops.assignment",
            "ops.shift",
            "finance.actual_record",
            "hr.employee_event_application",
            "hr.employee_absence",
            "hr.employee_time_account_txn",
            "audit.login_event",
        ],
        "export_format": "csv",
    },
    "customer-revenue": {
        "view": "rpt.customer_revenue_v",
        "source_chain": [
            "finance.customer_invoice",
            "finance.timesheet",
            "finance.timesheet_line",
            "finance.actual_record",
            "ops.customer_order",
            "ops.planning_record",
            "crm.customer",
        ],
        "export_format": "csv",
    },
    "subcontractor-control": {
        "view": "rpt.subcontractor_control_v",
        "source_chain": [
            "finance.subcontractor_invoice_check",
            "finance.subcontractor_invoice_check_line",
            "ops.shift",
            "partner.subcontractor_worker",
            "partner.subcontractor_worker_qualification",
        ],
        "export_format": "csv",
    },
    "planning-performance": {
        "view": "rpt.planning_performance_v",
        "source_chain": [
            "ops.shift",
            "ops.shift_plan",
            "ops.planning_record",
            "ops.demand_group",
            "ops.assignment",
            "finance.actual_record",
        ],
        "export_format": "csv",
    },
    "payroll-basis": {
        "view": "rpt.payroll_basis_v",
        "source_chain": [
            "finance.actual_record",
            "finance.employee_pay_profile",
            "finance.payroll_export_item",
            "finance.payroll_export_batch",
            "finance.payroll_payslip_archive",
            "hr.employee_allowance",
            "hr.employee_advance",
        ],
        "export_format": "csv",
    },
    "customer-profitability": {
        "view": "rpt.customer_profitability_v",
        "source_chain": [
            "finance.customer_invoice",
            "finance.customer_invoice_line",
            "rpt.payroll_basis_v",
            "finance.actual_expense",
            "crm.customer",
            "ops.customer_order",
            "ops.planning_record",
        ],
        "export_format": "csv",
    },
    "compliance-status": {
        "view": "rpt.compliance_status_v",
        "source_chain": [
            "hr.employee_qualification",
            "partner.subcontractor_worker_qualification",
            "hr.qualification_type",
            "docs.document_link",
            "docs.document",
            "partner.subcontractor_scope",
        ],
        "export_format": "csv",
    },
    "notice-read-stats": {
        "view": "rpt.notice_read_stats_v",
        "source_chain": [
            "info.notice",
            "info.notice_audience",
            "info.notice_read",
            "iam.user_role_assignment",
            "hr.employee",
            "crm.customer_contact",
            "partner.subcontractor_contact",
        ],
        "export_format": "csv",
    },
    "free-sundays": {
        "view": "rpt.free_sundays_v",
        "source_chain": [
            "finance.actual_record",
            "hr.employee",
            "hr.employee_absence",
        ],
        "export_format": "csv",
    },
    "absence-visibility": {
        "view": "rpt.absence_visibility_v",
        "source_chain": [
            "hr.employee_absence",
            "hr.employee",
        ],
        "export_format": "csv",
    },
    "inactivity-signals": {
        "view": "rpt.inactivity_signals_v",
        "source_chain": [
            "iam.user_account",
            "audit.login_event",
            "iam.user_role_assignment",
            "hr.employee",
            "crm.customer_contact",
            "partner.subcontractor_contact",
        ],
        "export_format": "csv",
    },
    "security-activity": {
        "view": "rpt.security_activity_v",
        "source_chain": [
            "audit.login_event",
            "audit.audit_event",
            "field.watchbook",
            "iam.user_account",
        ],
        "export_format": "csv",
    },
}


def parse_csv_payload(payload: str) -> list[dict[str, str]]:
    if not payload.strip():
        return []
    reader = csv.DictReader(StringIO(payload))
    return [dict(row) for row in reader]


def compare_csv_to_rows(payload: str, rows: list[dict[str, object]]) -> bool:
    csv_rows = parse_csv_payload(payload)
    normalized_rows = [{key: "" if value is None else str(value) for key, value in row.items()} for row in rows]
    return csv_rows == normalized_rows
