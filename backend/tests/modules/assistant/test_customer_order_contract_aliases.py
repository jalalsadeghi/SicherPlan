from __future__ import annotations

from app.modules.assistant.lexicon import expand_assistant_query
from app.modules.assistant.retrieval_planner import build_retrieval_plan
from app.modules.assistant.workflow_help import detect_workflow_intent


def test_customer_scoped_order_aliases_map_to_customer_order_workspace_intent() -> None:
    assert detect_workflow_intent("How can I create an order from the customer page?").intent == "customer_scoped_order_create"
    assert detect_workflow_intent("Wie erstelle ich einen Auftrag direkt beim Kunden?").intent == "customer_scoped_order_create"
    assert detect_workflow_intent("چطور از صفحه مشتری Order ثبت کنم؟").intent == "customer_scoped_order_create"


def test_customer_contract_aliases_map_to_customer_scoped_flow_in_customer_context() -> None:
    assert detect_workflow_intent("Wie registriere ich einen Kundenvertrag im Kundenbereich?").intent == "customer_scoped_order_create"
    assert detect_workflow_intent("چطور قرارداد مشتری را از تب Orders ثبت کنم؟").intent == "customer_scoped_order_create"

    generic = build_retrieval_plan(
        message="Wie registriere ich einen neuen Vertrag?",
        route_context={"page_id": "F-02", "path": "/admin/dashboard"},
    )
    assert generic.workflow_intent == "contract_or_document_register"


def test_customer_scoped_order_query_expands_to_customer_workspace_and_staffing_handoff() -> None:
    expanded = expand_assistant_query(
        "Wie erstelle ich einen Auftrag direkt beim Kunden?",
        workflow_intent="customer_scoped_order_create",
    )

    assert {"C-01", "C-02", "P-04"}.issubset(set(expanded.likely_page_ids))
    assert {"customers", "planning"}.issubset(set(expanded.likely_module_keys))
