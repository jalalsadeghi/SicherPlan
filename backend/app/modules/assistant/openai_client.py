"""Backend-only OpenAI Responses provider wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable

from app.config import AppSettings
from app.modules.assistant.provider import (
    AssistantProvider,
    AssistantProviderConfigurationError,
    AssistantProviderRequest,
    AssistantProviderResult,
    AssistantProviderStructuredOutputError,
    AssistantProviderTimeoutError,
    AssistantProviderUnavailableError,
    AssistantProviderUsage,
    AssistantProviderRateLimitError,
)
from app.modules.assistant.schemas import AssistantProviderStructuredOutput


OpenAIClientFactory = Callable[..., Any]


def _default_openai_client_factory(**kwargs: Any) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise AssistantProviderConfigurationError(
            "The OpenAI Python SDK is not installed for assistant openai mode."
        ) from exc
    return OpenAI(**kwargs)


@dataclass(frozen=True)
class OpenAIProviderRuntime:
    api_key: str
    model_name: str
    timeout_seconds: int
    store_responses: bool
    max_input_chars: int


class OpenAIResponsesProvider(AssistantProvider):
    def __init__(
        self,
        runtime: OpenAIProviderRuntime,
        *,
        client_factory: OpenAIClientFactory | None = None,
    ) -> None:
        self.runtime = runtime
        self.client_factory = client_factory or _default_openai_client_factory
        self._client: Any | None = None

    @classmethod
    def from_settings(
        cls,
        settings: AppSettings,
        *,
        client_factory: OpenAIClientFactory | None = None,
    ) -> "OpenAIResponsesProvider":
        api_key = settings.ai_openai_api_key.strip()
        if not api_key:
            raise AssistantProviderConfigurationError("AI provider is not configured.")
        return cls(
            OpenAIProviderRuntime(
                api_key=api_key,
                model_name=settings.ai_response_model,
                timeout_seconds=settings.ai_timeout_seconds,
                store_responses=settings.ai_store_responses,
                max_input_chars=settings.ai_max_input_chars,
            ),
            client_factory=client_factory,
        )

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        client = self._get_client()
        started = perf_counter()
        try:
            response = client.responses.parse(
                model=self.runtime.model_name,
                input=self._build_input(request),
                text_format=AssistantProviderStructuredOutput,
                store=self.runtime.store_responses,
                tools=request.available_tools,
            )
        except Exception as exc:
            raise self._map_provider_exception(exc) from exc

        latency_ms = max(int((perf_counter() - started) * 1000), 0)
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise AssistantProviderStructuredOutputError("OpenAI provider returned no parsed structured output.")
        if isinstance(parsed, AssistantProviderStructuredOutput):
            payload = parsed.model_dump(mode="json")
        elif isinstance(parsed, dict):
            try:
                payload = AssistantProviderStructuredOutput.model_validate(parsed).model_dump(mode="json")
            except Exception as exc:
                raise AssistantProviderStructuredOutputError(
                    "OpenAI provider returned invalid structured output."
                ) from exc
        else:
            try:
                payload = AssistantProviderStructuredOutput.model_validate(parsed).model_dump(mode="json")
            except Exception as exc:
                raise AssistantProviderStructuredOutputError(
                    "OpenAI provider returned invalid structured output."
                ) from exc

        requested_tool_calls = self._extract_tool_calls(response)
        usage = self._extract_usage(response)
        return AssistantProviderResult(
            final_response=payload,
            raw_text=getattr(response, "output_text", None),
            requested_tool_calls=requested_tool_calls,
            usage=usage,
            provider_name="openai",
            provider_mode="openai",
            model_name=self.runtime.model_name,
            latency_ms=latency_ms,
            finish_reason=getattr(response, "status", None),
        )

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = self.client_factory(
                api_key=self.runtime.api_key,
                timeout=self.runtime.timeout_seconds,
            )
        return self._client

    @staticmethod
    def _build_input(request: AssistantProviderRequest) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        if request.system_instructions:
            messages.append({"role": "system", "content": request.system_instructions})
        for item in request.recent_messages:
            role = str(item.get("role", "")).strip()
            content = str(item.get("content", "")).strip()
            if role and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": request.user_message[: request.max_input_chars]})
        return messages

    @staticmethod
    def _extract_tool_calls(response: Any) -> list[dict[str, Any]]:
        output = getattr(response, "output", None) or []
        tool_calls: list[dict[str, Any]] = []
        for item in output:
            item_type = getattr(item, "type", None)
            if item_type != "function_call":
                continue
            tool_calls.append(
                {
                    "id": getattr(item, "id", None),
                    "name": getattr(item, "name", None),
                    "arguments": getattr(item, "arguments", None),
                    "call_id": getattr(item, "call_id", None),
                }
            )
        return tool_calls

    @staticmethod
    def _extract_usage(response: Any) -> AssistantProviderUsage | None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return None
        return AssistantProviderUsage(
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
        )

    @staticmethod
    def _map_provider_exception(exc: Exception) -> Exception:
        name = type(exc).__name__
        if name == "APITimeoutError":
            return AssistantProviderTimeoutError("OpenAI provider request timed out.")
        if name == "RateLimitError":
            return AssistantProviderRateLimitError("OpenAI provider rate limited the request.")
        if name in {"APIConnectionError", "APIStatusError", "APIError"}:
            return AssistantProviderUnavailableError("OpenAI provider is unavailable.")
        if isinstance(exc, AssistantProviderConfigurationError):
            return exc
        if isinstance(exc, AssistantProviderStructuredOutputError):
            return exc
        return AssistantProviderUnavailableError("OpenAI provider is unavailable.")
