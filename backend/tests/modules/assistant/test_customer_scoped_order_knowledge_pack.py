from __future__ import annotations

from app.modules.assistant.expert_knowledge_pack import EXPERT_KNOWLEDGE_PACK_BY_KEY
from app.modules.assistant.workflow_help import WORKFLOW_HELP_SEEDS


def test_customer_scoped_order_knowledge_pack_contains_required_entries() -> None:
    required_keys = {
        "customer_orders_tab",
        "customer_scoped_order_workspace",
        "customer_order_create_from_customer",
        "customer_contract_register_from_customer",
    }

    assert required_keys.issubset(set(EXPERT_KNOWLEDGE_PACK_BY_KEY))
    for key in required_keys:
        pack = EXPERT_KNOWLEDGE_PACK_BY_KEY[key]
        assert pack.facts
        assert all(fact.source_basis for fact in pack.facts)


def test_customer_scoped_order_workflow_captures_route_aliases_and_current_steps() -> None:
    workflow = WORKFLOW_HELP_SEEDS["customer_scoped_order_create"]

    assert workflow.route_path == "/admin/customers/order-workspace"
    assert workflow.route_aliases == ("/admin/customers/new-plan",)
    assert workflow.entry_points == (
        "Customers workspace",
        "Selected customer detail",
        "Orders tab",
        "New order",
        "Edit existing order",
    )
    assert [step.step_key for step in workflow.steps] == [
        "order-details",
        "order-scope-documents",
        "planning-record-overview",
        "planning-record-documents",
        "shift-plan",
        "series-exceptions",
    ]
    assert workflow.steps[0].creates_or_updates == ("CustomerOrder",)
    assert "listCustomerOrders" in workflow.steps[0].api_functions
    assert "generateShiftSeries" in workflow.steps[-1].api_functions
    assert workflow.steps[-1].page_id == "C-02"
    assert all(step.source_basis for step in workflow.steps)
