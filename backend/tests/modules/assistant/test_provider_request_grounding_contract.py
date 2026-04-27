from __future__ import annotations

from pathlib import Path

from tests.modules.assistant.golden_qa_support import GoldenExpertProvider, build_golden_service
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _context
from app.modules.assistant.schemas import AssistantMessageCreate


def test_provider_request_contains_grounding_contract_for_in_scope_question(tmp_path: Path) -> None:
    provider = GoldenExpertProvider()
    service = build_golden_service(tmp_path, provider)
    conversation = service.repository.create_conversation(  # type: ignore[attr-defined]
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="How do I create a new customer?"),
        _context(
            "assistant.chat.access",
            "customers.customer.read",
            "customers.customer.write",
            "planning.order.read",
            "planning.record.read",
        ),
    )

    assert response.out_of_scope is False
    assert provider.requests
    request = provider.requests[0]

    assert request.system_instructions != request.user_message
    assert "For in-scope questions, answer using the provided RAG grounding context." in request.system_instructions
    assert "Use source_basis only for retrieved grounded sources" in request.system_instructions
    assert request.grounding_context is not None
    assert request.grounding_context["sources"]
    assert any(source.get("content_bearing") for source in request.grounding_context["sources"])
    assert any(
        source.get("source_type") in {"knowledge_chunk", "workflow", "page_help_manifest"}
        for source in request.grounding_context["sources"]
    )
