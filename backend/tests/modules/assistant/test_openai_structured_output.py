from __future__ import annotations

from types import SimpleNamespace

from app.modules.assistant.openai_client import OpenAIProviderRuntime, OpenAIResponsesProvider
from app.modules.assistant.provider import AssistantProviderRequest


def _request() -> AssistantProviderRequest:
    return AssistantProviderRequest(
        conversation_id="conv-1",
        user_message="Why is Markus not visible in the employee app?",
        system_instructions="Use the same language.",
        response_language="en",
        detected_language="en",
        route_context=None,
        recent_messages=[],
        knowledge_chunks=[],
        available_tools=[{"type": "function", "function": {"name": "search_docs"}}],
        max_tool_calls=8,
        max_input_chars=12000,
    )


def test_openai_provider_parses_tool_calls_from_response() -> None:
    response = SimpleNamespace(
        output_parsed={
            "answer": "OpenAI answer",
            "confidence": "low",
            "out_of_scope": False,
            "diagnosis": [],
            "links": [],
            "missing_permissions": [],
            "next_steps": [],
            "tool_trace_id": None,
        },
        output=[
            SimpleNamespace(
                type="function_call",
                id="fc-1",
                name="search_docs",
                arguments='{"query":"Markus"}',
                call_id="call-1",
            )
        ],
        usage=None,
        output_text="OpenAI answer",
        status="completed",
    )

    class _Responses:
        def parse(self, **kwargs):
            self.kwargs = kwargs
            return response

    class _Client:
        def __init__(self):
            self.responses = _Responses()

    client = _Client()
    provider = OpenAIResponsesProvider(
        OpenAIProviderRuntime(
            api_key="test-key",
            model_name="gpt-5.5-mini",
            timeout_seconds=45,
            store_responses=False,
            max_input_chars=12000,
        ),
        client_factory=lambda **kwargs: client,
    )
    result = provider.generate(_request())

    assert result.requested_tool_calls == [
        {
            "id": "fc-1",
            "name": "search_docs",
            "arguments": '{"query":"Markus"}',
            "call_id": "call-1",
        }
    ]
    assert client.responses.kwargs["tools"] == [{"type": "function", "function": {"name": "search_docs"}}]
