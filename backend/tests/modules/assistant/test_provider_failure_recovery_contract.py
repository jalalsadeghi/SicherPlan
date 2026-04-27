from __future__ import annotations

from dataclasses import dataclass

from app.errors import ApiException
from app.modules.assistant.provider import (
    AssistantProviderAuthenticationError,
    AssistantProviderInvalidRequestError,
)
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from tests.modules.assistant.test_how_to_employee_create_exact_ui import (
    _context as _page_help_context,
    _repository as _page_help_repository,
)
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository, _context as _basic_context
from tests.modules.assistant.test_shift_visibility_diagnostic import (
    _DiagnosticRepository,
    _context,
    _full_internal_permissions,
)


@dataclass
class _AuthFailingProvider:
    def generate(self, request):  # noqa: ANN001, ANN201
        raise AssistantProviderAuthenticationError("Bad API key.")


@dataclass
class _InvalidRequestProvider:
    def generate(self, request):  # noqa: ANN001, ANN201
        raise AssistantProviderInvalidRequestError("Structured response validation failed.")


def test_provider_auth_error_without_grounding_still_returns_safe_error() -> None:
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
        ),
        repository=repository,
        provider=_AuthFailingProvider(),
    )

    try:
        service.add_message(
            conversation.id,
            AssistantMessageCreate(message="How do I create a customer?"),
            _basic_context(),
        )
    except ApiException as exc:
        assert exc.status_code == 503
        assert exc.code == "assistant.provider.authentication_failed"
    else:
        raise AssertionError("Expected safe provider error when no grounded fallback exists.")


def test_invalid_request_with_grounding_now_returns_degraded_response() -> None:
    repository = _DiagnosticRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="dispatcher-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-4o",
        ),
        repository=repository,
        provider=_InvalidRequestProvider(),
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            employee_repository=repository,
            planning_repository=repository,
        ),
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="Ich habe Markus einer Schicht zugewiesen, aber sie ist in der mobilen App nicht sichtbar. Woran liegt das?"
        ),
        _context(role_keys=("dispatcher",), permission_keys=_full_internal_permissions()),
    )

    assert response.provider_degraded is True
    assert response.source_basis
    assert any(item.finding == "provider_degraded" for item in response.diagnosis)


def test_out_of_scope_request_never_uses_degraded_provider_fallback() -> None:
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
        ),
        repository=repository,
        provider=_InvalidRequestProvider(),
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="What is the weather in Berlin?"),
        _basic_context(),
    )

    assert response.out_of_scope is True
    assert response.provider_degraded is False


def test_permission_denial_never_uses_fallback_leakage() -> None:
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
        ),
        repository=repository,
        provider=_InvalidRequestProvider(),
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
