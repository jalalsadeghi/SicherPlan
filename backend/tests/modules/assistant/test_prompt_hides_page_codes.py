from __future__ import annotations

from app.modules.assistant.prompt_builder import (
    AssistantAuthContextSummary,
    build_assistant_prompt,
)


def test_prompt_instructs_model_to_hide_internal_page_codes_in_main_answer() -> None:
    prompt = build_assistant_prompt(
        user_message="Wie prüfe ich das im Mitarbeiter-Workspace?",
        detected_language="de",
        response_language="de",
        auth_context=AssistantAuthContextSummary(
            tenant_scope="current tenant only",
            scope_kind="tenant",
            current_user_type="internal",
            role_keys=["tenant_admin"],
            permission_keys=["assistant.chat.access"],
        ),
        route_context={"page_id": "E-01", "path": "/admin/employees"},
        knowledge_chunks=[],
        available_tools=[],
        conversation_messages=[],
    )

    assert "do not show internal page IDs" in prompt.system_instructions
    assert "Use human-readable page or workspace names" in prompt.system_instructions
    assert "Do not invent page routes" in prompt.system_instructions
    assert "Use page IDs only inside source_basis or debug-oriented fields" in prompt.system_instructions

