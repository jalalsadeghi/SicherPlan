from __future__ import annotations

from tests.modules.assistant.test_page_help_manifest import _context, _repository, _service


def test_customers_orders_tab_allowed_link_can_include_customer_context() -> None:
    service = _service(_repository())
    result = service.execute_registered_tool(
        tool_name="navigation.build_allowed_link",
        input_data={
            "page_id": "C-01",
            "entity_context": {"customer_id": "cust-1", "tab": "orders"},
        },
        actor=_context("assistant.chat.access", "customers.customer.read"),
    )

    assert result.ok is True
    assert result.data["allowed"] is True
    assert result.data["link"]["path"] == "/admin/customers?customer_id=cust-1&tab=orders"


def test_customer_order_workspace_allowed_link_can_include_order_context() -> None:
    service = _service(_repository())
    result = service.execute_registered_tool(
        tool_name="navigation.build_allowed_link",
        input_data={
            "page_id": "C-02",
            "entity_context": {"customer_id": "cust-1", "order_id": "ord-7"},
        },
        actor=_context("assistant.chat.access"),
    )

    assert result.ok is True
    assert result.data["allowed"] is True
    assert result.data["link"]["path"] == "/admin/customers/order-workspace?customer_id=cust-1&order_id=ord-7"


def test_customers_workspace_allowed_link_falls_back_without_selected_customer() -> None:
    service = _service(_repository())
    result = service.execute_registered_tool(
        tool_name="navigation.build_allowed_link",
        input_data={"page_id": "C-01"},
        actor=_context("assistant.chat.access", "customers.customer.read"),
    )

    assert result.ok is True
    assert result.data["allowed"] is True
    assert result.data["link"]["path"] == "/admin/customers"
