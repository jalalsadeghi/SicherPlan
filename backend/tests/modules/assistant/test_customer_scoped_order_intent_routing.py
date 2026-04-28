from __future__ import annotations

from app.modules.assistant.retrieval_planner import build_retrieval_plan


def test_customer_page_context_promotes_order_question_to_customer_scoped_flow() -> None:
    plan = build_retrieval_plan(
        message="How do I create a new order for this customer?",
        route_context={
            "page_id": "C-01",
            "path": "/admin/customers",
            "route_name": "SicherPlanCustomers",
            "query": {"customer_id": "cust-1", "tab": "orders"},
        },
    )

    assert plan.workflow_intent == "customer_scoped_order_create"
    assert plan.workflow_variant == "customer_order_from_customer_page"
    assert {"C-01", "C-02", "P-04"}.issubset(set(plan.likely_page_ids))


def test_customer_page_context_promotes_contract_question_to_customer_scoped_flow() -> None:
    plan = build_retrieval_plan(
        message="Wie registriere ich einen Vertrag beim Kunden?",
        route_context={
            "page_id": "C-01",
            "path": "/admin/customers",
            "route_name": "SicherPlanCustomers",
            "query": {"customer_id": "cust-1", "tab": "orders"},
        },
    )

    assert plan.workflow_intent == "customer_scoped_order_create"
    assert plan.workflow_variant == "customer_contract_register_from_customer"
    assert "C-02" in plan.likely_page_ids


def test_general_order_management_question_keeps_canonical_planning_route() -> None:
    plan = build_retrieval_plan(
        message="Wie verwalte ich alle Aufträge?",
        route_context={
            "page_id": "C-01",
            "path": "/admin/customers",
            "route_name": "SicherPlanCustomers",
            "query": {"customer_id": "cust-1", "tab": "orders"},
        },
    )

    assert plan.workflow_intent != "customer_scoped_order_create"
    assert "P-02" in plan.likely_page_ids
