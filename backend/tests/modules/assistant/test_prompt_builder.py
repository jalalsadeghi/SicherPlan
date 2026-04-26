from __future__ import annotations

from app.modules.assistant.prompt_builder import (
    ASSISTANT_PROMPT_POLICY_VERSION,
    AssistantAuthContextSummary,
    AssistantMessageContext,
    AssistantToolDefinition,
    AssistantToolResultSummary,
    build_assistant_prompt,
)
from app.modules.assistant.schemas import AssistantKnowledgeChunkResult


def _auth_summary() -> AssistantAuthContextSummary:
    return AssistantAuthContextSummary(
        tenant_scope="current tenant only",
        scope_kind="tenant",
        current_user_type="internal",
        role_keys=["tenant_admin"],
        permission_keys=["assistant.chat.access"],
    )


def _knowledge_chunk(content: str = "Planning release instructions for page P-04.") -> AssistantKnowledgeChunkResult:
    return AssistantKnowledgeChunkResult(
        chunk_id="chunk-1",
        source_id="source-1",
        source_name="Planning Manual",
        source_type="repository_docs",
        title="Release shifts",
        content=content,
        language_code="en",
        module_key="planning",
        page_id="P-04",
        role_keys=[],
        permission_keys=[],
        score=12.0,
        rank=1,
        matched_by="lexical",
    )


def test_system_prompt_contains_no_sql_rule() -> None:
    prompt = build_assistant_prompt(
        user_message="Why is Markus not visible?",
        detected_language="en",
        response_language="en",
        auth_context=_auth_summary(),
        route_context=None,
        knowledge_chunks=[],
        available_tools=[],
        conversation_messages=[],
    )

    assert "must not generate SQL" in prompt.system_instructions
    assert "Never ask the user to run SQL" in prompt.system_instructions


def test_system_prompt_contains_no_write_actions_rule() -> None:
    prompt = build_assistant_prompt(
        user_message="release this shift",
        detected_language="en",
        response_language="en",
        auth_context=_auth_summary(),
        route_context=None,
        knowledge_chunks=[],
        available_tools=[],
        conversation_messages=[],
    )

    assert "must not perform write actions" in prompt.system_instructions
    assert "Write actions are not available" in prompt.system_instructions


def test_system_prompt_forbids_guessing_exact_ui_labels() -> None:
    prompt = build_assistant_prompt(
        user_message="How do I create a new employee?",
        detected_language="en",
        response_language="en",
        auth_context=_auth_summary(),
        route_context={"page_id": "E-01", "path": "/admin/employees"},
        knowledge_chunks=[],
        available_tools=[],
        conversation_messages=[],
    )

    assert "do not invent button names" in prompt.system_instructions
    assert "Use verified page-help and UI-action tool output only" in prompt.system_instructions
    assert "Create Employee or New Employee" in prompt.system_instructions


def test_system_prompt_contains_same_language_rule() -> None:
    prompt = build_assistant_prompt(
        user_message="Warum ist Markus nicht sichtbar?",
        detected_language="de",
        response_language="de",
        auth_context=_auth_summary(),
        route_context=None,
        knowledge_chunks=[],
        available_tools=[],
        conversation_messages=[],
    )

    assert "response_language: de" in prompt.system_instructions
    assert "Use the same language" in prompt.system_instructions
    assert "Keep technical SicherPlan platform terms unchanged" in prompt.system_instructions


def test_system_prompt_contains_no_inaccessible_record_existence_rule() -> None:
    prompt = build_assistant_prompt(
        user_message="Is there a hidden payroll record?",
        detected_language="en",
        response_language="en",
        auth_context=_auth_summary(),
        route_context=None,
        knowledge_chunks=[],
        available_tools=[],
        conversation_messages=[],
    )

    assert "must not infer or confirm existence of inaccessible records" in prompt.system_instructions


def test_prompt_includes_knowledge_chunks_in_capped_truncated_way() -> None:
    prompt = build_assistant_prompt(
        user_message="How do I release a shift?",
        detected_language="en",
        response_language="en",
        auth_context=_auth_summary(),
        route_context=None,
        knowledge_chunks=[
            _knowledge_chunk("Planning release " * 80),
            AssistantKnowledgeChunkResult.model_validate(_knowledge_chunk().model_dump() | {"chunk_id": "chunk-2", "rank": 2}),
        ],
        available_tools=[],
        conversation_messages=[],
        max_context_chunks=1,
        max_input_chars=240,
    )

    assert '"source_name": "Planning Manual"' in prompt.system_instructions
    assert '"rank": 1' in prompt.system_instructions
    assert '"chunk_id": "chunk-2"' not in prompt.system_instructions
    assert "..." in prompt.system_instructions


def test_prompt_marks_route_context_as_informational_only() -> None:
    prompt = build_assistant_prompt(
        user_message="Why is Markus not visible?",
        detected_language="en",
        response_language="en",
        auth_context=_auth_summary(),
        route_context={"path": "/planning", "page_id": "P-04"},
        knowledge_chunks=[],
        available_tools=[],
        conversation_messages=[],
    )

    assert "Route context is informational only" in prompt.system_instructions
    assert '"page_id": "P-04"' in prompt.system_instructions


def test_prompt_excludes_secrets_and_sensitive_fields() -> None:
    prompt = build_assistant_prompt(
        user_message="My reset token is eyJabc.def.ghi and api key is sk-secret12345",
        detected_language="en",
        response_language="en",
        auth_context=_auth_summary(),
        route_context={"authorization": "Bearer eyJabc.def.ghi", "iban": "DE123456789"},
        knowledge_chunks=[],
        available_tools=[],
        conversation_messages=[],
        tool_results=[
            AssistantToolResultSummary(
                tool_name="diagnostics.lookup",
                summary={
                    "password_hash": "hash",
                    "refresh_token": "raw",
                    "note": "visible",
                },
            )
        ],
    )

    assert "sk-secret12345" not in prompt.user_message
    assert "eyJabc.def.ghi" not in prompt.user_message
    assert '"authorization": "[REDACTED]"' in prompt.system_instructions
    assert '"iban": "[REDACTED]"' in prompt.system_instructions
    assert '"password_hash": "[REDACTED]"' in prompt.system_instructions
    assert '"refresh_token": "[REDACTED]"' in prompt.system_instructions


def test_prompt_includes_structured_response_requirements() -> None:
    prompt = build_assistant_prompt(
        user_message="Why is Markus not visible?",
        detected_language="en",
        response_language="en",
        auth_context=_auth_summary(),
        route_context=None,
        knowledge_chunks=[],
        available_tools=[],
        conversation_messages=[],
    )

    assert "Structured response contract" in prompt.system_instructions
    assert "answer, confidence, out_of_scope, diagnosis, links, missing_permissions, next_steps, tool_trace_id" in prompt.system_instructions


def test_prompt_includes_only_available_tool_names_and_metadata() -> None:
    prompt = build_assistant_prompt(
        user_message="Why is Markus not visible?",
        detected_language="en",
        response_language="en",
        auth_context=_auth_summary(),
        route_context=None,
        knowledge_chunks=[],
        available_tools=[
            AssistantToolDefinition(
                name="assistant.employee.lookup",
                description="Lookup employee app visibility",
                required_permissions=["assistant.diagnostics.read"],
            )
        ],
        conversation_messages=[],
    )

    assert "assistant.employee.lookup" in prompt.system_instructions
    assert "assistant.diagnostics.read" in prompt.system_instructions
    assert "assistant.payroll.write" not in prompt.system_instructions


def test_prompt_metadata_includes_policy_version() -> None:
    prompt = build_assistant_prompt(
        user_message="Why is Markus not visible?",
        detected_language="en",
        response_language="en",
        auth_context=_auth_summary(),
        route_context=None,
        knowledge_chunks=[],
        available_tools=[],
        conversation_messages=[AssistantMessageContext(role="user", content="Earlier question")],
    )

    assert prompt.policy_version == ASSISTANT_PROMPT_POLICY_VERSION
    assert prompt.metadata["prompt_policy_version"] == ASSISTANT_PROMPT_POLICY_VERSION
