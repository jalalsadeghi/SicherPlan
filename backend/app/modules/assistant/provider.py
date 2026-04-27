"""Provider abstraction and deterministic mock provider for the assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from time import perf_counter
from typing import Any, Callable, Protocol

from app.config import AppSettings
from app.modules.assistant.language import placeholder_diagnosis
from app.modules.assistant.schemas import AssistantConfidence


@dataclass(frozen=True)
class AssistantProviderUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class AssistantProviderRequest:
    conversation_id: str
    user_message: str
    system_instructions: str
    response_language: str
    detected_language: str
    route_context: dict[str, Any] | None = None
    recent_messages: list[dict[str, Any]] = field(default_factory=list)
    knowledge_chunks: list[dict[str, Any]] = field(default_factory=list)
    grounding_context: dict[str, Any] | None = None
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    continuation_tool_outputs: list[dict[str, Any]] = field(default_factory=list)
    previous_response_id: str | None = None
    previous_output_items: list[dict[str, Any]] = field(default_factory=list)
    available_tools: list[dict[str, Any]] = field(default_factory=list)
    provider_tool_name_map: dict[str, str] = field(default_factory=dict)
    max_tool_calls: int = 0
    max_input_chars: int = 12000
    max_output_tokens: int = 900
    model_name_override: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AssistantProviderResult:
    final_response: dict[str, Any]
    raw_text: str | None
    requested_tool_calls: list[dict[str, Any]] = field(default_factory=list)
    response_id: str | None = None
    output_items: list[dict[str, Any]] = field(default_factory=list)
    usage: AssistantProviderUsage | None = None
    provider_name: str = "mock"
    provider_mode: str = "mock"
    model_name: str = "mock-assistant-v1"
    latency_ms: int | None = None
    finish_reason: str | None = None


class AssistantProvider(Protocol):
    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult: ...


class AssistantProviderError(RuntimeError):
    """Base provider error without sensitive payload data."""

    code = "assistant.provider.unavailable"

    def __init__(
        self,
        message: str,
        *,
        provider_error_type: str | None = None,
        provider_error_code: str | None = None,
        http_status: int | None = None,
        safe_message: str | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.provider_error_type = provider_error_type
        self.provider_error_code = provider_error_code
        self.http_status = http_status
        self.safe_message = safe_message or message
        self.retry_after_seconds = retry_after_seconds


class AssistantProviderConfigurationError(AssistantProviderError):
    """Provider mode is invalid or not available in the current runtime."""

    code = "assistant.provider.configuration_error"


class AssistantProviderTimeoutError(AssistantProviderError):
    """Provider call timed out."""

    code = "assistant.provider.timeout"


class AssistantProviderUnavailableError(AssistantProviderError):
    """Provider call failed or is unavailable."""

    code = "assistant.provider.unavailable"


class AssistantProviderRateLimitError(AssistantProviderError):
    """Provider request was rate limited."""

    code = "assistant.provider.rate_limited"


class AssistantProviderAuthenticationError(AssistantProviderError):
    """Provider authentication or project access failed."""

    code = "assistant.provider.authentication_failed"


class AssistantProviderInvalidRequestError(AssistantProviderError):
    """Provider request shape or tool schema is invalid."""

    code = "assistant.provider.invalid_request"


class AssistantProviderStructuredOutputError(AssistantProviderError):
    """Provider returned invalid structured output."""

    code = "assistant.provider.invalid_response"


_MOCK_PERSIAN = (
    "این یک پاسخ آزمایشی از Mock Provider برای SicherPlan است. "
    "در نسخه واقعی، پاسخ با استفاده از مستندات، سطح دسترسی کاربر و ابزارهای backend تولید می‌شود."
)
_MOCK_GERMAN = (
    "Dies ist eine Testantwort des Mock Providers für SicherPlan. "
    "In der echten Version wird die Antwort anhand der Dokumentation, der Benutzerberechtigungen "
    "und der Backend-Tools erzeugt."
)
_MOCK_ENGLISH = (
    "[MOCK RAG] This response was generated in mock mode by the Mock Provider using grounded SicherPlan context. "
    "Real provider mode will generate the final expert answer from the same facts."
)


class MockAssistantProvider:
    def __init__(
        self,
        *,
        raise_error: AssistantProviderError | None = None,
    ) -> None:
        self.raise_error = raise_error
        self.call_count = 0

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.call_count += 1
        if self.raise_error is not None:
            raise self.raise_error

        started = perf_counter()
        answer = _mock_answer(
            request.response_language,
            grounding_context=request.grounding_context,
        )
        diagnosis_finding, diagnosis_evidence = placeholder_diagnosis(request.response_language)
        duration_ms = max(int((perf_counter() - started) * 1000), 0)
        return AssistantProviderResult(
            final_response={
                "answer": answer,
                "confidence": AssistantConfidence.LOW.value,
                "out_of_scope": False,
                "diagnosis": [
                    {
                        "finding": diagnosis_finding,
                        "severity": "info",
                        "evidence": diagnosis_evidence,
                    }
                ],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text=answer,
            requested_tool_calls=[],
            usage=AssistantProviderUsage(
                input_tokens=min(len(request.user_message), request.max_input_chars),
                output_tokens=len(answer),
            ),
            provider_name="mock",
            provider_mode="mock",
            model_name="mock-assistant-v1",
            latency_ms=duration_ms,
            finish_reason="mock_complete",
        )


class OpenAIReservedAssistantProvider:
    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        del request
        raise AssistantProviderConfigurationError(
            "SP_AI_PROVIDER=openai is reserved for AI-11 and is not implemented in this task."
        )


def build_assistant_provider(
    settings: AppSettings,
    *,
    openai_client_factory: Callable[..., Any] | None = None,
) -> AssistantProvider:
    if not settings.ai_enabled:
        return MockAssistantProvider()
    if settings.ai_provider == "mock":
        return MockAssistantProvider()
    if settings.ai_provider == "openai":
        from app.modules.assistant.openai_client import OpenAIResponsesProvider

        return OpenAIResponsesProvider.from_settings(settings, client_factory=openai_client_factory)
    raise AssistantProviderConfigurationError("Unsupported assistant provider mode.")


def estimate_tokens(text_or_payload: Any) -> int:
    if text_or_payload is None:
        return 0
    if isinstance(text_or_payload, str):
        serialized = text_or_payload
    else:
        try:
            serialized = json.dumps(text_or_payload, ensure_ascii=False, sort_keys=True)
        except TypeError:
            serialized = str(text_or_payload)
    if not serialized:
        return 0
    structural_chars = sum(1 for char in serialized if char in "{}[],:\"")
    newline_chars = serialized.count("\n")
    estimated = math.ceil(len(serialized) / 3.5)
    estimated += math.ceil(structural_chars / 12)
    estimated += math.ceil(newline_chars / 8)
    return max(estimated, 1)


def _mock_answer(
    response_language: str,
    *,
    grounding_context: dict[str, Any] | None = None,
) -> str:
    source_hint = _mock_source_hint(grounding_context)
    if response_language == "fa":
        return f"[MOCK RAG] {source_hint} {_MOCK_PERSIAN}".strip()
    if response_language == "de":
        return f"[MOCK RAG] {source_hint} {_MOCK_GERMAN}".strip()
    return f"{_MOCK_ENGLISH} {source_hint}".strip()


def _mock_source_hint(grounding_context: dict[str, Any] | None) -> str:
    if not grounding_context:
        return "No grounding sources were attached."
    sources = grounding_context.get("sources")
    if not isinstance(sources, list) or not sources:
        return "No grounding sources were attached."
    source_labels: list[str] = []
    for item in sources[:4]:
        if not isinstance(item, dict):
            continue
        page_id = str(item.get("page_id") or "").strip()
        source_type = str(item.get("source_type") or "").strip()
        title = str(item.get("title") or "").strip()
        if page_id:
            source_labels.append(page_id)
        elif title:
            source_labels.append(title)
        elif source_type:
            source_labels.append(source_type)
    if not source_labels:
        return "Grounding sources were attached."
    return "Grounding sources: " + ", ".join(source_labels) + "."


def mock_provider_answer(
    response_language: str,
    *,
    grounding_context: dict[str, Any] | None = None,
) -> str:
    return _mock_answer(response_language, grounding_context=grounding_context)
