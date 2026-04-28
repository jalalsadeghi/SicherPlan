from __future__ import annotations

from pathlib import Path

from app.modules.assistant.schemas import AssistantMessageCreate
from tests.modules.assistant.golden_qa_support import GoldenExpertProvider, build_golden_service
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _context


def test_customer_order_prompt_capture_contains_route_context_links_and_guidance(tmp_path: Path) -> None:
    provider = GoldenExpertProvider()
    service = build_golden_service(tmp_path, provider)
    conversation = service.repository.create_conversation(  # type: ignore[attr-defined]
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="Wie kann ich von der Kundenseite aus einen Auftrag registrieren?",
            route_context={
                "path": "/admin/customers",
                "route_name": "SicherPlanCustomers",
                "page_id": "C-01",
                "query": {"customer_id": "customer-1", "tab": "orders"},
            },
        ),
        _context(
            "assistant.chat.access",
            "customers.customer.read",
            "customers.customer.write",
            "planning.order.read",
            "planning.order.write",
            "planning.record.read",
            "planning.record.write",
            "planning.shift.read",
            "planning.shift.write",
            "planning.staffing.read",
        ),
    )

    assert response.out_of_scope is False
    request = provider.requests[-1]
    assert request.system_instructions != request.user_message
    assert "Do not answer only with Operations & Planning for customer-page order or contract questions" in request.system_instructions
    assert "standalone Contract module" in request.system_instructions
    assert request.route_context is not None
    assert request.route_context["query"] == {"customer_id": "customer-1", "tab": "orders"}
    assert request.grounding_context is not None
    assert request.grounding_context["retrieval_plan"]["workflow_intent"] == "customer_scoped_order_create"
    assert request.grounding_context["retrieval_plan"]["route_context_signals"]["customer_orders_tab"] is True
    assert any(
        source.get("source_type") == "knowledge_chunk"
        and "customer_scoped_order_create" in (source.get("facts", {}).get("workflow_keys") or [])
        for source in request.grounding_context["sources"]
        if isinstance(source, dict) and isinstance(source.get("facts"), dict)
    )
    assert any(
        source.get("page_id") in {"C-01", "C-02"} and source.get("source_type") in {"knowledge_chunk", "page_help_manifest", "workflow"}
        for source in request.grounding_context["sources"]
        if isinstance(source, dict)
    )
    allowed_links = [
        source["facts"]["link"]
        for source in request.grounding_context["sources"]
        if source.get("source_type") == "allowed_navigation_link" and isinstance(source.get("facts"), dict) and isinstance(source["facts"].get("link"), dict)
    ]
    paths = {item["path"] for item in allowed_links}
    assert "/admin/customers?customer_id=customer-1&tab=orders" in paths
    assert "/admin/customers/order-workspace?customer_id=customer-1" in paths
