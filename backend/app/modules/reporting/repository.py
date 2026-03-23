"""SQL-view-backed reporting repository."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.modules.reporting.schemas import (
    AbsenceVisibilityReportRow,
    ComplianceStatusReportRow,
    CustomerProfitabilityReportRow,
    CustomerRevenueReportRow,
    EmployeeActivityReportRow,
    FreeSundayStatusReportRow,
    InactivitySignalReportRow,
    NoticeReadStatsReportRow,
    PayrollBasisReportRow,
    PlanningPerformanceReportRow,
    ReportingDeliveryJobRead,
    ReportingFilterBase,
    SecurityActivityReportRow,
    SubcontractorControlReportRow,
)


class ReportingRepository:
    def list_employee_activity(  # noqa: PLR0913
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        *,
        allowed_customer_ids: set[str] | None = None,
        allowed_subcontractor_ids: set[str] | None = None,
    ) -> list[EmployeeActivityReportRow]:
        raise NotImplementedError

    def list_customer_revenue(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        *,
        allowed_customer_ids: set[str] | None = None,
    ) -> list[CustomerRevenueReportRow]:
        raise NotImplementedError

    def list_subcontractor_control(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        *,
        allowed_subcontractor_ids: set[str] | None = None,
    ) -> list[SubcontractorControlReportRow]:
        raise NotImplementedError

    def list_planning_performance(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        *,
        allowed_customer_ids: set[str] | None = None,
    ) -> list[PlanningPerformanceReportRow]:
        raise NotImplementedError

    def list_payroll_basis(self, tenant_id: str, filters: ReportingFilterBase) -> list[PayrollBasisReportRow]:
        raise NotImplementedError

    def list_customer_profitability(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        *,
        allowed_customer_ids: set[str] | None = None,
    ) -> list[CustomerProfitabilityReportRow]:
        raise NotImplementedError

    def list_compliance_status(self, tenant_id: str, filters: ReportingFilterBase) -> list[ComplianceStatusReportRow]:
        raise NotImplementedError

    def list_notice_read_stats(self, tenant_id: str, filters: ReportingFilterBase) -> list[NoticeReadStatsReportRow]:
        raise NotImplementedError

    def list_free_sundays(self, tenant_id: str, filters: ReportingFilterBase) -> list[FreeSundayStatusReportRow]:
        raise NotImplementedError

    def list_absence_visibility(self, tenant_id: str, filters: ReportingFilterBase) -> list[AbsenceVisibilityReportRow]:
        raise NotImplementedError

    def list_inactivity_signals(self, tenant_id: str, filters: ReportingFilterBase) -> list[InactivitySignalReportRow]:
        raise NotImplementedError

    def list_security_activity(self, tenant_id: str, filters: ReportingFilterBase) -> list[SecurityActivityReportRow]:
        raise NotImplementedError

    def list_reporting_delivery_jobs(
        self,
        tenant_id: str,
        *,
        report_key: str | None = None,
        limit: int = 50,
    ) -> list[ReportingDeliveryJobRead]:
        raise NotImplementedError


class SqlAlchemyReportingRepository(ReportingRepository):
    _REPORT_DATE_COLUMN: dict[str, str] = {
        "employee_activity": "activity_month",
        "customer_revenue": "issue_date",
        "subcontractor_control": "period_start",
        "planning_performance": "shift_date",
        "payroll_basis": "service_date",
        "customer_profitability": "service_month",
        "compliance_status": "valid_until",
        "notice_read_stats": "published_at",
        "free_sundays": "service_month",
        "absence_visibility": "starts_on",
        "inactivity_signals": "last_login_at",
        "security_activity": "occurred_at",
    }
    _REPORT_FILTER_COLUMNS: dict[str, frozenset[str]] = {
        "employee_activity": frozenset({"date_from", "date_to", "branch_id", "mandate_id", "employee_id"}),
        "customer_revenue": frozenset(
            {
                "date_from",
                "date_to",
                "branch_id",
                "mandate_id",
                "customer_id",
                "order_id",
                "planning_record_id",
                "invoice_status_code",
            }
        ),
        "subcontractor_control": frozenset(
            {
                "date_from",
                "date_to",
                "branch_id",
                "mandate_id",
                "subcontractor_id",
                "status_code",
            }
        ),
        "planning_performance": frozenset(
            {
                "date_from",
                "date_to",
                "branch_id",
                "mandate_id",
                "customer_id",
                "order_id",
                "planning_record_id",
                "planning_mode_code",
                "status_code",
            }
        ),
        "payroll_basis": frozenset(
            {
                "date_from",
                "date_to",
                "branch_id",
                "mandate_id",
                "employee_id",
                "export_state_code",
            }
        ),
        "customer_profitability": frozenset(
            {
                "date_from",
                "date_to",
                "branch_id",
                "mandate_id",
                "customer_id",
                "order_id",
                "planning_record_id",
            }
        ),
        "compliance_status": frozenset(
            {
                "date_from",
                "date_to",
                "branch_id",
                "mandate_id",
                "employee_id",
                "subcontractor_id",
                "actor_type_code",
                "rule_code",
                "document_type_key",
                "severity_code",
                "status_code",
            }
        ),
        "notice_read_stats": frozenset({"date_from", "date_to", "severity_code", "status_code"}),
        "free_sundays": frozenset({"date_from", "date_to", "branch_id", "mandate_id", "employee_id", "severity_code", "status_code"}),
        "absence_visibility": frozenset({"date_from", "date_to", "branch_id", "mandate_id", "employee_id", "status_code"}),
        "inactivity_signals": frozenset({"date_from", "date_to", "branch_id", "mandate_id", "actor_type_code", "severity_code", "status_code"}),
        "security_activity": frozenset({"date_from", "date_to", "branch_id", "mandate_id", "severity_code", "category_code", "result_status_code", "entity_type", "request_id"}),
    }
    _SORT_MAP: dict[str, dict[str, str]] = {
        "employee_activity": {
            "activity_month": "activity_month",
            "display_name": "display_name",
            "confirmed_shift_count": "confirmed_shift_count",
            "login_count": "login_count",
            "approved_absence_days": "approved_absence_days",
        },
        "customer_revenue": {
            "issue_date": "issue_date",
            "due_date": "due_date",
            "total_amount": "total_amount",
            "customer_name": "customer_name",
            "invoice_status_code": "invoice_status_code",
        },
        "subcontractor_control": {
            "period_start": "period_start",
            "approved_amount_total": "approved_amount_total",
            "comparison_variance_amount": "comparison_variance_amount",
            "subcontractor_name": "subcontractor_name",
            "status_code": "status_code",
        },
        "planning_performance": {
            "shift_date": "shift_date",
            "customer_name": "customer_name",
            "fill_rate_ratio": "fill_rate_ratio",
            "coverage_gap_qty": "coverage_gap_qty",
            "planning_mode_code": "planning_mode_code",
        },
        "payroll_basis": {
            "service_date": "service_date",
            "display_name": "display_name",
            "payroll_cost_basis_amount": "payroll_cost_basis_amount",
            "export_state_code": "export_state_code",
        },
        "customer_profitability": {
            "service_month": "service_month",
            "customer_name": "customer_name",
            "revenue_net_amount": "revenue_net_amount",
            "contribution_margin_amount": "contribution_margin_amount",
            "contribution_margin_ratio": "contribution_margin_ratio",
        },
        "compliance_status": {
            "actor_display_name": "actor_display_name",
            "status_code": "status_code",
            "severity_code": "severity_code",
            "valid_until": "valid_until",
            "days_until_expiry": "days_until_expiry",
        },
        "notice_read_stats": {
            "published_at": "published_at",
            "title": "title",
            "completion_ratio": "completion_ratio",
            "unread_count": "unread_count",
            "overdue_unread_count": "overdue_unread_count",
        },
        "free_sundays": {
            "service_month": "service_month",
            "display_name": "display_name",
            "worked_sunday_count": "worked_sunday_count",
            "free_sunday_count": "free_sunday_count",
            "status_code": "status_code",
        },
        "absence_visibility": {
            "starts_on": "starts_on",
            "display_name": "display_name",
            "absence_type": "absence_type",
            "status_code": "status_code",
            "quantity_days": "quantity_days",
        },
        "inactivity_signals": {
            "days_since_last_login": "days_since_last_login",
            "actor_display_name": "actor_display_name",
            "account_status": "account_status",
            "status_code": "status_code",
            "severity_code": "severity_code",
        },
        "security_activity": {
            "occurred_at": "occurred_at",
            "category_code": "category_code",
            "severity_code": "severity_code",
            "result_status_code": "result_status_code",
            "event_type": "event_type",
        },
    }

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_employee_activity(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        *,
        allowed_customer_ids: set[str] | None = None,
        allowed_subcontractor_ids: set[str] | None = None,
    ) -> list[EmployeeActivityReportRow]:
        rows = self._run_list_query(
            "employee_activity",
            EmployeeActivityReportRow,
            tenant_id,
            filters,
            allowed_customer_ids=allowed_customer_ids,
            allowed_subcontractor_ids=allowed_subcontractor_ids,
        )
        return rows

    def list_customer_revenue(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        *,
        allowed_customer_ids: set[str] | None = None,
    ) -> list[CustomerRevenueReportRow]:
        return self._run_list_query(
            "customer_revenue",
            CustomerRevenueReportRow,
            tenant_id,
            filters,
            allowed_customer_ids=allowed_customer_ids,
        )

    def list_subcontractor_control(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        *,
        allowed_subcontractor_ids: set[str] | None = None,
    ) -> list[SubcontractorControlReportRow]:
        return self._run_list_query(
            "subcontractor_control",
            SubcontractorControlReportRow,
            tenant_id,
            filters,
            allowed_subcontractor_ids=allowed_subcontractor_ids,
        )

    def list_planning_performance(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        *,
        allowed_customer_ids: set[str] | None = None,
    ) -> list[PlanningPerformanceReportRow]:
        return self._run_list_query(
            "planning_performance",
            PlanningPerformanceReportRow,
            tenant_id,
            filters,
            allowed_customer_ids=allowed_customer_ids,
        )

    def list_payroll_basis(self, tenant_id: str, filters: ReportingFilterBase) -> list[PayrollBasisReportRow]:
        return self._run_list_query("payroll_basis", PayrollBasisReportRow, tenant_id, filters)

    def list_customer_profitability(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        *,
        allowed_customer_ids: set[str] | None = None,
    ) -> list[CustomerProfitabilityReportRow]:
        return self._run_list_query(
            "customer_profitability",
            CustomerProfitabilityReportRow,
            tenant_id,
            filters,
            allowed_customer_ids=allowed_customer_ids,
        )

    def list_compliance_status(self, tenant_id: str, filters: ReportingFilterBase) -> list[ComplianceStatusReportRow]:
        return self._run_list_query("compliance_status", ComplianceStatusReportRow, tenant_id, filters)

    def list_notice_read_stats(self, tenant_id: str, filters: ReportingFilterBase) -> list[NoticeReadStatsReportRow]:
        return self._run_list_query("notice_read_stats", NoticeReadStatsReportRow, tenant_id, filters)

    def list_free_sundays(self, tenant_id: str, filters: ReportingFilterBase) -> list[FreeSundayStatusReportRow]:
        return self._run_list_query("free_sundays", FreeSundayStatusReportRow, tenant_id, filters)

    def list_absence_visibility(self, tenant_id: str, filters: ReportingFilterBase) -> list[AbsenceVisibilityReportRow]:
        return self._run_list_query("absence_visibility", AbsenceVisibilityReportRow, tenant_id, filters)

    def list_inactivity_signals(self, tenant_id: str, filters: ReportingFilterBase) -> list[InactivitySignalReportRow]:
        return self._run_list_query("inactivity_signals", InactivitySignalReportRow, tenant_id, filters)

    def list_security_activity(self, tenant_id: str, filters: ReportingFilterBase) -> list[SecurityActivityReportRow]:
        return self._run_list_query("security_activity", SecurityActivityReportRow, tenant_id, filters)

    def list_reporting_delivery_jobs(
        self,
        tenant_id: str,
        *,
        report_key: str | None = None,
        limit: int = 50,
    ) -> list[ReportingDeliveryJobRead]:
        sql = """
            SELECT
                job.id AS job_id,
                job.tenant_id,
                COALESCE(job.request_payload_json ->> 'report_key', '') AS report_key,
                job.status AS job_status,
                job.created_at AS requested_at,
                job.started_at,
                job.completed_at,
                job.next_delivery_at AS scheduled_for,
                job.requested_by_user_id,
                job.endpoint_id,
                doc.id AS document_id,
                doc.title AS document_title,
                COALESCE((job.result_summary_json ->> 'row_count')::int, 0) AS row_count,
                job.request_payload_json ->> 'target_label' AS target_label
            FROM (
                SELECT
                    j.*,
                    CASE
                        WHEN jsonb_typeof(j.request_payload_json -> 'scheduled_for') = 'string'
                        THEN (j.request_payload_json ->> 'scheduled_for')::timestamptz
                        ELSE NULL
                    END AS next_delivery_at
                FROM integration.import_export_job AS j
                WHERE j.tenant_id = :tenant_id
                  AND j.job_type = 'reporting_export'
            ) AS job
            LEFT JOIN docs.document_link AS l
              ON l.tenant_id = job.tenant_id
             AND l.owner_type = 'integration.import_export_job'
             AND l.owner_id = job.id
             AND l.relation_type = 'generated_output'
            LEFT JOIN docs.document AS doc
              ON doc.tenant_id = l.tenant_id
             AND doc.id = l.document_id
            ORDER BY job.created_at DESC
            LIMIT :limit
            """
        params = {"tenant_id": tenant_id, "limit": limit}
        if report_key is not None:
            sql = sql.replace(
                "ORDER BY job.created_at DESC",
                "WHERE job.request_payload_json ->> 'report_key' = :report_key\n            ORDER BY job.created_at DESC",
            )
            params["report_key"] = report_key
        query = text(sql)
        rows = self._session.execute(query, params).mappings().all()
        return [ReportingDeliveryJobRead.model_validate(row) for row in rows]

    def _run_list_query(
        self,
        report_key: str,
        schema_type,
        tenant_id: str,
        filters: ReportingFilterBase,
        *,
        allowed_customer_ids: set[str] | None = None,
        allowed_subcontractor_ids: set[str] | None = None,
    ) -> list[Any]:
        params: dict[str, Any] = {
            "tenant_id": tenant_id,
            "limit": filters.limit,
            "offset": filters.offset,
        }
        active_filters = self._active_filters(report_key, filters)
        params.update(active_filters)
        if allowed_customer_ids is not None:
            params["allowed_customer_ids"] = sorted(allowed_customer_ids)
        if allowed_subcontractor_ids is not None:
            params["allowed_subcontractor_ids"] = sorted(allowed_subcontractor_ids)
        query = self._build_query(report_key, filters, allowed_customer_ids, allowed_subcontractor_ids)
        return [
            schema_type.model_validate(row)
            for row in self._session.execute(query, params).mappings().all()
        ]

    def _build_query(
        self,
        report_key: str,
        filters: ReportingFilterBase,
        allowed_customer_ids: set[str] | None,
        allowed_subcontractor_ids: set[str] | None,
    ):
        where_clauses = ["tenant_id = :tenant_id"]
        binds: list[Any] = []
        date_column = self._REPORT_DATE_COLUMN[report_key]
        if filters.date_from is not None:
            where_clauses.append(f"{date_column} IS NOT NULL AND {date_column} >= :date_from")
        if filters.date_to is not None:
            where_clauses.append(f"{date_column} IS NOT NULL AND {date_column} <= :date_to")
        for column in self._REPORT_FILTER_COLUMNS[report_key]:
            if column in {"date_from", "date_to"}:
                continue
            if getattr(filters, column) is not None:
                where_clauses.append(f"{column} = :{column}")
        if allowed_customer_ids is not None and report_key in {"customer_revenue", "planning_performance", "customer_profitability"}:
            binds.append(bindparam("allowed_customer_ids", expanding=True))
            where_clauses.append("customer_id IN :allowed_customer_ids")
        if allowed_subcontractor_ids is not None and report_key == "subcontractor_control":
            binds.append(bindparam("allowed_subcontractor_ids", expanding=True))
            where_clauses.append("subcontractor_id IN :allowed_subcontractor_ids")
        sort_column = self._SORT_MAP[report_key].get(filters.sort_by or "", date_column)
        sort_direction = "ASC" if filters.sort_direction == "asc" else "DESC"
        sql = text(
            f"""
            SELECT *
            FROM rpt.{report_key}_v
            WHERE {' AND '.join(where_clauses)}
            ORDER BY {sort_column} {sort_direction}, tenant_id ASC
            LIMIT :limit OFFSET :offset
            """
        )
        if binds:
            sql = sql.bindparams(*binds)
        return sql

    def _active_filters(self, report_key: str, filters: ReportingFilterBase) -> dict[str, Any]:
        active: dict[str, Any] = {}
        for field_name in self._REPORT_FILTER_COLUMNS[report_key]:
            value = getattr(filters, field_name)
            if value is not None:
                active[field_name] = value
        return active


def serialize_rows_for_csv(rows: Sequence[object]) -> tuple[list[str], list[list[str]]]:
    if not rows:
        return [], []
    sample = rows[0]
    columns = list(sample.model_dump().keys())
    data = []
    for row in rows:
        payload = row.model_dump()
        data.append(["" if payload[column] is None else str(payload[column]) for column in columns])
    return columns, data
