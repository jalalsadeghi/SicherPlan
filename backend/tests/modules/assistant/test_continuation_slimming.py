from __future__ import annotations

from types import SimpleNamespace

from app.modules.assistant.openai_client import OpenAIProviderRuntime, OpenAIResponsesProvider
from app.modules.assistant.provider import AssistantProviderRequest, estimate_tokens


def test_stateless_continuation_does_not_resend_full_grounding_or_history() -> None:
    response = SimpleNamespace(
        output_parsed={
            "answer": "ok",
            "confidence": "medium",
            "out_of_scope": False,
            "diagnosis": [],
            "links": [],
            "missing_permissions": [],
            "next_steps": [],
            "tool_trace_id": None,
        },
        output=[],
        usage=None,
        output_text="ok",
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
            user_message="ignored",
            system_instructions="Use the tool outputs and prior response context to produce the final structured answer.",
            response_language="de",
            detected_language="de",
            recent_messages=[{"role": "user", "content": "very long history " * 200}],
            grounding_context={"sources": [{"page_id": "P-04", "content": "y" * 4000}]},
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
            max_output_tokens=700,
            metadata={"continuation_mode": "stateless"},
        )
    )

    call = client.responses.calls[0]
    input_rows = call["input"]
    assert not any("Grounding context package" in row.get("content", "") for row in input_rows if isinstance(row, dict))
    assert not any(row.get("role") == "user" for row in input_rows if isinstance(row, dict))
    assert estimate_tokens(input_rows) < 5000
