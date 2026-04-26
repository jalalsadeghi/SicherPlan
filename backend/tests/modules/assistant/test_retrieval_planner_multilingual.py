from __future__ import annotations

from app.modules.assistant.retrieval_planner import build_retrieval_plan


def test_persian_customer_create_maps_to_customer_workspace_without_dashboard_bias() -> None:
    plan = build_retrieval_plan(
        message="چطور باید مشتری ثبت کنم؟",
        route_context={"page_id": "F-02", "path": "/admin/dashboard"},
    )

    assert plan.workflow_intent == "customer_create"
    assert plan.likely_page_ids[0] == "C-01"
    assert "F-02" not in plan.likely_page_ids
    assert "customers" in plan.likely_module_keys
    assert "customer" in plan.expanded_query


def test_persian_customer_plan_maps_to_customer_and_planning_pages() -> None:
    plan = build_retrieval_plan(
        message="چطور میتونم یک پلن جدید برای مشتری ثبت کنم؟",
        route_context={"page_id": "F-02", "path": "/admin/dashboard"},
    )

    assert plan.workflow_intent == "customer_plan_create"
    assert {"C-01", "P-02"}.issubset(set(plan.likely_page_ids))
    assert "P-03" in plan.likely_page_ids
    assert "planning" in plan.likely_module_keys


def test_persian_contract_registration_maps_to_platform_customer_or_order_context() -> None:
    plan = build_retrieval_plan(
        message="چطوری یک قرارداد جدید ثبت کنم؟",
        route_context={"page_id": "F-02", "path": "/admin/dashboard"},
    )

    assert plan.workflow_intent == "contract_registration"
    assert "PS-01" in plan.likely_page_ids
    assert "C-01" in plan.likely_page_ids
    assert "P-02" in plan.likely_page_ids
    assert "platform_services" in plan.likely_module_keys


def test_german_customer_order_maps_to_order_or_customer_plan_pages() -> None:
    plan = build_retrieval_plan(
        message="Wie erstelle ich einen neuen Auftrag für einen Kunden?",
        route_context={"page_id": "E-01", "path": "/admin/employees"},
    )

    assert plan.workflow_intent in {"order_create", "customer_plan_create"}
    assert "P-02" in plan.likely_page_ids
    assert "C-01" in plan.likely_page_ids
    assert "E-01" not in plan.likely_page_ids
