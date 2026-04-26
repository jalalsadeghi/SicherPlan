from __future__ import annotations

from types import SimpleNamespace

from app.modules.assistant.openai_client import OpenAIProviderRuntime, OpenAIResponsesProvider
from app.modules.assistant.provider import AssistantProviderRequest


class _FakeResponsesAPI:
    def __init__(self, response) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class _FakeClient:
    def __init__(self, response) -> None:
        self.responses = _FakeResponsesAPI(response)


def _request() -> AssistantProviderRequest:
    return AssistantProviderRequest(
        conversation_id="conv-1",
        user_message="Why is Markus not visible in the employee app?",
        system_instructions="Use the same language.",
        response_language="en",
        detected_language="en",
        route_context={"path": "/admin/planning-staffing", "route_name": "SicherPlanPlanningStaffing"},
        recent_messages=[{"role": "user", "content": "Earlier question"}],
        knowledge_chunks=[],
        available_tools=[],
        max_tool_calls=8,
        max_input_chars=12000,
        metadata={"request_id": "req-1"},
    )


def test_openai_provider_builds_structured_response_request() -> None:
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
        output=[],
        usage=SimpleNamespace(input_tokens=11, output_tokens=7),
        output_text="OpenAI answer",
        status="completed",
    )
    fake_client = _FakeClient(response)
    provider = OpenAIResponsesProvider(
        OpenAIProviderRuntime(
            api_key="test-key",
            model_name="gpt-5.5-mini",
            timeout_seconds=45,
            store_responses=False,
            max_input_chars=12000,
        ),
        client_factory=lambda **kwargs: fake_client,
    )
    result = provider.generate(_request())

    assert result.provider_mode == "openai"
    assert result.model_name == "gpt-5.5-mini"
    assert result.final_response["answer"] == "OpenAI answer"
    call = fake_client.responses.calls[0]
    assert call["model"] == "gpt-5.5-mini"
    assert call["store"] is False
    assert call["text_format"].__name__ == "AssistantProviderStructuredOutput"
    assert call["input"][0]["role"] == "system"
    assert call["input"][-1]["role"] == "user"


def test_openai_provider_sets_store_false_by_default() -> None:
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
        output=[],
        usage=None,
        output_text="OpenAI answer",
        status="completed",
    )
    fake_client = _FakeClient(response)
    provider = OpenAIResponsesProvider(
        OpenAIProviderRuntime(
            api_key="test-key",
            model_name="gpt-5.5-mini",
            timeout_seconds=45,
            store_responses=False,
            max_input_chars=12000,
        ),
        client_factory=lambda **kwargs: fake_client,
    )
    provider.generate(_request())
    assert fake_client.responses.calls[0]["store"] is False


def test_openai_provider_uses_configured_model() -> None:
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
        output=[],
        usage=None,
        output_text="OpenAI answer",
        status="completed",
    )
    fake_client = _FakeClient(response)
    provider = OpenAIResponsesProvider(
        OpenAIProviderRuntime(
            api_key="test-key",
            model_name="gpt-5.5-pro",
            timeout_seconds=45,
            store_responses=False,
            max_input_chars=12000,
        ),
        client_factory=lambda **kwargs: fake_client,
    )
    provider.generate(_request())
    assert fake_client.responses.calls[0]["model"] == "gpt-5.5-pro"
