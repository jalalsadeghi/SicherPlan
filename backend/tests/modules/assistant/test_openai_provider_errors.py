from __future__ import annotations

from types import SimpleNamespace

from app.modules.assistant.openai_client import OpenAIProviderRuntime, OpenAIResponsesProvider
from app.modules.assistant.provider import (
    AssistantProviderRateLimitError,
    AssistantProviderStructuredOutputError,
    AssistantProviderTimeoutError,
)
from app.modules.assistant.provider import AssistantProviderRequest


def _request() -> AssistantProviderRequest:
    return AssistantProviderRequest(
        conversation_id="conv-1",
        user_message="Why is Markus not visible in the employee app?",
        system_instructions="Use the same language.",
        response_language="en",
        detected_language="en",
        max_tool_calls=8,
        max_input_chars=12000,
    )


def _provider(client_factory):
    return OpenAIResponsesProvider(
        OpenAIProviderRuntime(
            api_key="test-key",
            model_name="gpt-5.5-mini",
            timeout_seconds=45,
            store_responses=False,
            max_input_chars=12000,
        ),
        client_factory=client_factory,
    )


def test_openai_provider_handles_timeout_safely() -> None:
    APITimeoutError = type("APITimeoutError", (Exception,), {})

    class _Responses:
        def parse(self, **kwargs):
            raise APITimeoutError()

    class _Client:
        responses = _Responses()

    try:
        _provider(lambda **kwargs: _Client()).generate(_request())
    except AssistantProviderTimeoutError:
        pass
    else:
        raise AssertionError("Expected AssistantProviderTimeoutError")


def test_openai_provider_handles_rate_limit_safely() -> None:
    RateLimitError = type("RateLimitError", (Exception,), {})

    class _Responses:
        def parse(self, **kwargs):
            raise RateLimitError()

    class _Client:
        responses = _Responses()

    try:
        _provider(lambda **kwargs: _Client()).generate(_request())
    except AssistantProviderRateLimitError:
        pass
    else:
        raise AssertionError("Expected AssistantProviderRateLimitError")


def test_openai_provider_handles_invalid_structured_output_safely() -> None:
    response = SimpleNamespace(
        output_parsed={"bad": "payload"},
        output=[],
        usage=None,
        output_text="bad",
        status="completed",
    )

    class _Responses:
        def parse(self, **kwargs):
            return response

    class _Client:
        responses = _Responses()

    try:
        _provider(lambda **kwargs: _Client()).generate(_request())
    except AssistantProviderStructuredOutputError:
        pass
    else:
        raise AssertionError("Expected AssistantProviderStructuredOutputError")
