from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.assistant.language import (
    choose_response_language,
    detect_message_language,
    language_instruction,
)
from app.modules.assistant.models import AssistantConversation, AssistantMessage
from app.modules.assistant.provider import MockAssistantProvider, mock_provider_answer
from app.modules.assistant.router import get_assistant_service
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext, get_request_authorization_context


def _context() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"assistant.chat.access"}),
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


def _service(repository: InMemoryAssistantRepository) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="mock",
            max_input_chars=400,
        ),
        repository=repository,
        provider=MockAssistantProvider(),
    )


def _conversation(repository: InMemoryAssistantRepository, *, locale: str | None = None) -> AssistantConversation:
    return repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale=locale,
        last_route_name=None,
        last_route_path=None,
    )


def test_detects_persian_message_as_fa() -> None:
    assert detect_message_language("من برای Markus شیفت ثبت کردم ولی نمایش داده نمی‌شود") == "fa"


def test_detects_german_message_as_de() -> None:
    assert detect_message_language("Warum wird der Mitarbeiter nicht angezeigt?") == "de"


def test_detects_english_message_as_en() -> None:
    assert detect_message_language("Why is the employee shift not visible?") == "en"


def test_detects_mixed_persian_and_technical_english_as_fa() -> None:
    assert detect_message_language("من برای Markus یک Shift assigned کردم ولی در App نمایش داده نمی‌شود") == "fa"


def test_detects_german_message_with_umlauts_as_de() -> None:
    assert detect_message_language("Warum wird die Schicht für Jörg nicht angezeigt?") == "de"


def test_detects_german_message_without_umlauts_as_de() -> None:
    assert detect_message_language("Wie kann ich die Schicht fur den Mitarbeiter freigeben?") == "de"


def test_ambiguous_latin_text_falls_back_to_en() -> None:
    assert detect_message_language("Status check") == "en"


def test_ui_locale_used_when_message_language_is_ambiguous() -> None:
    assert detect_message_language("12345", ui_locale="de-DE") == "de"
    assert choose_response_language("unknown", "fa-IR") == "fa"


def test_technical_terms_do_not_switch_language() -> None:
    assert detect_message_language("چگونه Route Catalog و Tool Registry را بررسی کنم؟") == "fa"
    assert detect_message_language("Warum ist der Shift Plan im Staffing Board nicht sichtbar?") == "de"


def test_language_instruction_mentions_same_language_rule() -> None:
    instruction = language_instruction("fa")
    assert "same language" in instruction
    assert "fa" in instruction


def test_persian_message_returns_fa_and_persian_placeholder() -> None:
    repository = InMemoryAssistantRepository()
    conversation = _conversation(repository)
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context()
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={"message": "چگونه دسترسی کارمند را در SicherPlan بازنشانی کنم؟"},
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["detected_language"] == "fa"
        assert payload["response_language"] == "fa"
        assert payload["answer"] == mock_provider_answer("fa")
        assert payload["diagnosis"][0]["finding"] == "پاسخ ساختاریافتهٔ موقت Assistant فعال است."

    app.dependency_overrides.clear()


def test_german_message_returns_de_and_german_placeholder() -> None:
    repository = InMemoryAssistantRepository()
    conversation = _conversation(repository)
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context()
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={"message": "Wie kann ich den Mitarbeiterzugang in SicherPlan zuruecksetzen?"},
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["detected_language"] == "de"
        assert payload["response_language"] == "de"
        assert payload["answer"] == mock_provider_answer("de")
        assert payload["diagnosis"][0]["finding"] == "Der strukturierte Platzhaltermodus des Assistant ist aktiv."

    app.dependency_overrides.clear()


def test_english_message_returns_en_and_english_placeholder() -> None:
    repository = InMemoryAssistantRepository()
    conversation = _conversation(repository)
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context()
    app.dependency_overrides[get_assistant_service] = lambda: _service(repository)

    with TestClient(app) as client:
        response = client.post(
            f"/api/assistant/conversations/{conversation.id}/messages",
            json={"message": "How do I reset employee access in SicherPlan?"},
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["detected_language"] == "en"
        assert payload["response_language"] == "en"
        assert payload["answer"] == mock_provider_answer("en")
        assert payload["diagnosis"][0]["finding"] == "Structured response placeholder active."

    app.dependency_overrides.clear()
