"""Dedicated customer dashboard read models for the internal customer workspace."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from typing import Protocol

from app.errors import ApiException
from app.modules.customers.policy import enforce_customer_module_access
from app.modules.customers.schemas import (
    CustomerDashboardCalendarItemRead,
    CustomerDashboardFinanceSummaryRead,
    CustomerDashboardPlanItemRead,
    CustomerDashboardPlanningSummaryRead,
    CustomerDashboardRead,
)
from app.modules.iam.authz import RequestAuthorizationContext


class CustomerDashboardRepository(Protocol):
    def get_customer(self, tenant_id: str, customer_id: str): ...  # noqa: ANN001
    def count_planning_records_for_customer(self, tenant_id: str, customer_id: str) -> int: ...
    def list_latest_planning_records_for_customer(
        self,
        tenant_id: str,
        customer_id: str,
        *,
        limit: int,
    ) -> list[object]: ...
    def list_released_customer_invoices_for_customer(self, tenant_id: str, customer_id: str) -> list[object]: ...  # noqa: ANN401


class CustomerDashboardReadService:
    RELEASED_INVOICE_STATUSES = frozenset({"released", "queued", "sent"})
    FINANCE_LABEL_RELEASED_TOTAL = "released_invoice_total"
    FINANCE_LABEL_RELEASED_TOTAL_MULTI_CURRENCY = "released_invoice_total_multi_currency"
    CALENDAR_ITEM_LIMIT = 20

    def __init__(self, repository: CustomerDashboardRepository) -> None:
        self.repository = repository

    def get_dashboard(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> CustomerDashboardRead:
        self._require_customer(tenant_id, customer_id, actor)
        latest_plans = self.repository.list_latest_planning_records_for_customer(tenant_id, customer_id, limit=5)
        calendar_rows = self.repository.list_latest_planning_records_for_customer(
            tenant_id,
            customer_id,
            limit=self.CALENDAR_ITEM_LIMIT,
        )
        return CustomerDashboardRead(
            customer_id=customer_id,
            planning_summary=CustomerDashboardPlanningSummaryRead(
                total_plans_count=self.repository.count_planning_records_for_customer(tenant_id, customer_id),
                latest_plans=[self._serialize_plan_item(row) for row in latest_plans],
            ),
            finance_summary=self._build_finance_summary(tenant_id, customer_id, actor),
            calendar_items=[self._serialize_calendar_item(row) for row in calendar_rows],
        )

    def _build_finance_summary(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> CustomerDashboardFinanceSummaryRead:
        if not actor.has_permission("customers.billing.read"):
            return CustomerDashboardFinanceSummaryRead(
                visibility="restricted",
                semantic_label=self.FINANCE_LABEL_RELEASED_TOTAL,
            )
        invoices = self.repository.list_released_customer_invoices_for_customer(tenant_id, customer_id)
        if not invoices:
            return CustomerDashboardFinanceSummaryRead(
                visibility="available",
                total_received_amount=Decimal("0.00"),
                currency_code=None,
                semantic_label=self.FINANCE_LABEL_RELEASED_TOTAL,
            )
        currency_codes = {str(getattr(row, "currency_code", "") or "").upper() for row in invoices if getattr(row, "currency_code", None)}
        if len(currency_codes) != 1:
            return CustomerDashboardFinanceSummaryRead(
                visibility="unavailable",
                total_received_amount=None,
                currency_code=None,
                semantic_label=self.FINANCE_LABEL_RELEASED_TOTAL_MULTI_CURRENCY,
            )
        total = sum((Decimal(str(getattr(row, "total_amount", 0) or 0)) for row in invoices), Decimal("0.00"))
        return CustomerDashboardFinanceSummaryRead(
            visibility="available",
            total_received_amount=total.quantize(Decimal("0.01")),
            currency_code=next(iter(currency_codes)),
            semantic_label=self.FINANCE_LABEL_RELEASED_TOTAL,
        )

    @staticmethod
    def _serialize_plan_item(row: object) -> CustomerDashboardPlanItemRead:
        order = getattr(row, "order", None)
        order_no = str(getattr(order, "order_no", "") or "")
        label = str(getattr(row, "name", "") or order_no or getattr(order, "title", ""))
        if order_no and label and label != order_no:
            label = f"{order_no} · {label}"
        return CustomerDashboardPlanItemRead(
            id=str(getattr(row, "id")),
            order_id=str(getattr(row, "order_id")),
            order_no=order_no,
            label=label,
            status=str(getattr(row, "release_state")),
            planning_mode_code=str(getattr(row, "planning_mode_code")),
            planning_from=getattr(row, "planning_from"),
            planning_to=getattr(row, "planning_to"),
            released_at=getattr(row, "released_at", None),
        )

    def _serialize_calendar_item(self, row: object) -> CustomerDashboardCalendarItemRead:
        order = getattr(row, "order", None)
        plan_item = self._serialize_plan_item(row)
        return CustomerDashboardCalendarItemRead(
            id=f"planning_record:{getattr(row, 'id')}",
            source_type="planning_record",
            source_ref_id=str(getattr(row, "id")),
            order_id=str(getattr(order, "id")) if getattr(order, "id", None) is not None else str(getattr(row, "order_id")),
            planning_record_id=str(getattr(row, "id")),
            title=plan_item.label,
            starts_at=self._start_of_day(getattr(row, "planning_from")),
            ends_at=self._end_boundary(getattr(row, "planning_to")),
            status=plan_item.status,
        )

    @staticmethod
    def _start_of_day(value) -> datetime | None:  # noqa: ANN001
        if value is None:
            return None
        return datetime.combine(value, time.min, tzinfo=UTC)

    @staticmethod
    def _end_boundary(value) -> datetime | None:  # noqa: ANN001
        if value is None:
            return None
        return datetime.combine(value + timedelta(days=1), time.min, tzinfo=UTC)

    def _require_customer(self, tenant_id: str, customer_id: str, actor: RequestAuthorizationContext):
        enforce_customer_module_access(actor, tenant_id=tenant_id)
        row = self.repository.get_customer(tenant_id, customer_id)
        if row is None:
            raise self._not_found("customer")
        return row

    @staticmethod
    def _not_found(entity: str) -> ApiException:
        return ApiException(
            404,
            f"customers.not_found.{entity}",
            f"errors.customers.{entity}.not_found",
        )
