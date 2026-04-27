from __future__ import annotations

from app.modules.assistant.grounding import AssistantGroundingContext, AssistantGroundingSource
from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from tests.modules.assistant.test_operational_diagnostic_tool_loop import _context
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


def _grounding() -> AssistantGroundingContext:
    return AssistantGroundingContext(
        detected_language="de",
        response_language="de",
        auth_summary={"scope_kind": "tenant"},
        retrieval_plan={
            "intent_category": "workflow_how_to",
            "likely_page_ids": ["C-01"],
            "likely_module_keys": ["customers"],
        },
        sources=[
            AssistantGroundingSource(
                source_id=f"source-{index}",
                source_type="knowledge_chunk",
                source_name=f"source-{index}",
                page_id="C-01",
                module_key="customers",
                title=f"Title {index}",
                content=("Kunde " * 220),
                facts={"index": index, "content": "x" * 600},
                score=20 - index,
                content_bearing=True,
                verified=True,
                permission_checked=True,
            )
            for index in range(8)
        ],
    )


def test_provider_request_never_uses_output_cap_below_structured_minimum() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-4o",
            min_structured_output_tokens=800,
            max_output_tokens=200,
            continuation_max_output_tokens=300,
            max_provider_input_tokens=2400,
            max_total_grounding_chars=1500,
            max_grounding_chars_per_source=260,
            max_recent_messages_for_model=2,
        ),
        repository=repository,
        provider=MockAssistantProvider(),
    )

    request = service._build_provider_request(  # noqa: SLF001
        conversation=conversation,
        cleaned_message="Wie registriere ich einen Kunden?",
        route_context=None,
        detected_language="de",
        response_language="de",
        actor=_context(),
        grounding_context=_grounding(),
    )

    assert request.max_output_tokens >= 800
    assert request.max_output_tokens != 200


def test_continuation_request_also_honors_structured_output_minimum() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-4o",
            min_structured_output_tokens=800,
            max_output_tokens=1200,
            continuation_max_output_tokens=200,
        ),
        repository=repository,
        provider=MockAssistantProvider(),
    )

    request = service._build_provider_request(  # noqa: SLF001
        conversation=conversation,
        cleaned_message="Wie registriere ich einen Kunden?",
        route_context=None,
        detected_language="de",
        response_language="de",
        actor=_context(),
        grounding_context=_grounding(),
        provider_tool_results=[
            {
                "type": "function_call_output",
                "call_id": "call-1",
                "output": '{"ok": true}',
            }
        ],
        previous_output_items=[
            {
                "type": "function_call",
                "id": "fc-1",
                "call_id": "call-1",
                "name": "assistant_search_workflow_help",
                "arguments": '{"query":"kunde"}',
            }
        ],
    )

    assert request.max_output_tokens >= 800
    assert request.metadata["continuation_mode"] == "stateless"
