from __future__ import annotations

from app.modules.assistant.grounding import AssistantGroundingContext, AssistantGroundingSource
from app.modules.assistant.prompt_builder import (
    AssistantAuthContextSummary,
    AssistantToolDefinition,
    build_assistant_prompt,
)


def test_prompt_quality_includes_grounding_requirements_and_source_basis_contract() -> None:
    payload = build_assistant_prompt(
        user_message="Wie registriere ich einen neuen Vertrag?",
        detected_language="de",
        response_language="de",
        auth_context=AssistantAuthContextSummary(
            tenant_scope="current tenant only",
            scope_kind="tenant",
            current_user_type="internal",
        ),
        route_context={"page_id": "PS-01"},
        knowledge_chunks=[],
        grounding_context=AssistantGroundingContext(
            detected_language="de",
            response_language="de",
            auth_summary={"tenant_scope": "current tenant only"},
            route_context={"page_id": "PS-01"},
            retrieval_plan={
                "intent_category": "workflow_how_to",
                "workflow_intent": "contract_or_document_register",
                "likely_page_ids": ["PS-01", "C-01", "P-02"],
            },
            query_expansion={
                "detected_terms": ["contract"],
                "expanded_terms_en": ["contract", "agreement"],
                "expanded_terms_de": ["vertrag", "dokument"],
            },
            sources=[
                AssistantGroundingSource(
                    source_id="workflow:contract_or_document_register:contract_or_document_register",
                    source_type="workflow",
                    source_name="contract_or_document_register",
                    page_id="PS-01",
                    module_key="platform_services",
                    title="Vertrag oder Dokument im richtigen Fachkontext registrieren",
                    content="Nutzen Sie Platform Services als generischen Dokumentkontext.",
                    why_selected=["exact workflow manifest"],
                    content_bearing=True,
                    verified=True,
                    permission_checked=True,
                )
            ],
            missing_context=[],
        ),
        available_tools=[AssistantToolDefinition(name="assistant.search_workflow_help")],
        conversation_messages=[],
    )

    instructions = payload.system_instructions
    assert "You are the SicherPlan AI Assistant." in instructions
    assert "For in-scope questions, answer using the provided RAG grounding context." in instructions
    assert "If a precise claim is not supported by grounding context, say that it is not verified." in instructions
    assert "Use source_basis only for retrieved grounded sources" in instructions
    assert "You may include source_basis" in instructions
    assert '"source_id": "workflow:contract_or_document_register:contract_or_document_register"' in instructions
    assert '"expanded_terms_de"' in instructions
