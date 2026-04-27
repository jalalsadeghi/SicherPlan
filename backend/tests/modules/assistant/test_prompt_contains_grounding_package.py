from __future__ import annotations

from app.modules.assistant.openai_client import OpenAIResponsesProvider
from app.modules.assistant.provider import AssistantProviderRequest


def test_openai_input_contains_grounding_package_and_query_expansion() -> None:
    request = AssistantProviderRequest(
        conversation_id="conv-1",
        user_message="Wie registriere ich einen neuen Vertrag?",
        system_instructions="System instructions",
        response_language="de",
        detected_language="de",
        grounding_context={
            "query_expansion": {
                "original_query": "Wie registriere ich einen neuen Vertrag?",
                "detected_terms": ["contract", "document"],
                "expanded_terms_en": ["contract", "agreement", "document", "attachment"],
                "expanded_terms_de": ["Vertrag", "Dokument", "Anhang"],
                "likely_page_ids": ["PS-01", "C-01", "P-02"],
                "likely_module_keys": ["platform_services", "customers", "planning"],
            },
            "sources": [
                {
                    "source_type": "workflow",
                    "source_name": "contract_or_document_register",
                    "page_id": "PS-01",
                    "module_key": "platform_services",
                    "title": "Vertrag oder Dokument im richtigen Fachkontext registrieren",
                    "content": "Contract registration is document-centered and context-dependent.",
                    "facts": {"workflow_key": "contract_or_document_register"},
                    "score": 92.5,
                    "why_selected": ["exact workflow manifest", "page match PS-01"],
                }
            ],
        },
        recent_messages=[{"role": "assistant", "content": "Previous grounded reply."}],
        max_input_chars=12000,
    )

    messages = OpenAIResponsesProvider._build_input(request)

    assert len(messages) >= 3
    grounding_message = next(item for item in messages if item.get("role") == "system" and "Grounding context package" in item.get("content", ""))
    assert "query_expansion" in grounding_message["content"]
    assert "contract_or_document_register" in grounding_message["content"]
    assert "Vertrag oder Dokument" in grounding_message["content"]
    assert messages[-1]["content"] == "Wie registriere ich einen neuen Vertrag?"
    assert any(item.get("content") == "Previous grounded reply." for item in messages if item.get("role") == "assistant")
