from __future__ import annotations

from app.modules.assistant.prompt_builder import (
    AssistantAuthContextSummary,
    AssistantToolDefinition,
    build_assistant_prompt,
)
from app.modules.assistant.grounding import AssistantGroundingContext, AssistantGroundingSource


def test_prompt_includes_grounding_context_and_shallow_hint_warning() -> None:
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
                "likely_page_ids": ["PS-01", "C-01", "P-02", "S-01"],
            },
            sources=[
                AssistantGroundingSource(
                    source_type="page_route",
                    source_name="Platform Services",
                    page_id="PS-01",
                    title="Platform Services",
                    content="/admin/platform-services",
                )
            ],
            missing_context=["content_bearing_sources"],
        ),
        available_tools=[AssistantToolDefinition(name="assistant.search_workflow_help")],
        conversation_messages=[],
    )

    assert "Grounding context" in payload.system_instructions
    assert "RAG answer" in payload.system_instructions
    assert "page ID, route name, page title, or generic page hint alone is not enough" in payload.system_instructions
    assert "Only shallow page hints were found" in payload.system_instructions
