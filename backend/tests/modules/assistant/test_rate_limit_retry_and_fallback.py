from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import (
    AssistantProviderRateLimitError,
    AssistantProviderRequest,
    AssistantProviderResult,
)
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from tests.modules.assistant.test_operational_diagnostic_tool_loop import _context
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


@dataclass
class _RetryingProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        if len(self.requests) == 1:
            raise AssistantProviderRateLimitError(
                "Rate limit reached. Try again in 0s.",
                retry_after_seconds=0.0,
            )
        return AssistantProviderResult(
            final_response={
                "answer": "Use the prepared facts.",
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text="Use the prepared facts.",
            provider_name="openai",
            provider_mode="openai",
            model_name=request.model_name_override or "gpt-4o",
        )


@dataclass
class _FallbackProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        if request.model_name_override != "gpt-4o-mini":
            raise AssistantProviderRateLimitError(
                "Rate limit reached. Try again in 0s.",
                retry_after_seconds=0.0,
            )
        return AssistantProviderResult(
            final_response={
                "answer": "Fallback model answered.",
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text="Fallback model answered.",
            provider_name="openai",
            provider_mode="openai",
            model_name="gpt-4o-mini",
        )

def test_rate_limit_retry_uses_smaller_request_before_success() -> None:
    provider = _RetryingProvider()
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-4o",
            rate_limit_max_retries=1,
            rate_limit_retry_seconds=0,
        ),
        repository=repository,
        provider=provider,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="How do I create a customer?"),
        _context(),
    )

    assert response.answer == "Use the prepared facts."
    assert len(provider.requests) == 2
    assert provider.requests[1].max_output_tokens < provider.requests[0].max_output_tokens
    assert provider.requests[1].metadata["rate_limit_retry_compacted"] is True


def test_rate_limit_fallback_model_is_used_when_configured() -> None:
    provider = _FallbackProvider()
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-4o",
            rate_limit_max_retries=0,
            rate_limit_retry_seconds=0,
            fallback_response_model="gpt-4o-mini",
        ),
        repository=repository,
        provider=provider,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="How do I create a customer?"),
        _context(),
    )

    assert response.answer == "Fallback model answered."
    assert len(provider.requests) == 2
    assert provider.requests[1].model_name_override == "gpt-4o-mini"
