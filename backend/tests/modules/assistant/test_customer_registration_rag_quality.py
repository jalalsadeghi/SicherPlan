from __future__ import annotations

from app.modules.assistant.schemas import AssistantMessageCreate
from tests.modules.assistant.test_how_to_employee_create_exact_ui import (
    _GroundedCapturingProvider,
    _context,
    _repository,
    _service,
)


def test_customer_registration_uses_content_bearing_workflow_sources_not_route_only() -> None:
    repository = _repository()
    provider = _GroundedCapturingProvider(answer="Verifizierte Workflow-Hinweise zeigen auf den Kunden-Workspace und die dortigen Stammdaten- und Abrechnungsdaten.")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )

    response = _service(repository, provider, provider_mode="openai").add_message(
        conversation.id,
        AssistantMessageCreate(message="Bitte erklären Sie mir genau, wie ich einen Kunden registrieren kann."),
        _context("assistant.chat.access", "customers.customer.read"),
    )

    assert response.out_of_scope is False
    assert response.rag_trace is not None
    assert response.rag_trace.retrieval_plan["workflow_intent"] == "customer_create"
    assert response.rag_trace.content_bearing_source_count > 0
    assert response.source_basis
    assert any(item.source_type == "workflow_help" for item in response.source_basis)
    assert not all(item.source_type == "page_route" for item in response.source_basis)
