from __future__ import annotations

import pytest

from app.errors import ApiException
from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_capabilities import _NoopAssistantRepository


def _context(*permission_keys: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permission_keys),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )


def _service(*, provider_mode: str, mock_provider_allowed: bool, openai_configured: bool) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode=provider_mode,
            env="development",
            openai_configured=openai_configured,
            mock_provider_allowed=mock_provider_allowed,
            response_model="gpt-5.5-mini" if provider_mode == "openai" else "mock-assistant-v1",
            store_responses=False,
        ),
        repository=_NoopAssistantRepository(),
        provider=MockAssistantProvider(),
    )


def test_capabilities_expose_provider_reality_in_mock_mode() -> None:
    payload = _service(
        provider_mode="mock",
        mock_provider_allowed=False,
        openai_configured=False,
    ).get_capabilities(_context("assistant.chat.access"))

    assert payload.provider_mode == "mock"
    assert payload.mock_provider_allowed is False
    assert payload.openai_configured is False
    assert payload.rag_enabled is False
    assert payload.can_chat is False


def test_capabilities_expose_provider_reality_in_openai_mode() -> None:
    payload = _service(
        provider_mode="openai",
        mock_provider_allowed=False,
        openai_configured=True,
    ).get_capabilities(_context("assistant.chat.access"))

    assert payload.provider_mode == "openai"
    assert payload.openai_configured is True
    assert payload.rag_enabled is True
    assert payload.can_chat is True


def test_provider_status_requires_admin_permission() -> None:
    with pytest.raises(ApiException) as exc_info:
        _service(
            provider_mode="openai",
            mock_provider_allowed=False,
            openai_configured=True,
        ).get_provider_status(_context("assistant.chat.access"))

    assert exc_info.value.code == "iam.authorization.permission_denied"


def test_provider_status_returns_safe_configuration_fields() -> None:
    payload = _service(
        provider_mode="openai",
        mock_provider_allowed=False,
        openai_configured=True,
    ).get_provider_status(_context("assistant.admin"))

    assert payload.model_dump(mode="json") == {
        "provider_mode": "openai",
        "openai_configured": True,
        "model": "gpt-5.5-mini",
        "mock_provider_allowed": False,
        "store_responses": False,
        "rag_enabled": True,
    }
