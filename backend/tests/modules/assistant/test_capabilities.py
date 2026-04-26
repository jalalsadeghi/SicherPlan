from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.assistant.models import AssistantConversation, AssistantMessage
from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.router import get_assistant_service
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext, get_request_authorization_context


class _NoopAssistantRepository:
    def create_conversation(self, **kwargs) -> AssistantConversation:  # noqa: ANN003
        raise AssertionError("not used")

    def get_conversation_for_user(self, **kwargs) -> AssistantConversation | None:  # noqa: ANN003
        raise AssertionError("not used")

    def list_messages_for_conversation(self, conversation_id: str) -> list[AssistantMessage]:
        raise AssertionError("not used")

    def update_conversation_route_context(self, conversation: AssistantConversation, **kwargs) -> None:  # noqa: ANN003
        raise AssertionError("not used")

    def create_messages(self, conversation: AssistantConversation, messages: list[AssistantMessage]) -> list[AssistantMessage]:
        raise AssertionError("not used")

    def update_message_payload(self, message: AssistantMessage, **kwargs) -> None:  # noqa: ANN003
        raise AssertionError("not used")


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


def _service(*, enabled: bool, provider_mode: str) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=enabled,
            provider_mode=provider_mode,
        ),
        repository=_NoopAssistantRepository(),
        provider=MockAssistantProvider(),
    )


def test_assistant_capabilities_disabled_returns_disabled_state() -> None:
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context("assistant.chat.access")
    app.dependency_overrides[get_assistant_service] = lambda: _service(enabled=False, provider_mode="mock")

    with TestClient(app) as client:
        response = client.get(
            "/api/assistant/capabilities",
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["enabled"] is False
        assert payload["provider_mode"] == "mock"
        assert payload["can_chat"] is False
        assert payload["can_run_diagnostics"] is False
        assert payload["can_reindex_knowledge"] is False
        assert payload["supported_features"] == []

    app.dependency_overrides.clear()


def test_assistant_capabilities_enabled_with_chat_permission() -> None:
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context("assistant.chat.access")
    app.dependency_overrides[get_assistant_service] = lambda: _service(enabled=True, provider_mode="mock")

    with TestClient(app) as client:
        response = client.get(
            "/api/assistant/capabilities",
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["enabled"] is True
        assert payload["provider_mode"] == "mock"
        assert payload["can_chat"] is True
        assert payload["can_run_diagnostics"] is False
        assert payload["can_reindex_knowledge"] is False
        assert "mock_provider_ready" in payload["supported_features"]

    app.dependency_overrides.clear()


def test_assistant_capabilities_enabled_without_chat_permission() -> None:
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context()
    app.dependency_overrides[get_assistant_service] = lambda: _service(enabled=True, provider_mode="mock")

    with TestClient(app) as client:
        response = client.get(
            "/api/assistant/capabilities",
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["enabled"] is True
        assert payload["can_chat"] is False
        assert payload["can_run_diagnostics"] is False
        assert payload["can_reindex_knowledge"] is False

    app.dependency_overrides.clear()


def test_assistant_capabilities_diagnostics_permission() -> None:
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context("assistant.diagnostics.read")
    app.dependency_overrides[get_assistant_service] = lambda: _service(enabled=True, provider_mode="mock")

    with TestClient(app) as client:
        response = client.get(
            "/api/assistant/capabilities",
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["can_chat"] is False
        assert payload["can_run_diagnostics"] is True

    app.dependency_overrides.clear()


def test_assistant_capabilities_reindex_permission() -> None:
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context("assistant.knowledge.reindex")
    app.dependency_overrides[get_assistant_service] = lambda: _service(enabled=True, provider_mode="openai")

    with TestClient(app) as client:
        response = client.get(
            "/api/assistant/capabilities",
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["provider_mode"] == "openai"
        assert payload["can_reindex_knowledge"] is True
        assert "openai_provider_configured" in payload["supported_features"]

    app.dependency_overrides.clear()


def test_assistant_capabilities_does_not_require_openai_key_in_mock_or_disabled_mode() -> None:
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context("assistant.chat.access")
    services = iter(
        (
            _service(enabled=False, provider_mode="mock"),
            _service(enabled=True, provider_mode="mock"),
        )
    )
    app.dependency_overrides[get_assistant_service] = lambda: next(services)

    with TestClient(app) as client:
        disabled_response = client.get(
            "/api/assistant/capabilities",
            headers={"Authorization": "Bearer test-access"},
        )
        mock_response = client.get(
            "/api/assistant/capabilities",
            headers={"Authorization": "Bearer test-access"},
        )

        assert disabled_response.status_code == 200
        assert disabled_response.json()["enabled"] is False
        assert mock_response.status_code == 200
        assert mock_response.json()["enabled"] is True
        assert mock_response.json()["provider_mode"] == "mock"

    app.dependency_overrides.clear()
