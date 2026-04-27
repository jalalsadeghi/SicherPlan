"""Backend-only OpenAI Responses provider wrapper."""

from __future__ import annotations

from dataclasses import dataclass
import json
from time import perf_counter
from typing import Any, Callable

from app.config import AppSettings
from app.modules.assistant.provider import (
    AssistantProvider,
    AssistantProviderConfigurationError,
    AssistantProviderAuthenticationError,
    AssistantProviderInvalidRequestError,
    AssistantProviderRequest,
    AssistantProviderResult,
    AssistantProviderStructuredOutputError,
    AssistantProviderTimeoutError,
    AssistantProviderUnavailableError,
    AssistantProviderUsage,
    AssistantProviderRateLimitError,
)
from app.modules.assistant.schemas import AssistantProviderStructuredOutput
from app.modules.assistant.tool_name_adapter import is_valid_provider_tool_name


OpenAIClientFactory = Callable[..., Any]


def get_openai_sdk_info() -> tuple[bool, str | None]:
    try:
        import openai
    except Exception:
        return False, None
    return True, getattr(openai, "__version__", None)


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
            call_kwargs = {
                "model": self.runtime.model_name,
                "text_format": AssistantProviderStructuredOutput,
                "store": self.runtime.store_responses,
            }
            if request.previous_response_id:
                call_kwargs["previous_response_id"] = request.previous_response_id
                call_kwargs["input"] = self._build_previous_response_continuation_input(request)
            elif request.previous_output_items and request.continuation_tool_outputs:
                call_kwargs["input"] = self._build_stateless_continuation_input(request)
            else:
                call_kwargs["input"] = self._build_initial_input(request)
            normalized_tools = self._normalize_tools_for_responses_api(
                request.available_tools,
                request.provider_tool_name_map,
            )
            if normalized_tools:
                call_kwargs["tools"] = normalized_tools
            response = client.responses.parse(**call_kwargs)
        except Exception as exc:
            raise self._map_provider_exception(exc) from exc

        latency_ms = max(int((perf_counter() - started) * 1000), 0)
        requested_tool_calls = self._extract_tool_calls(response)
        usage = self._extract_usage(response)
        if requested_tool_calls:
            return AssistantProviderResult(
                final_response={},
                raw_text=getattr(response, "output_text", None),
                requested_tool_calls=requested_tool_calls,
                response_id=getattr(response, "id", None),
                output_items=self._extract_output_items(response),
                usage=usage,
                provider_name="openai",
                provider_mode="openai",
                model_name=self.runtime.model_name,
                latency_ms=latency_ms,
                finish_reason=getattr(response, "status", None),
            )

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

        return AssistantProviderResult(
            final_response=payload,
            raw_text=getattr(response, "output_text", None),
            requested_tool_calls=requested_tool_calls,
            response_id=getattr(response, "id", None),
            output_items=self._extract_output_items(response),
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
    def _build_initial_input(request: AssistantProviderRequest) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        if request.system_instructions:
            messages.append({"role": "system", "content": request.system_instructions})
        if request.grounding_context:
            messages.append(
                {
                    "role": "system",
                    "content": "Grounding context package\n"
                    + json.dumps(request.grounding_context, ensure_ascii=False, indent=2, sort_keys=True),
                }
            )
        for item in request.recent_messages:
            role = str(item.get("role", "")).strip()
            content = str(item.get("content", "")).strip()
            if role and content:
                messages.append({"role": role, "content": content})
        user_content = request.user_message[: request.max_input_chars]
        if not messages or messages[-1].get("role") != "user" or messages[-1].get("content") != user_content:
            messages.append({"role": "user", "content": user_content})
        return messages

    @classmethod
    def _build_previous_response_continuation_input(
        cls,
        request: AssistantProviderRequest,
    ) -> list[dict[str, Any]]:
        return cls._normalize_function_call_outputs(request.continuation_tool_outputs)

    @classmethod
    def _build_stateless_continuation_input(
        cls,
        request: AssistantProviderRequest,
    ) -> list[dict[str, Any]]:
        messages = cls._build_initial_input(request)
        messages.extend(cls._normalize_output_items(request.previous_output_items))
        messages.extend(cls._normalize_function_call_outputs(request.continuation_tool_outputs))
        return messages

    @staticmethod
    def _normalize_function_call_outputs(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type") or "").strip()
            if item_type != "function_call_output":
                continue
            output = item.get("output")
            if output is None:
                continue
            payload: dict[str, Any] = {
                "type": "function_call_output",
                "output": str(output),
            }
            call_id = str(item.get("call_id") or "").strip()
            if call_id:
                payload["call_id"] = call_id
            normalized.append(payload)
        return normalized

    @staticmethod
    def _normalize_output_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type") or "").strip()
            if not item_type:
                continue
            normalized_item = dict(item)
            if item_type == "function_call":
                name = str(item.get("name") or "").strip()
                arguments = item.get("arguments")
                if not name or arguments is None:
                    continue
                normalized_item["name"] = name
                normalized_item["arguments"] = str(arguments)
                call_id = str(item.get("call_id") or "").strip()
                if call_id:
                    normalized_item["call_id"] = call_id
            normalized.append(normalized_item)
        return normalized

    @staticmethod
    def _normalize_tools_for_responses_api(
        tools: list[dict[str, Any]],
        provider_tool_name_map: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        name_map = provider_tool_name_map or {}
        normalized: list[dict[str, Any]] = []
        seen_names: set[str] = set()
        for item in tools:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type") or "").strip()
            if item_type != "function":
                continue
            function = item.get("function")
            if not isinstance(function, dict):
                continue
            internal_name = str(function.get("name") or "").strip()
            if not internal_name:
                continue
            name = next(
                (provider_name for provider_name, mapped_name in name_map.items() if mapped_name == internal_name),
                internal_name,
            )
            if not is_valid_provider_tool_name(name):
                raise AssistantProviderInvalidRequestError(
                    "OpenAI provider tool name is invalid.",
                    provider_error_type="ToolNameValidationError",
                    safe_message=f"Invalid provider tool name: {name}",
                )
            if name in seen_names:
                raise AssistantProviderInvalidRequestError(
                    "OpenAI provider tool names must be unique.",
                    provider_error_type="ToolNameValidationError",
                    safe_message=f"Duplicate provider tool name: {name}",
                )
            parameters = function.get("parameters") or {"type": "object", "properties": {}}
            if not isinstance(parameters, dict) or parameters.get("type") != "object":
                raise AssistantProviderInvalidRequestError(
                    "OpenAI provider tool schema is invalid.",
                    provider_error_type="ToolSchemaValidationError",
                    safe_message=f"Invalid JSON schema for tool: {internal_name}",
                )
            seen_names.add(name)
            normalized.append(
                {
                    "type": "function",
                    "name": name,
                    "description": function.get("description"),
                    "parameters": parameters,
                }
            )
        return normalized

    @staticmethod
    def _extract_tool_calls(response: Any) -> list[dict[str, Any]]:
        output = getattr(response, "output", None) or []
        tool_calls: list[dict[str, Any]] = []
        for item in output:
            item_type = getattr(item, "type", None)
            if item_type != "function_call":
                continue
            response_item = {
                "type": "function_call",
                "id": getattr(item, "id", None),
                "call_id": getattr(item, "call_id", None),
                "name": getattr(item, "name", None),
                "arguments": getattr(item, "arguments", None),
            }
            tool_calls.append(
                {
                    "id": getattr(item, "id", None),
                    "name": getattr(item, "name", None),
                    "provider_tool_name": getattr(item, "name", None),
                    "arguments": getattr(item, "arguments", None),
                    "call_id": getattr(item, "call_id", None),
                    "response_item": response_item,
                }
            )
        return tool_calls

    @staticmethod
    def _extract_output_items(response: Any) -> list[dict[str, Any]]:
        output = getattr(response, "output", None) or []
        items: list[dict[str, Any]] = []
        for item in output:
            item_type = getattr(item, "type", None)
            if not item_type:
                continue
            normalized: dict[str, Any] = {"type": item_type}
            for key in ("id", "call_id", "name", "arguments", "status"):
                value = getattr(item, key, None)
                if value is not None:
                    normalized[key] = value
            items.append(normalized)
        return items

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
        safe_message = str(exc).strip()[:240] or name
        if name == "APITimeoutError":
            return AssistantProviderTimeoutError(
                "OpenAI provider request timed out.",
                provider_error_type=name,
                safe_message=safe_message,
            )
        if name == "RateLimitError":
            return AssistantProviderRateLimitError(
                "OpenAI provider rate limited the request.",
                provider_error_type=name,
                safe_message=safe_message,
            )
        if name in {"AuthenticationError", "PermissionDeniedError"}:
            return AssistantProviderAuthenticationError(
                "OpenAI provider authentication failed.",
                provider_error_type=name,
                provider_error_code=getattr(exc, "code", None),
                http_status=getattr(exc, "status_code", None),
                safe_message=safe_message,
            )
        if name in {"BadRequestError", "UnprocessableEntityError"}:
            return AssistantProviderInvalidRequestError(
                "OpenAI provider request was invalid.",
                provider_error_type=name,
                provider_error_code=getattr(exc, "code", None),
                http_status=getattr(exc, "status_code", None),
                safe_message=safe_message,
            )
        if name == "APIStatusError":
            status_code = getattr(exc, "status_code", None)
            if status_code in {401, 403}:
                return AssistantProviderAuthenticationError(
                    "OpenAI provider authentication failed.",
                    provider_error_type=name,
                    provider_error_code=getattr(exc, "code", None),
                    http_status=status_code,
                    safe_message=safe_message,
                )
            if status_code == 429:
                return AssistantProviderRateLimitError(
                    "OpenAI provider rate limited the request.",
                    provider_error_type=name,
                    provider_error_code=getattr(exc, "code", None),
                    http_status=status_code,
                    safe_message=safe_message,
                )
            if status_code is not None and 400 <= status_code < 500:
                return AssistantProviderInvalidRequestError(
                    "OpenAI provider request was invalid.",
                    provider_error_type=name,
                    provider_error_code=getattr(exc, "code", None),
                    http_status=status_code,
                    safe_message=safe_message,
                )
            return AssistantProviderUnavailableError(
                "OpenAI provider is unavailable.",
                provider_error_type=name,
                provider_error_code=getattr(exc, "code", None),
                http_status=status_code,
                safe_message=safe_message,
            )
        if name in {"APIConnectionError", "APIError"}:
            return AssistantProviderUnavailableError(
                "OpenAI provider is unavailable.",
                provider_error_type=name,
                provider_error_code=getattr(exc, "code", None),
                http_status=getattr(exc, "status_code", None),
                safe_message=safe_message,
            )
        if isinstance(exc, (TypeError, ValueError)):
            return AssistantProviderInvalidRequestError(
                "OpenAI provider request was invalid.",
                provider_error_type=name,
                safe_message=safe_message,
            )
        if isinstance(exc, AssistantProviderConfigurationError):
            return exc
        if isinstance(exc, AssistantProviderStructuredOutputError):
            return exc
        return AssistantProviderUnavailableError(
            "OpenAI provider is unavailable.",
            provider_error_type=name,
            provider_error_code=getattr(exc, "code", None),
            http_status=getattr(exc, "status_code", None),
            safe_message=safe_message,
        )
