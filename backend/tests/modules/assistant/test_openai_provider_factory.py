from __future__ import annotations

from app.config import AppSettings
from app.modules.assistant.openai_client import OpenAIResponsesProvider
from app.modules.assistant.provider import AssistantProviderConfigurationError, build_assistant_provider


def test_openai_provider_requires_api_key_in_openai_mode() -> None:
    settings = object.__new__(AppSettings)
    object.__setattr__(settings, "ai_enabled", True)
    object.__setattr__(settings, "ai_provider", "openai")
    object.__setattr__(settings, "ai_openai_api_key", "")
    object.__setattr__(settings, "ai_response_model", "gpt-5.5-mini")
    object.__setattr__(settings, "ai_timeout_seconds", 45)
    object.__setattr__(settings, "ai_store_responses", False)
    object.__setattr__(settings, "ai_max_input_chars", 12000)
    try:
        build_assistant_provider(settings, openai_client_factory=lambda **kwargs: object())
    except AssistantProviderConfigurationError as exc:
        assert str(exc) == "AI provider is not configured."
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
