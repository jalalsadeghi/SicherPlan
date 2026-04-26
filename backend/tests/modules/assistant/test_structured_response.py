from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.assistant.models import AssistantConversation, AssistantMessage
from app.modules.assistant.provider import MockAssistantProvider, mock_provider_answer
from app.modules.assistant.router import get_assistant_service
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext, get_request_authorization_context


def _context(
    *,
    permission_keys: tuple[str, ...] = ("assistant.chat.access",),
    tenant_id: str = "tenant-1",
    user_id: str = "assistant-user-1",
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id=user_id,
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permission_keys),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )


@dataclass
class InMemoryAssistantRepository:
    conversations: dict[str, AssistantConversation] = field(default_factory=dict)
    messages: dict[str, list[AssistantMessage]] = field(default_factory=dict)
    counter: int = 0

    def create_conversation(
        self,
        *,
        tenant_id: str | None,
        user_id: str,
        title: str | None,
        locale: str | None,
        last_route_name: str | None,
        last_route_path: str | None,
    ) -> AssistantConversation:
        now = self._next_time()
        conversation = AssistantConversation(
            id=str(uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            locale=locale,
            status="active",
            last_route_name=last_route_name,
            last_route_path=last_route_path,
            created_at=now,
            updated_at=now,
            archived_at=None,
        )
        conversation.messages = []
        self.conversations[conversation.id] = conversation
        self.messages[conversation.id] = []
        return conversation

    def get_conversation_for_user(self, *, conversation_id: str, tenant_id: str | None, user_id: str) -> AssistantConversation | None:
        conversation = self.conversations.get(conversation_id)
        if conversation is None or conversation.user_id != user_id or conversation.tenant_id != tenant_id:
            return None
        conversation.messages = self.list_messages_for_conversation(conversation_id)
        return conversation

    def list_messages_for_conversation(self, conversation_id: str) -> list[AssistantMessage]:
        return sorted(self.messages.get(conversation_id, []), key=lambda row: row.created_at)

    def update_conversation_route_context(self, conversation: AssistantConversation, *, last_route_name: str | None, last_route_path: str | None) -> None:
        conversation.last_route_name = last_route_name
        conversation.last_route_path = last_route_path
        conversation.updated_at = self._next_time()

    def create_messages(self, conversation: AssistantConversation, messages: list[AssistantMessage]) -> list[AssistantMessage]:
        stored = self.messages.setdefault(conversation.id, [])
        for message in messages:
            message.id = message.id or str(uuid4())
            message.created_at = self._next_time()
            stored.append(message)
        conversation.updated_at = self._next_time()
        conversation.messages = self.list_messages_for_conversation(conversation.id)
        return list(messages)

    def update_message_payload(self, message: AssistantMessage, *, structured_payload: dict[str, object]) -> None:
        message.structured_payload = structured_payload

    def _next_time(self) -> datetime:
        base = datetime(2026, 4, 26, 12, 0, 0, tzinfo=UTC)
        next_value = base + timedelta(seconds=self.counter)
        self.counter += 1
        return next_value


def _service(repository: InMemoryAssistantRepository, *, enabled: bool = True) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=enabled,
            provider_mode="mock",
            max_input_chars=200,
        ),
        repository=repository,
        provider=MockAssistantProvider(),
    )


def test_sending_message_returns_structured_response_and_persists_payload() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="fa",
        last_route_name=None,
        last_route_path=None,
    )
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context()
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={
                "message": "shift not visible",
                "client_context": {"ui_locale": "fa"},
            },
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["conversation_id"] == conversation.id
        assert payload["message_id"]
        assert payload["detected_language"] == "fa"
        assert payload["response_language"] == "fa"
        assert payload["answer"] == mock_provider_answer("fa")
        assert payload["scope"] == "tenant"
        assert payload["confidence"] == "low"
        assert payload["out_of_scope"] is False
        assert isinstance(payload["diagnosis"], list)
        assert payload["diagnosis"][0]["finding"] == "پاسخ ساختاریافتهٔ موقت Assistant فعال است."
        assert isinstance(payload["links"], list)
        assert isinstance(payload["missing_permissions"], list)
        assert isinstance(payload["next_steps"], list)
        assert payload["tool_trace_id"] is None

        stored_conversation = repository.get_conversation_for_user(
            conversation_id=conversation.id,
            tenant_id="tenant-1",
            user_id="assistant-user-1",
        )
        assert stored_conversation is not None
        assistant_message = stored_conversation.messages[-1]
        assert assistant_message.role == "assistant"
        assert assistant_message.structured_payload is not None
        assert assistant_message.structured_payload["conversation_id"] == conversation.id
        assert assistant_message.structured_payload["message_id"] == assistant_message.id
        assert assistant_message.structured_payload["detected_language"] == "fa"
        assert assistant_message.structured_payload["response_language"] == "fa"

    app.dependency_overrides.clear()


def test_structured_response_defaults_to_en_for_english_input_without_locale_context() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale=None,
        last_route_name=None,
        last_route_path=None,
    )
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context()
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={"message": "hello"},
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["detected_language"] == "en"
        assert payload["response_language"] == "en"
        assert payload["answer"] == mock_provider_answer("en")

    app.dependency_overrides.clear()


def test_unauthorized_users_cannot_get_structured_response() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale=None,
        last_route_name=None,
        last_route_path=None,
    )
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(permission_keys=())
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={"message": "hello"},
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "iam.authorization.permission_denied"

    app.dependency_overrides.clear()


def test_disabled_assistant_behavior_unchanged_for_structured_response() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale=None,
        last_route_name=None,
        last_route_path=None,
    )
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context()
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository, enabled=False)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={"message": "hello"},
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "assistant.disabled"

    app.dependency_overrides.clear()
