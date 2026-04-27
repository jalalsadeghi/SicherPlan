from __future__ import annotations

from app.modules.assistant.schemas import AssistantMessageCreate
from tests.modules.assistant.test_how_to_employee_create_exact_ui import (
    _GroundedCapturingProvider,
    _context,
    _repository,
    _service,
)


def test_contract_registration_answer_includes_source_basis_and_expected_pages() -> None:
    repository = _repository()
    provider = _GroundedCapturingProvider(
        answer="Ein eigenständiger Vertrags-Workflow ist nicht verifiziert. Verifizierte Hinweise zeigen auf Platform Services für Dokumente sowie auf Kunden- und Auftragskontext."
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

    assert response.rag_trace is not None
    assert response.rag_trace.retrieval_plan["workflow_intent"] == "contract_or_document_register"
    likely_page_ids = set(response.rag_trace.retrieval_plan["likely_page_ids"])
    assert {"PS-01", "C-01", "P-02"}.issubset(likely_page_ids)
    assert response.source_basis
    source_page_ids = {item.page_id for item in response.source_basis if item.page_id}
    assert source_page_ids.intersection({"PS-01", "C-01", "P-02"})
    assert "eigenständiger Vertrags-Workflow ist nicht verifiziert" in response.answer
