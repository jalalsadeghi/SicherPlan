from __future__ import annotations

from dataclasses import dataclass

from app.errors import ApiException
from app.modules.assistant.provider import AssistantProviderRateLimitError
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from tests.modules.assistant.test_how_to_employee_create_exact_ui import (
    _context as _page_help_context,
    _repository as _page_help_repository,
)
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository, _context as _basic_context


@dataclass
class _RateLimitedProvider:
    def generate(self, request):  # noqa: ANN001, ANN201
        raise AssistantProviderRateLimitError("Rate limit reached.", retry_after_seconds=0.0)


def test_provider_failure_without_grounding_still_returns_safe_error() -> None:
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
        ),
        repository=repository,
        provider=_RateLimitedProvider(),
    )

    try:
        service.add_message(
            conversation.id,
            AssistantMessageCreate(message="How do I create a customer?"),
            _basic_context(),
        )
    except ApiException as exc:
        assert exc.status_code == 503
        assert exc.code == "assistant.provider.rate_limited"
    else:
        raise AssertionError("Expected safe provider error when no grounded fallback exists.")


def test_permission_denial_never_uses_fallback() -> None:
    repository = _page_help_repository()
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
        ),
        repository=repository,
        provider=_RateLimitedProvider(),
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            page_help_repository=repository,
        ),
    )

    try:
        service.add_message(
            conversation.id,
            AssistantMessageCreate(message="How do I create a new Employee?"),
            _page_help_context("employees.employee.read"),
        )
    except ApiException as exc:
        assert exc.status_code == 403
        assert exc.code == "iam.authorization.permission_denied"
    else:
        raise AssertionError("Expected permission denial before any degraded fallback.")
