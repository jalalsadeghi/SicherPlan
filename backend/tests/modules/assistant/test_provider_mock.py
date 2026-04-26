from __future__ import annotations

from app.modules.assistant.provider import (
    AssistantProviderConfigurationError,
    AssistantProviderRequest,
    MockAssistantProvider,
    mock_provider_answer,
)


def _request(response_language: str) -> AssistantProviderRequest:
    return AssistantProviderRequest(
        conversation_id="conv-1",
        user_message="Why is Markus not visible?",
        system_instructions="Use the same language.",
        response_language=response_language,
        detected_language=response_language,
        route_context=None,
        recent_messages=[],
        knowledge_chunks=[],
        available_tools=[],
        max_tool_calls=8,
        max_input_chars=12000,
        metadata={"request_id": "req-1"},
    )


def test_mock_provider_returns_structured_response() -> None:
    result = MockAssistantProvider().generate(_request("en"))
    assert result.provider_mode == "mock"
    assert result.provider_name == "mock"
    assert result.requested_tool_calls == []
    assert result.final_response["answer"] == mock_provider_answer("en")
    assert result.final_response["answer"].startswith("[MOCK RAG]")
    assert result.final_response["out_of_scope"] is False


def test_mock_provider_respects_persian_response_language() -> None:
    result = MockAssistantProvider().generate(_request("fa"))
    assert result.final_response["answer"] == mock_provider_answer("fa")


def test_mock_provider_respects_german_response_language() -> None:
    result = MockAssistantProvider().generate(_request("de"))
    assert result.final_response["answer"] == mock_provider_answer("de")


def test_mock_provider_respects_english_response_language() -> None:
    result = MockAssistantProvider().generate(_request("en"))
    assert result.final_response["answer"] == mock_provider_answer("en")


def test_mock_provider_requires_no_api_key() -> None:
    result = MockAssistantProvider().generate(_request("en"))
    assert result.final_response["answer"] == mock_provider_answer("en")


def test_provider_error_is_safe() -> None:
    provider = MockAssistantProvider(
        raise_error=AssistantProviderConfigurationError("AI provider is not configured.")
    )
    try:
        provider.generate(_request("en"))
    except AssistantProviderConfigurationError as exc:
        message = str(exc)
        assert "configured" in message
        assert "sk-" not in message
    else:
        raise AssertionError("Expected AssistantProviderConfigurationError")
