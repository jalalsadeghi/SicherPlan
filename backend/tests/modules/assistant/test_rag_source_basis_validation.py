from __future__ import annotations

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from tests.modules.assistant.test_how_to_employee_create_exact_ui import (
    _GroundedCapturingProvider,
    _context,
    _repository,
    _service,
)


class _InventingSourceBasisProvider(_GroundedCapturingProvider):
    def __init__(self, answer: str) -> None:
        super().__init__(answer=answer)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        self.call_count += 1
        return AssistantProviderResult(
            final_response={
                "answer": self.answer,
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
                "source_basis": [
                    {
                        "source_type": "workflow_help",
                        "source_name": "contract_or_document_register",
                        "page_id": "PS-01",
                        "title": "Vertrag oder Dokument im richtigen Fachkontext registrieren",
                        "evidence": "Invented by model and should be replaced by backend-safe evidence.",
                    },
                    {
                        "source_type": "workflow_help",
                        "source_name": "invented_contract_workspace",
                        "page_id": "CONTRACT-01",
                        "title": "Contract Workspace",
                        "evidence": "This source does not exist.",
                    },
                ],
            },
            raw_text=self.answer,
        )


def test_model_proposed_source_basis_is_validated_and_invented_sources_removed() -> None:
    repository = _repository()
    provider = _InventingSourceBasisProvider(
        answer="Ein eigenständiger Vertragsbereich ist nicht verifiziert. Verwenden Sie die verifizierten Dokument- und Kundenkontexte."
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

    assert response.source_basis
    assert {item.page_id for item in response.source_basis if item.page_id}.issubset({"PS-01", "C-01", "P-02", "S-01"})
    assert all(item.page_id != "CONTRACT-01" for item in response.source_basis)
    assert all("Invented by model" not in item.evidence for item in response.source_basis)


def test_exact_ui_claims_without_verified_page_help_drop_confidence() -> None:
    repository = _repository()
    provider = _GroundedCapturingProvider(
        answer="Use the exact button label New Order in Orders & Planning Records."
    )
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
        AssistantMessageCreate(message="I want to create a new order. Tell me the exact button."),
        _context("assistant.chat.access", "planning.order.read", "planning.record.read"),
    )

    assert response.confidence == "low"
    assert not any(item.source_type == "page_help_manifest" and item.page_id == "P-02" for item in response.source_basis)
