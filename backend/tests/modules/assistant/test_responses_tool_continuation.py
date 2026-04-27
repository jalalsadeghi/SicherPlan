from __future__ import annotations

from types import SimpleNamespace

from app.modules.assistant.openai_client import OpenAIProviderRuntime, OpenAIResponsesProvider
from app.modules.assistant.provider import AssistantProviderRequest


def _response() -> SimpleNamespace:
    return SimpleNamespace(
        id="resp-test-1",
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


def test_previous_response_continuation_keeps_matching_call_id_without_fresh_user_prompt() -> None:
    class _Responses:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def parse(self, **kwargs):
            self.calls.append(kwargs)
            return _response()

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
            user_message="ignored during continuation",
            system_instructions="ignored during continuation",
            response_language="de",
            detected_language="de",
            previous_response_id="resp-1",
            continuation_tool_outputs=[
                {
                    "type": "function_call_output",
                    "call_id": "call-1",
                    "output": '{"status":"not_visible"}',
                }
            ],
        )
    )

    call = client.responses.calls[0]
    assert call["previous_response_id"] == "resp-1"
    assert call["input"] == [
        {
            "type": "function_call_output",
            "call_id": "call-1",
            "output": '{"status":"not_visible"}',
        }
    ]


def test_stateless_continuation_replays_function_call_before_tool_output() -> None:
    class _Responses:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def parse(self, **kwargs):
            self.calls.append(kwargs)
            return _response()

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
            user_message="Warum ist die Schicht nicht sichtbar?",
            system_instructions="Return structured output.",
            response_language="de",
            detected_language="de",
            recent_messages=[{"role": "user", "content": "Warum ist die Schicht nicht sichtbar?"}],
            previous_output_items=[
                {
                    "type": "function_call",
                    "id": "fc-1",
                    "call_id": "call-1",
                    "name": "assistant_diagnose_employee_shift_visibility",
                    "arguments": '{"employee_name":"Markus"}',
                }
            ],
            continuation_tool_outputs=[
                {
                    "type": "function_call_output",
                    "call_id": "call-1",
                    "output": '{"status":"not_visible"}',
                }
            ],
        )
    )

    call = client.responses.calls[0]
    input_rows = call["input"]
    assert "previous_response_id" not in call
    assert sum(1 for row in input_rows if row.get("role") == "user") == 1
    function_call_index = next(index for index, row in enumerate(input_rows) if row.get("type") == "function_call")
    function_output_index = next(
        index for index, row in enumerate(input_rows) if row.get("type") == "function_call_output"
    )
    assert function_call_index < function_output_index
