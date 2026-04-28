from __future__ import annotations

from pathlib import Path

from tests.modules.assistant.golden_qa_support import GoldenQaCase, run_case


def test_customer_order_regression_no_longer_falls_back_to_old_global_route(tmp_path: Path) -> None:
    result = run_case(
        tmp_path / "customer-order-regression",
        case=GoldenQaCase(
            id="de_customer_order_regression",
            language="de",
            question="Wie kann ich von der Kundenseite aus einen Auftrag registrieren?",
            route_context={
                "path": "/admin/customers",
                "route_name": "SicherPlanCustomers",
                "page_id": "C-01",
                "query": {"customer_id": "customer-1", "tab": "orders"},
            },
            expected_intent="customer_scoped_order_create",
            expected_pages=["C-01", "C-02", "P-04"],
            required_concepts=[
                "ausgewählten kunden",
                "orders-tab",
                "New order",
                "Order Workspace",
            ],
            forbidden_patterns=["nur operations & planning"],
            requires_source_basis=True,
            min_content_bearing_sources=3,
            expected_links=["Orders-Tab des Kunden", "Order Workspace"],
        ),
    )

    assert result.passed, result.failures
