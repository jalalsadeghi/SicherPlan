from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.errors import ApiException
from app.modules.assistant.models import AssistantConversation, AssistantFeedback, AssistantMessage
from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.schemas import AssistantFeedbackCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from tests.modules.assistant.test_conversation_persistence import _context


@dataclass
class InMemoryAssistantFeedbackRepository:
    conversations: dict[str, AssistantConversation] = field(default_factory=dict)
    feedback_rows: dict[tuple[str, str, str], AssistantFeedback] = field(default_factory=dict)
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
        if conversation.user_id != user_id or conversation.tenant_id != tenant_id:
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

    def get_message_for_conversation(
        self,
        *,
        conversation_id: str,
        message_id: str,
    ) -> AssistantMessage | None:
        for message in self.messages.get(conversation_id, []):
            if message.id == message_id:
                return message
        return None

    def upsert_feedback(
        self,
        *,
        conversation_id: str,
        message_id: str,
        tenant_id: str | None,
        user_id: str,
        rating: str,
        comment: str | None,
    ) -> AssistantFeedback:
        key = (conversation_id, message_id, user_id)
        row = self.feedback_rows.get(key)
        if row is None:
            row = AssistantFeedback(
                id=str(uuid4()),
                conversation_id=conversation_id,
                message_id=message_id,
                tenant_id=tenant_id,
                user_id=user_id,
                rating=rating,
                comment=comment,
                created_at=self._next_time(),
            )
            self.feedback_rows[key] = row
            return row
        row.tenant_id = tenant_id
        row.rating = rating
        row.comment = comment
        return row

    def _next_time(self) -> datetime:
        base = datetime(2026, 4, 26, 12, 0, 0, tzinfo=UTC)
        next_value = base + timedelta(seconds=self.counter)
        self.counter += 1
        return next_value


def _service(repository: InMemoryAssistantFeedbackRepository, *, enabled: bool = True) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(enabled=enabled, provider_mode="mock"),
        repository=repository,
        provider=MockAssistantProvider(),
    )


def _conversation_with_messages(
    repository: InMemoryAssistantFeedbackRepository,
) -> tuple[AssistantConversation, AssistantMessage, AssistantMessage]:
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    user_message, assistant_message = repository.create_messages(
        conversation,
        [
            AssistantMessage(
                conversation_id=conversation.id,
                tenant_id="tenant-1",
                user_id="assistant-user-1",
                role="user",
                content="Warum sieht Markus die Schicht nicht?",
            ),
            AssistantMessage(
                conversation_id=conversation.id,
                tenant_id="tenant-1",
                user_id=None,
                role="assistant",
                content="Die Schicht ist noch nicht freigegeben.",
            ),
        ],
    )
    return conversation, user_message, assistant_message


def test_submit_feedback_success() -> None:
    repository = InMemoryAssistantFeedbackRepository()
    conversation, _, assistant_message = _conversation_with_messages(repository)
    service = _service(repository)

    result = service.submit_feedback(
        conversation.id,
        AssistantFeedbackCreate(message_id=assistant_message.id, rating="helpful"),
        _context(permission_keys=("assistant.chat.access", "assistant.feedback.write")),
    )

    assert result.conversation_id == conversation.id
    assert result.message_id == assistant_message.id
    assert result.rating == "helpful"
    assert len(repository.feedback_rows) == 1


def test_submit_feedback_requires_feedback_permission() -> None:
    repository = InMemoryAssistantFeedbackRepository()
    conversation, _, assistant_message = _conversation_with_messages(repository)
    service = _service(repository)

    with pytest.raises(ApiException) as exc:
        service.submit_feedback(
            conversation.id,
            AssistantFeedbackCreate(message_id=assistant_message.id, rating="helpful"),
            _context(permission_keys=("assistant.chat.access",)),
        )

    assert exc.value.code == "iam.authorization.permission_denied"
    assert exc.value.details["permission_key"] == "assistant.feedback.write"


def test_submit_feedback_rejects_user_messages() -> None:
    repository = InMemoryAssistantFeedbackRepository()
    conversation, user_message, _ = _conversation_with_messages(repository)
    service = _service(repository)

    with pytest.raises(ApiException) as exc:
        service.submit_feedback(
            conversation.id,
            AssistantFeedbackCreate(
                message_id=user_message.id,
                rating="not_helpful",
                comment="Should not be accepted",
            ),
            _context(permission_keys=("assistant.chat.access", "assistant.feedback.write")),
        )

    assert exc.value.code == "assistant.feedback.invalid_target"


def test_submit_feedback_updates_existing_row_for_same_user_and_message() -> None:
    repository = InMemoryAssistantFeedbackRepository()
    conversation, _, assistant_message = _conversation_with_messages(repository)
    service = _service(repository)
    actor = _context(permission_keys=("assistant.chat.access", "assistant.feedback.write"))

    first = service.submit_feedback(
        conversation.id,
        AssistantFeedbackCreate(message_id=assistant_message.id, rating="helpful"),
        actor,
    )
    second = service.submit_feedback(
        conversation.id,
        AssistantFeedbackCreate(
            message_id=assistant_message.id,
            rating="not_helpful",
            comment="Need more detail",
        ),
        actor,
    )

    assert second.id == first.id
    row = next(iter(repository.feedback_rows.values()))
    assert row.rating == "not_helpful"
    assert row.comment == "Need more detail"
    assert len(repository.feedback_rows) == 1


def test_submit_feedback_blocks_other_user_conversation() -> None:
    repository = InMemoryAssistantFeedbackRepository()
    conversation, _, assistant_message = _conversation_with_messages(repository)
    service = _service(repository)

    with pytest.raises(ApiException) as exc:
        service.submit_feedback(
            conversation.id,
            AssistantFeedbackCreate(message_id=assistant_message.id, rating="helpful"),
            _context(
                user_id="other-user",
                permission_keys=("assistant.chat.access", "assistant.feedback.write"),
            ),
        )

    assert exc.value.code == "assistant.conversation.not_found"
