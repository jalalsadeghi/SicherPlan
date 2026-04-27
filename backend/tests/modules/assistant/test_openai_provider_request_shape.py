from __future__ import annotations

from types import SimpleNamespace

from app.modules.assistant.openai_client import OpenAIProviderRuntime, OpenAIResponsesProvider
from app.modules.assistant.provider import AssistantProviderRequest


def test_openai_provider_builds_expected_parse_request() -> None:
    response = SimpleNamespace(
        output_parsed={
            "answer": "provider ok",
            "confidence": "high",
            "out_of_scope": False,
            "diagnosis": [],
            "links": [],
            "missing_permissions": [],
            "next_steps": [],
            "tool_trace_id": None,
        },
        output=[],
        usage=None,
        output_text="provider ok",
        status="completed",
    )

    class _Responses:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def parse(self, **kwargs):
            self.calls.append(kwargs)
            return response

    class _Client:
        def __init__(self) -> None:
            self.responses = _Responses()

    client = _Client()
    provider = OpenAIResponsesProvider(
        OpenAIProviderRuntime(
            api_key="test-key",
            model_name="gpt-4o",
            timeout_seconds=45,
            store_responses=False,
            max_input_chars=12000,
        ),
        client_factory=lambda **kwargs: client,
    )

    provider.generate(
        AssistantProviderRequest(
            conversation_id="conv-1",
            user_message="How do I create a new order?",
            system_instructions="Return structured output.",
            response_language="en",
            detected_language="en",
            grounding_context={"sources": [{"page_id": "P-02", "source_type": "workflow"}]},
            recent_messages=[{"role": "assistant", "content": "Previous answer"}],
            available_tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "assistant.search_workflow_help",
                        "description": "Search verified workflow help.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                            },
                            "required": ["query"],
                        },
                    },
                }
            ],
            provider_tool_name_map={
                "assistant_search_workflow_help": "assistant.search_workflow_help",
            },
            max_tool_calls=8,
            max_input_chars=12000,
        )
    )

    assert len(client.responses.calls) == 1
    call = client.responses.calls[0]
    assert call["model"] == "gpt-4o"
    assert call["store"] is False
    assert call["text_format"].__name__ == "AssistantProviderStructuredOutput"
    assert call["tools"] == [
        {
            "type": "function",
            "name": "assistant_search_workflow_help",
            "description": "Search verified workflow help.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        }
    ]
    input_rows = call["input"]
    assert any(row.get("role") == "system" for row in input_rows)
    assert any(row.get("content") == "Previous answer" for row in input_rows if isinstance(row, dict))
    assert any("Grounding context package" in row.get("content", "") for row in input_rows if isinstance(row, dict))


def test_openai_provider_builds_previous_response_continuation_request() -> None:
    response = SimpleNamespace(
        output_parsed={
            "answer": "provider ok",
            "confidence": "high",
            "out_of_scope": False,
            "diagnosis": [],
            "links": [],
            "missing_permissions": [],
            "next_steps": [],
            "tool_trace_id": None,
        },
        output=[],
        usage=None,
        output_text="provider ok",
        status="completed",
    )

    class _Responses:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def parse(self, **kwargs):
            self.calls.append(kwargs)
            return response

    class _Client:
        def __init__(self) -> None:
            self.responses = _Responses()

    client = _Client()
    provider = OpenAIResponsesProvider(
        OpenAIProviderRuntime(
            api_key="test-key",
            model_name="gpt-4o",
            timeout_seconds=45,
            store_responses=True,
            max_input_chars=12000,
        ),
        client_factory=lambda **kwargs: client,
    )

    provider.generate(
        AssistantProviderRequest(
            conversation_id="conv-1",
            user_message="How do I create a new order?",
            system_instructions="Return structured output.",
            response_language="en",
            detected_language="en",
            continuation_tool_outputs=[
                {
                    "type": "function_call_output",
                    "call_id": "call-1",
                    "output": '{"ok": true}',
                }
            ],
            previous_response_id="resp-1",
            provider_tool_name_map={},
            max_tool_calls=8,
            max_input_chars=12000,
        )
    )

    call = client.responses.calls[0]
    assert call["previous_response_id"] == "resp-1"
    assert call["input"] == [
        {
            "type": "function_call_output",
            "call_id": "call-1",
            "output": '{"ok": true}',
        }
    ]
    assert not any(row.get("role") == "user" for row in call["input"] if isinstance(row, dict))


def test_openai_provider_builds_stateless_continuation_request() -> None:
    response = SimpleNamespace(
        output_parsed={
            "answer": "provider ok",
            "confidence": "high",
            "out_of_scope": False,
            "diagnosis": [],
            "links": [],
            "missing_permissions": [],
            "next_steps": [],
            "tool_trace_id": None,
        },
        output=[],
        usage=None,
        output_text="provider ok",
        status="completed",
    )

    class _Responses:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def parse(self, **kwargs):
            self.calls.append(kwargs)
            return response

    class _Client:
        def __init__(self) -> None:
            self.responses = _Responses()

    client = _Client()
    provider = OpenAIResponsesProvider(
        OpenAIProviderRuntime(
            api_key="test-key",
            model_name="gpt-4o",
            timeout_seconds=45,
            store_responses=False,
            max_input_chars=12000,
        ),
        client_factory=lambda **kwargs: client,
    )

    provider.generate(
        AssistantProviderRequest(
            conversation_id="conv-1",
            user_message="How do I create a new order?",
            system_instructions="Return structured output.",
            response_language="en",
            detected_language="en",
            previous_output_items=[
                {
                    "type": "function_call",
                    "id": "fc-1",
                    "call_id": "call-1",
                    "name": "assistant_search_workflow_help",
                    "arguments": '{"query":"order"}',
                }
            ],
            continuation_tool_outputs=[
                {
                    "type": "function_call_output",
                    "call_id": "call-1",
                    "output": '{"ok": true}',
                }
            ],
            recent_messages=[{"role": "user", "content": "How do I create a new order?"}],
            provider_tool_name_map={},
            max_tool_calls=8,
            max_input_chars=12000,
        )
    )

    call = client.responses.calls[0]
    input_rows = call["input"]
    assert "previous_response_id" not in call
    assert any(row.get("role") == "user" for row in input_rows if isinstance(row, dict))
    function_call_index = next(index for index, row in enumerate(input_rows) if row.get("type") == "function_call")
    function_output_index = next(
        index for index, row in enumerate(input_rows) if row.get("type") == "function_call_output"
    )
    assert function_call_index < function_output_index
