from __future__ import annotations

from app.modules.assistant.openai_client import OpenAIProviderRuntime, OpenAIResponsesProvider
from app.modules.assistant.provider import (
    AssistantProviderAuthenticationError,
    AssistantProviderInvalidRequestError,
    AssistantProviderRateLimitError,
    AssistantProviderTimeoutError,
    AssistantProviderUnavailableError,
)
from app.modules.assistant.provider import AssistantProviderRequest


def _request() -> AssistantProviderRequest:
    return AssistantProviderRequest(
        conversation_id="conv-1",
        user_message="How do I create a new order?",
        system_instructions="Return structured output.",
        response_language="en",
        detected_language="en",
        max_tool_calls=8,
        max_input_chars=12000,
    )


def _provider(client_factory):
    return OpenAIResponsesProvider(
        OpenAIProviderRuntime(
            api_key="test-key",
            model_name="gpt-4o",
            timeout_seconds=45,
            store_responses=False,
            max_input_chars=12000,
        ),
        client_factory=client_factory,
    )


def test_openai_provider_maps_timeout_safely() -> None:
    APITimeoutError = type("APITimeoutError", (Exception,), {})

    class _Responses:
        def parse(self, **kwargs):
            raise APITimeoutError("request timed out")

    class _Client:
        responses = _Responses()

    try:
        _provider(lambda **kwargs: _Client()).generate(_request())
    except AssistantProviderTimeoutError as exc:
        assert exc.code == "assistant.provider.timeout"
        assert exc.provider_error_type == "APITimeoutError"
    else:
        raise AssertionError("Expected timeout mapping")


def test_openai_provider_maps_rate_limit_safely() -> None:
    RateLimitError = type("RateLimitError", (Exception,), {})

    class _Responses:
        def parse(self, **kwargs):
            raise RateLimitError("rate limit")

    class _Client:
        responses = _Responses()

    try:
        _provider(lambda **kwargs: _Client()).generate(_request())
    except AssistantProviderRateLimitError as exc:
        assert exc.code == "assistant.provider.rate_limited"
        assert exc.provider_error_type == "RateLimitError"
    else:
        raise AssertionError("Expected rate limit mapping")


def test_openai_provider_maps_api_status_401_to_authentication_failure() -> None:
    AuthenticationError = type("AuthenticationError", (Exception,), {"status_code": 401, "code": "invalid_api_key"})

    class _Responses:
        def parse(self, **kwargs):
            raise AuthenticationError("invalid api key")

    class _Client:
        responses = _Responses()

    try:
        _provider(lambda **kwargs: _Client()).generate(_request())
    except AssistantProviderAuthenticationError as exc:
        assert exc.code == "assistant.provider.authentication_failed"
        assert exc.provider_error_type == "AuthenticationError"
        assert exc.provider_error_code == "invalid_api_key"
        assert exc.http_status == 401
    else:
        raise AssertionError("Expected auth failure mapping")


def test_openai_provider_maps_invalid_request_safely() -> None:
    BadRequestError = type("BadRequestError", (Exception,), {"status_code": 400, "code": "invalid_request_error"})

    class _Responses:
        def parse(self, **kwargs):
            raise BadRequestError("tools schema invalid")

    class _Client:
        responses = _Responses()

    try:
        _provider(lambda **kwargs: _Client()).generate(_request())
    except AssistantProviderInvalidRequestError as exc:
        assert exc.code == "assistant.provider.invalid_request"
        assert exc.provider_error_type == "BadRequestError"
        assert exc.provider_error_code == "invalid_request_error"
        assert exc.http_status == 400
    else:
        raise AssertionError("Expected invalid request mapping")


def test_openai_provider_maps_api_status_503_to_unavailable() -> None:
    APIStatusError = type("APIStatusError", (Exception,), {"status_code": 503, "code": "server_error"})

    class _Responses:
        def parse(self, **kwargs):
            raise APIStatusError("upstream unavailable")

    class _Client:
        responses = _Responses()

    try:
        _provider(lambda **kwargs: _Client()).generate(_request())
    except AssistantProviderUnavailableError as exc:
        assert exc.code == "assistant.provider.unavailable"
        assert exc.provider_error_type == "APIStatusError"
        assert exc.provider_error_code == "server_error"
        assert exc.http_status == 503
    else:
        raise AssertionError("Expected unavailable mapping")

