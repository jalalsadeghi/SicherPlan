from __future__ import annotations

import pytest

from app.errors import ApiException
from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


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


def test_mock_provider_not_allowed_returns_safe_error_for_message_send() -> None:
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
            provider_mode="mock",
            env="development",
            mock_provider_allowed=False,
            response_model="mock-assistant-v1",
        ),
        repository=repository,
        provider=MockAssistantProvider(),
    )

    with pytest.raises(ApiException) as exc_info:
        service.add_message(
            conversation.id,
            AssistantMessageCreate(message="How do I create a new order in SicherPlan?"),
            _context("assistant.chat.access"),
        )

    assert exc_info.value.code == "assistant.provider.mock_not_allowed"
    assert exc_info.value.message_key == "errors.assistant.provider.mock_not_allowed"
