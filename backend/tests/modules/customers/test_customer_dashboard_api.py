from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import Request

from app.errors import ApiException
from app.modules.customers.dashboard_service import CustomerDashboardReadService
from app.modules.customers.router import get_customer_dashboard
from app.modules.customers.schemas import CustomerDashboardRead
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization


def _request(tenant_id: str, customer_id: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": f"/api/customers/tenants/{tenant_id}/customers/{customer_id}/dashboard",
            "path_params": {"tenant_id": tenant_id, "customer_id": customer_id},
            "headers": [],
        }
    )


def _context(
    *,
    tenant_id: str = "tenant-1",
    permission_keys: frozenset[str] | None = None,
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=permission_keys
        if permission_keys is not None
        else frozenset({"customers.customer.read", "customers.billing.read"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-1",
    )


@dataclass
class FakeOrder:
    id: str
    customer_id: str
    order_no: str
    title: str


@dataclass
class FakePlanningRecord:
    id: str
    tenant_id: str
    order_id: str
    name: str
    planning_mode_code: str
    planning_from: date
    planning_to: date
    release_state: str
    created_at: datetime
    released_at: datetime | None = None
    archived_at: datetime | None = None
    order: FakeOrder | None = None


@dataclass
class FakeInvoice:
    id: str
    tenant_id: str
    customer_id: str
    invoice_status_code: str
    total_amount: Decimal
    currency_code: str
    issue_date: date
    created_at: datetime
    archived_at: datetime | None = None


class FakeDashboardRepository:
    def __init__(self) -> None:
        self.customers = {
            ("tenant-1", "customer-1"): SimpleNamespace(id="customer-1", tenant_id="tenant-1"),
            ("tenant-1", "customer-2"): SimpleNamespace(id="customer-2", tenant_id="tenant-1"),
        }
        self.planning_records: list[FakePlanningRecord] = []
        self.invoices: list[FakeInvoice] = []

    def get_customer(self, tenant_id: str, customer_id: str):
        return self.customers.get((tenant_id, customer_id))

    def count_planning_records_for_customer(self, tenant_id: str, customer_id: str) -> int:
        return len(
            [
                row
                for row in self.planning_records
                if row.tenant_id == tenant_id
                and row.archived_at is None
                and row.order is not None
                and row.order.customer_id == customer_id
            ]
        )

    def list_latest_planning_records_for_customer(
        self,
        tenant_id: str,
        customer_id: str,
        *,
        limit: int,
    ) -> list[FakePlanningRecord]:
        rows = [
            row
            for row in self.planning_records
            if row.tenant_id == tenant_id
            and row.archived_at is None
            and row.order is not None
            and row.order.customer_id == customer_id
        ]
        rows.sort(key=lambda row: (row.planning_from, row.created_at, row.id), reverse=True)
        return rows[:limit]

    def list_released_customer_invoices_for_customer(self, tenant_id: str, customer_id: str) -> list[FakeInvoice]:
        rows = [
            row
            for row in self.invoices
            if row.tenant_id == tenant_id
            and row.customer_id == customer_id
            and row.archived_at is None
            and row.invoice_status_code in {"released", "queued", "sent"}
        ]
        rows.sort(key=lambda row: (row.issue_date, row.created_at, row.id), reverse=True)
        return rows


class TestCustomerDashboardReadService:
    def setup_method(self) -> None:
        self.repository = FakeDashboardRepository()
        self.service = CustomerDashboardReadService(self.repository)
        base_created_at = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)
        for index in range(6):
            order = FakeOrder(
                id=f"order-{index}",
                customer_id="customer-1",
                order_no=f"ORD-{index}",
                title=f"Order {index}",
            )
            self.repository.planning_records.append(
                FakePlanningRecord(
                    id=f"plan-{index}",
                    tenant_id="tenant-1",
                    order_id=order.id,
                    name=f"Plan {index}",
                    planning_mode_code="site",
                    planning_from=date(2026, 5, 1) + timedelta(days=index),
                    planning_to=date(2026, 5, 1) + timedelta(days=index + 1),
                    release_state="released" if index % 2 == 0 else "draft",
                    created_at=base_created_at + timedelta(hours=index),
                    released_at=base_created_at + timedelta(hours=index) if index % 2 == 0 else None,
                    order=order,
                )
            )
        foreign_order = FakeOrder(id="order-foreign", customer_id="customer-2", order_no="ORD-X", title="Foreign")
        self.repository.planning_records.append(
            FakePlanningRecord(
                id="plan-foreign",
                tenant_id="tenant-1",
                order_id=foreign_order.id,
                name="Foreign plan",
                planning_mode_code="event",
                planning_from=date(2026, 6, 1),
                planning_to=date(2026, 6, 2),
                release_state="released",
                created_at=base_created_at + timedelta(days=1),
                released_at=base_created_at + timedelta(days=1),
                order=foreign_order,
            )
        )
        self.repository.invoices.extend(
            [
                FakeInvoice(
                    id="invoice-1",
                    tenant_id="tenant-1",
                    customer_id="customer-1",
                    invoice_status_code="released",
                    total_amount=Decimal("120.00"),
                    currency_code="EUR",
                    issue_date=date(2026, 5, 15),
                    created_at=base_created_at,
                ),
                FakeInvoice(
                    id="invoice-2",
                    tenant_id="tenant-1",
                    customer_id="customer-1",
                    invoice_status_code="sent",
                    total_amount=Decimal("80.00"),
                    currency_code="EUR",
                    issue_date=date(2026, 5, 20),
                    created_at=base_created_at + timedelta(days=1),
                ),
                FakeInvoice(
                    id="invoice-foreign",
                    tenant_id="tenant-1",
                    customer_id="customer-2",
                    invoice_status_code="released",
                    total_amount=Decimal("999.00"),
                    currency_code="EUR",
                    issue_date=date(2026, 5, 25),
                    created_at=base_created_at + timedelta(days=2),
                ),
            ]
        )

    def test_empty_dashboard_state_returns_truthful_zero_and_no_items(self) -> None:
        repository = FakeDashboardRepository()
        service = CustomerDashboardReadService(repository)

        dashboard = service.get_dashboard("tenant-1", "customer-1", _context())

        assert dashboard.planning_summary.total_plans_count == 0
        assert dashboard.planning_summary.latest_plans == []
        assert dashboard.calendar_items == []
        assert dashboard.finance_summary.visibility == "available"
        assert dashboard.finance_summary.total_received_amount == Decimal("0.00")
        assert dashboard.finance_summary.currency_code is None
        assert dashboard.finance_summary.semantic_label == "released_invoice_total"

    def test_latest_plans_are_limited_to_five_with_stable_ordering(self) -> None:
        dashboard = self.service.get_dashboard("tenant-1", "customer-1", _context())

        assert dashboard.planning_summary.total_plans_count == 6
        assert [row.id for row in dashboard.planning_summary.latest_plans] == [
            "plan-5",
            "plan-4",
            "plan-3",
            "plan-2",
            "plan-1",
        ]

    def test_calendar_items_are_filtered_to_selected_customer_only(self) -> None:
        dashboard = self.service.get_dashboard("tenant-1", "customer-1", _context())

        assert all(item.planning_record_id != "plan-foreign" for item in dashboard.calendar_items)
        assert all(item.order_id != "order-foreign" for item in dashboard.calendar_items)
        assert dashboard.calendar_items[0].source_type == "planning_record"
        assert dashboard.calendar_items[0].starts_at is not None
        assert dashboard.calendar_items[0].ends_at is not None

    def test_finance_summary_is_restricted_without_billing_permission(self) -> None:
        dashboard = self.service.get_dashboard(
            "tenant-1",
            "customer-1",
            _context(permission_keys=frozenset({"customers.customer.read"})),
        )

        assert dashboard.finance_summary.visibility == "restricted"
        assert dashboard.finance_summary.total_received_amount is None
        assert dashboard.finance_summary.currency_code is None
        assert dashboard.finance_summary.semantic_label == "released_invoice_total"

    def test_finance_summary_uses_released_invoice_total_not_received_cash(self) -> None:
        dashboard = self.service.get_dashboard("tenant-1", "customer-1", _context())

        assert dashboard.finance_summary.visibility == "available"
        assert dashboard.finance_summary.total_received_amount == Decimal("200.00")
        assert dashboard.finance_summary.currency_code == "EUR"
        assert dashboard.finance_summary.semantic_label == "released_invoice_total"

    def test_tenant_isolation_is_enforced(self) -> None:
        with pytest.raises(ApiException) as raised:
            self.service.get_dashboard("tenant-1", "customer-1", _context(tenant_id="tenant-2"))

        assert raised.value.status_code == 403
        assert raised.value.code == "iam.authorization.scope_denied"


def test_customer_dashboard_endpoint_uses_customer_read_scope() -> None:
    tenant_id = str(uuid4())
    customer_id = str(uuid4())
    dependency = require_authorization("customers.customer.read", scope="tenant")
    authorized_context = dependency(_request(tenant_id, customer_id), _context(tenant_id=tenant_id))
    service = SimpleNamespace(
        get_dashboard=lambda tenant_id_arg, customer_id_arg, context: CustomerDashboardRead(
            customer_id=customer_id_arg,
            planning_summary={"total_plans_count": 0, "latest_plans": []},
            finance_summary={"visibility": "restricted", "total_received_amount": None, "currency_code": None, "semantic_label": "released_invoice_total"},
            calendar_items=[],
        )
    )

    result = get_customer_dashboard(UUID(tenant_id), UUID(customer_id), authorized_context, service)  # type: ignore[arg-type]

    assert isinstance(result, CustomerDashboardRead)


def test_customer_dashboard_endpoint_rejects_missing_customer_read_permission() -> None:
    tenant_id = str(uuid4())
    customer_id = str(uuid4())
    dependency = require_authorization("customers.customer.read", scope="tenant")

    with pytest.raises(ApiException) as raised:
        dependency(_request(tenant_id, customer_id), _context(tenant_id=tenant_id, permission_keys=frozenset()))

    assert raised.value.status_code == 403
    assert raised.value.code == "iam.authorization.permission_denied"
