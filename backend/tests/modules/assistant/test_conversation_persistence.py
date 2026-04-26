from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.assistant.models import AssistantConversation, AssistantMessage
from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.router import get_assistant_service
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext, get_request_authorization_context


def _context(
    *,
    tenant_id: str = "tenant-1",
    user_id: str = "assistant-user-1",
    permission_keys: tuple[str, ...] = (),
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

    def get_conversation_for_user(
        self,
        *,
        conversation_id: str,
        tenant_id: str | None,
        user_id: str,
    ) -> AssistantConversation | None:
        conversation = self.conversations.get(conversation_id)
        if conversation is None:
            return None
        if conversation.user_id != user_id:
            return None
        if conversation.tenant_id != tenant_id:
            return None
        conversation.messages = self.list_messages_for_conversation(conversation_id)
        return conversation

    def list_messages_for_conversation(self, conversation_id: str) -> list[AssistantMessage]:
        return sorted(self.messages.get(conversation_id, []), key=lambda row: row.created_at)

    def update_conversation_route_context(
        self,
        conversation: AssistantConversation,
        *,
        last_route_name: str | None,
        last_route_path: str | None,
    ) -> None:
        conversation.last_route_name = last_route_name
        conversation.last_route_path = last_route_path
        conversation.updated_at = self._next_time()

    def create_messages(
        self,
        conversation: AssistantConversation,
        messages: list[AssistantMessage],
    ) -> list[AssistantMessage]:
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


def _service(
    repository: InMemoryAssistantRepository,
    *,
    enabled: bool = True,
    provider_mode: str = "mock",
    max_input_chars: int = 200,
) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=enabled,
            provider_mode=provider_mode,
            max_input_chars=max_input_chars,
        ),
        repository=repository,
        provider=MockAssistantProvider(),
    )


def test_create_conversation_requires_assistant_enabled() -> None:
    repository = InMemoryAssistantRepository()
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(
        permission_keys=("assistant.chat.access",)
    )
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository, enabled=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/assistant/conversations",
            json={"locale": "fa"},
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "assistant.disabled"

    app.dependency_overrides.clear()


def test_create_conversation_requires_chat_permission() -> None:
    repository = InMemoryAssistantRepository()
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context()
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            "/api/assistant/conversations",
            json={"locale": "fa"},
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "iam.authorization.permission_denied"

    app.dependency_overrides.clear()


def test_create_conversation_success() -> None:
    repository = InMemoryAssistantRepository()
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(
        permission_keys=("assistant.chat.access",)
    )
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            "/api/assistant/conversations",
            json={
                "locale": "fa",
                "title": "Markus mobile app",
                "initial_route": {
                    "path": "/admin/planning-staffing",
                    "route_name": "SicherPlanPlanningStaffing",
                    "page_id": "P-04",
                    "query": {"date": "2026-05-01"},
                },
            },
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["tenant_id"] == "tenant-1"
        assert payload["user_id"] == "assistant-user-1"
        assert payload["locale"] == "fa"
        assert payload["title"] == "Markus mobile app"
        assert payload["last_route_name"] == "SicherPlanPlanningStaffing"
        assert payload["last_route_path"] == "/admin/planning-staffing"
        assert payload["messages"] == []

    app.dependency_overrides.clear()


def test_get_own_conversation_success() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    repository.create_messages(
        conversation,
        [
            AssistantMessage(
                conversation_id=conversation.id,
                tenant_id="tenant-1",
                user_id="assistant-user-1",
                role="user",
                content="first",
            ),
            AssistantMessage(
                conversation_id=conversation.id,
                tenant_id="tenant-1",
                user_id=None,
                role="assistant",
                content="second",
            ),
        ],
    )

    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(
        permission_keys=("assistant.chat.access",)
    )
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.get(
            f"/api/assistant/conversations/{conversation.id}",
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["id"] == conversation.id
        assert [item["content"] for item in payload["messages"]] == ["first", "second"]

    app.dependency_overrides.clear()


def test_get_other_user_conversation_blocked() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="other-user",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(
        permission_keys=("assistant.chat.access",)
    )
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.get(
            f"/api/assistant/conversations/{conversation.id}",
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "assistant.conversation.not_found"

    app.dependency_overrides.clear()


def test_get_other_tenant_conversation_blocked() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-2",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(
        tenant_id="tenant-1",
        permission_keys=("assistant.chat.access",),
    )
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.get(
            f"/api/assistant/conversations/{conversation.id}",
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "assistant.conversation.not_found"

    app.dependency_overrides.clear()


def test_send_message_success() -> None:
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
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(
        permission_keys=("assistant.chat.access",)
    )
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={
                "message": "  Markus sees no shift  ",
                "route_context": {
                    "path": "/admin/planning-staffing",
                    "route_name": "SicherPlanPlanningStaffing",
                    "page_id": "P-04",
                    "query": {"date": "2026-05-01"},
                },
                "client_context": {
                    "timezone": "Europe/Berlin",
                    "ui_locale": "fa",
                    "visible_page_title": "Staffing Board",
                },
            },
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["conversation_id"] == conversation.id
        assert payload["answer"]
        assert payload["detected_language"] == "en"
        assert payload["response_language"] == "en"
        assert payload["tool_trace_id"] is None

        follow_up = client.get(
            f"/api/assistant/conversations/{conversation.id}",
            headers={"Authorization": "Bearer test-access"},
        )
        assert follow_up.status_code == 200
        conversation_payload = follow_up.json()
        assert conversation_payload["last_route_name"] == "SicherPlanPlanningStaffing"
        assert conversation_payload["last_route_path"] == "/admin/planning-staffing"
        assert len(conversation_payload["messages"]) == 2
        assert conversation_payload["messages"][0]["role"] == "user"
        assert conversation_payload["messages"][0]["content"] == "Markus sees no shift"
        assert conversation_payload["messages"][0]["detected_language"] == "en"
        assert conversation_payload["messages"][0]["response_language"] == "en"
        assert conversation_payload["messages"][0]["structured_payload"]["detected_language"] == "en"
        assert conversation_payload["messages"][0]["structured_payload"]["response_language"] == "en"
        assert conversation_payload["messages"][1]["role"] == "assistant"
        assert conversation_payload["messages"][1]["structured_payload"]["conversation_id"] == conversation.id

    app.dependency_overrides.clear()


def test_send_empty_message_rejected() -> None:
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
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(
        permission_keys=("assistant.chat.access",)
    )
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={"message": "   "},
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "assistant.validation.message_empty"

    app.dependency_overrides.clear()


def test_send_too_long_message_rejected() -> None:
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
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(
        permission_keys=("assistant.chat.access",)
    )
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository, max_input_chars=5)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={"message": "123456"},
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "assistant.validation.message_too_long"

    app.dependency_overrides.clear()


def test_send_message_to_other_user_conversation_blocked() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="other-user",
        title=None,
        locale=None,
        last_route_name=None,
        last_route_path=None,
    )
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(
        permission_keys=("assistant.chat.access",)
    )
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={"message": "hello"},
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "assistant.conversation.not_found"

    app.dependency_overrides.clear()


def test_route_context_is_stored_as_non_authoritative_metadata() -> None:
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
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(
        permission_keys=("assistant.chat.access",)
    )
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={
                "message": "hello",
                "route_context": {
                    "path": "/admin/planning",
                    "route_name": "Route",
                    "page_id": "P-01",
                    "query": {
                        "tenant_id": "tenant-override",
                        "user_id": "user-override",
                        "date": "2026-05-01",
                    },
                },
                "client_context": {
                    "timezone": "Europe/Berlin",
                    "ui_locale": "de",
                    "visible_page_title": "Planning",
                },
            },
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 201
        follow_up = client.get(
            f"/api/assistant/conversations/{conversation.id}",
            headers={"Authorization": "Bearer test-access"},
        )
        assert follow_up.status_code == 200
        user_message = follow_up.json()["messages"][0]
        payload = user_message["structured_payload"]
        assert payload["route_context"]["query"] == {"date": "2026-05-01"}
        assert "tenant_id" not in payload["route_context"]["query"]
        assert "user_id" not in payload["route_context"]["query"]

    app.dependency_overrides.clear()


def test_conversation_messages_ordered_by_created_at() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale=None,
        last_route_name=None,
        last_route_path=None,
    )
    repository.create_messages(
        conversation,
        [
            AssistantMessage(
                conversation_id=conversation.id,
                tenant_id="tenant-1",
                user_id=None,
                role="assistant",
                content="first",
            ),
            AssistantMessage(
                conversation_id=conversation.id,
                tenant_id="tenant-1",
                user_id="assistant-user-1",
                role="user",
                content="second",
            ),
        ],
    )
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(
        permission_keys=("assistant.chat.access",)
    )
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.get(
            f"/api/assistant/conversations/{conversation.id}",
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 200
        assert [item["content"] for item in response.json()["messages"]] == ["first", "second"]

    app.dependency_overrides.clear()
