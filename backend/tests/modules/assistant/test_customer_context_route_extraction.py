from __future__ import annotations

from app.modules.assistant.retrieval_planner import extract_route_context_signals


def test_extract_customer_orders_tab_route_context_signals() -> None:
    signals = extract_route_context_signals(
        {
            "page_id": "C-01",
            "path": "/admin/customers",
            "route_name": "SicherPlanCustomers",
            "query": {"customer_id": "cust-1", "tab": "orders"},
        }
    )

    assert signals["customer_id"] == "cust-1"
    assert signals["tab"] == "orders"
    assert signals["customer_orders_tab"] is True
    assert signals["customer_context_active"] is True
    assert signals["customer_order_workspace"] is False


def test_extract_customer_order_workspace_route_context_signals() -> None:
    signals = extract_route_context_signals(
        {
            "page_id": "C-02",
            "path": "/admin/customers/order-workspace",
            "route_name": "SicherPlanCustomerOrderWorkspace",
            "query": {
                "customer_id": "cust-1",
                "order_id": "ord-7",
                "planning_record_id": "plan-9",
                "shift_plan_id": "shift-plan-3",
                "date": "2026-05-01",
            },
        }
    )

    assert signals["customer_id"] == "cust-1"
    assert signals["order_id"] == "ord-7"
    assert signals["planning_record_id"] == "plan-9"
    assert signals["shift_plan_id"] == "shift-plan-3"
    assert signals["date"] == "2026-05-01"
    assert signals["customer_order_workspace"] is True
