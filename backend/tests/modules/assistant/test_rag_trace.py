from __future__ import annotations

from app.modules.assistant.schemas import AssistantMessageCreate
from tests.modules.assistant.test_how_to_employee_create_exact_ui import (
    _GroundedCapturingProvider,
    _context,
    _repository,
    _service,
)


def test_in_scope_response_includes_rag_trace_and_source_basis() -> None:
    repository = _repository()
    provider = _GroundedCapturingProvider(answer="Grounded employee guidance")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )

    response = _service(repository, provider, provider_mode="openai").add_message(
        conversation.id,
        AssistantMessageCreate(message="How do I create a new Employee?"),
        _context("assistant.chat.access", "employees.employee.read", "employees.employee.write"),
    )

    assert response.rag_trace is not None
    assert response.rag_trace.provider_called is True
    assert response.rag_trace.provider_mode == "openai"
    assert response.rag_trace.retrieval_executed is True
    assert response.rag_trace.grounding_attached is True
    assert response.rag_trace.grounding_source_count > 0
    assert response.rag_trace.content_bearing_source_count > 0
    assert response.rag_trace.source_type_counts.get("ui_action", 0) >= 1
    assert response.source_basis
    assert any(item.source_type == "page_help_manifest" for item in response.source_basis)
    assert provider.requests[0].grounding_context is not None
