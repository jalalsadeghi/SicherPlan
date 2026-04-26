from __future__ import annotations

from app.config import AppSettings
from app.modules.assistant.openai_client import OpenAIResponsesProvider
from app.modules.assistant.provider import (
    AssistantProviderConfigurationError,
    MockAssistantProvider,
    build_assistant_provider,
)


def test_provider_factory_returns_mock_provider() -> None:
    provider = build_assistant_provider(AppSettings())
    assert isinstance(provider, MockAssistantProvider)


def test_provider_factory_rejects_unknown_provider() -> None:
    settings = object.__new__(AppSettings)
    object.__setattr__(settings, "ai_enabled", True)
    object.__setattr__(settings, "ai_provider", "unknown")
    try:
        build_assistant_provider(settings)
    except AssistantProviderConfigurationError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("Expected AssistantProviderConfigurationError")


def test_provider_factory_returns_openai_provider() -> None:
    settings = object.__new__(AppSettings)
    object.__setattr__(settings, "ai_enabled", True)
    object.__setattr__(settings, "ai_provider", "openai")
    object.__setattr__(settings, "ai_openai_api_key", "test-key")
    object.__setattr__(settings, "ai_response_model", "gpt-5.5-mini")
    object.__setattr__(settings, "ai_timeout_seconds", 45)
    object.__setattr__(settings, "ai_store_responses", False)
    object.__setattr__(settings, "ai_max_input_chars", 12000)
    provider = build_assistant_provider(settings, openai_client_factory=lambda **kwargs: object())
    assert isinstance(provider, OpenAIResponsesProvider)


def test_openai_provider_not_created_when_mock_mode() -> None:
    settings = object.__new__(AppSettings)
    object.__setattr__(settings, "ai_enabled", True)
    object.__setattr__(settings, "ai_provider", "mock")
    provider = build_assistant_provider(settings)
    assert isinstance(provider, MockAssistantProvider)


def test_openai_provider_not_created_when_ai_disabled() -> None:
    settings = object.__new__(AppSettings)
    object.__setattr__(settings, "ai_enabled", False)
    object.__setattr__(settings, "ai_provider", "openai")
    provider = build_assistant_provider(settings)
    assert isinstance(provider, MockAssistantProvider)
