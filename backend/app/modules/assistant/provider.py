"""Provider abstraction and deterministic mock provider for the assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
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
    available_tools: list[dict[str, Any]] = field(default_factory=list)
    max_tool_calls: int = 0
    max_input_chars: int = 12000
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AssistantProviderResult:
    final_response: dict[str, Any]
    raw_text: str | None
    requested_tool_calls: list[dict[str, Any]] = field(default_factory=list)
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


class AssistantProviderConfigurationError(AssistantProviderError):
    """Provider mode is invalid or not available in the current runtime."""


class AssistantProviderTimeoutError(AssistantProviderError):
    """Provider call timed out."""


class AssistantProviderUnavailableError(AssistantProviderError):
    """Provider call failed or is unavailable."""


class AssistantProviderRateLimitError(AssistantProviderError):
    """Provider request was rate limited."""


class AssistantProviderStructuredOutputError(AssistantProviderError):
    """Provider returned invalid structured output."""


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
    "This is a test response from the Mock Provider for SicherPlan. "
    "In the real version, the answer will be generated using documentation, user permissions, "
    "and backend tools."
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
        answer = _mock_answer(request.response_language)
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


def _mock_answer(response_language: str) -> str:
    if response_language == "fa":
        return _MOCK_PERSIAN
    if response_language == "de":
        return _MOCK_GERMAN
    return _MOCK_ENGLISH


def mock_provider_answer(response_language: str) -> str:
    return _mock_answer(response_language)
