from __future__ import annotations

from app.modules.assistant.schemas import AssistantMessageCreate
from tests.modules.assistant.test_how_to_employee_create_exact_ui import (
    _GroundedCapturingProvider,
    _context,
    _repository,
    _service,
)


def test_contract_question_uses_grounded_provider_answer_without_inventing_contract_page() -> None:
    repository = _repository()
    provider = _GroundedCapturingProvider(
        answer=(
            "Ein eigenständiger Contract-Workspace ist in dieser Repository-Version nicht verifiziert. "
            "Nutzen Sie Platform Services für dokumentzentrierte Vorgänge und prüfen Sie je nach Kontext "
            "Customers oder Orders & Planning Records."
        )
    )
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
        AssistantMessageCreate(message="Wie registriere ich einen neuen Vertrag?"),
        _context("assistant.chat.access"),
    )

    assert provider.call_count == 1
    assert response.answer == provider.answer
    assert "standalone Contract page" not in response.answer
    assert response.rag_trace is not None
    assert response.rag_trace.retrieval_plan["workflow_intent"] == "contract_or_document_register"
    assert response.rag_trace.content_bearing_source_count >= 1
    assert response.source_basis
    assert any(item.page_id in {"PS-01", "C-01", "P-02"} for item in response.source_basis)
