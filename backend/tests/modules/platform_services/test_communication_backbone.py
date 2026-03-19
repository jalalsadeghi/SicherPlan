from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from app.db import Base
from app.errors import ApiException
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.comm_models import DeliveryAttempt, MessageRecipient, MessageTemplate, OutboundMessage
from app.modules.platform_services.comm_schemas import (
    DeliveryAttemptCreate,
    MessageRecipientCreate,
    MessageTemplateUpsert,
    RenderedMessageCreate,
)
from app.modules.platform_services.comm_service import CommunicationService


@dataclass
class FakeTemplate:
    id: str
    tenant_id: str
    channel: str
    template_key: str
    language_code: str
    subject_template: str | None
    body_template: str
    metadata_json: dict[str, object] = field(default_factory=dict)
    status: str = "active"
    version_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeRecipient:
    id: str
    tenant_id: str
    outbound_message_id: str
    recipient_kind: str
    destination: str
    display_name: str | None
    user_account_id: str | None
    status: str = "active"
    status_reason: str | None = None
    metadata_json: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeAttempt:
    id: str
    tenant_id: str
    outbound_message_id: str
    recipient_id: str
    provider_key: str
    provider_message_ref: str | None
    outcome: str
    attempt_no: int
    response_code: str | None
    response_summary: str | None
    error_code: str | None
    metadata_json: dict[str, object] = field(default_factory=dict)
    attempted_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeMessage:
    id: str
    tenant_id: str
    template_id: str | None
    channel: str
    template_key: str | None
    language_code: str
    subject_rendered: str | None
    body_rendered: str
    related_entity_type: str | None
    related_entity_id: str | None
    send_started_at: datetime | None
    metadata_json: dict[str, object] = field(default_factory=dict)
    status: str = "active"
    version_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    recipients: list[FakeRecipient] = field(default_factory=list)
    delivery_attempts: list[FakeAttempt] = field(default_factory=list)


class FakeDocumentService:
    def __init__(self) -> None:
        self.document_ids = {"doc-1", "doc-2"}
        self.links: list[tuple[str, str, str, str]] = []

    def get_document(self, tenant_id: str, document_id: str, actor):  # noqa: ANN001
        if document_id not in self.document_ids:
            raise ApiException(404, "docs.document.not_found", "errors.docs.document.not_found")
        return {"id": document_id, "tenant_id": tenant_id}

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.links.append((tenant_id, document_id, payload.owner_type, payload.owner_id))
        return payload


class FakeCommunicationRepository:
    def __init__(self) -> None:
        self.templates: dict[tuple[str, str, str, str], FakeTemplate] = {}
        self.messages: dict[str, FakeMessage] = {}

    def find_template(self, tenant_id: str, channel: str, template_key: str, language_code: str):
        return self.templates.get((tenant_id, channel, template_key, language_code))

    def upsert_template(self, row: MessageTemplate):
        key = (row.tenant_id, row.channel, row.template_key, row.language_code)
        existing = self.templates.get(key)
        if existing is None:
            template = FakeTemplate(
                id=str(uuid4()),
                tenant_id=row.tenant_id,
                channel=row.channel,
                template_key=row.template_key,
                language_code=row.language_code,
                subject_template=row.subject_template,
                body_template=row.body_template,
                metadata_json=row.metadata_json,
            )
            self.templates[key] = template
            return template
        existing.subject_template = row.subject_template
        existing.body_template = row.body_template
        existing.metadata_json = row.metadata_json
        existing.version_no += 1
        existing.updated_at = datetime.now(UTC)
        return existing

    def create_outbound_message(self, message: OutboundMessage, recipients: list[MessageRecipient]):
        stored = FakeMessage(
            id=str(uuid4()),
            tenant_id=message.tenant_id,
            template_id=message.template_id,
            channel=message.channel,
            template_key=message.template_key,
            language_code=message.language_code,
            subject_rendered=message.subject_rendered,
            body_rendered=message.body_rendered,
            related_entity_type=message.related_entity_type,
            related_entity_id=message.related_entity_id,
            send_started_at=message.send_started_at,
            metadata_json=message.metadata_json,
        )
        for recipient in recipients:
            stored.recipients.append(
                FakeRecipient(
                    id=str(uuid4()),
                    tenant_id=recipient.tenant_id,
                    outbound_message_id=stored.id,
                    recipient_kind=recipient.recipient_kind,
                    destination=recipient.destination,
                    display_name=recipient.display_name,
                    user_account_id=recipient.user_account_id,
                    metadata_json=recipient.metadata_json,
                )
            )
        self.messages[stored.id] = stored
        return stored

    def get_outbound_message(self, tenant_id: str, message_id: str):
        message = self.messages.get(message_id)
        if message is None or message.tenant_id != tenant_id:
            return None
        return message

    def get_recipient(self, tenant_id: str, message_id: str, recipient_id: str):
        message = self.get_outbound_message(tenant_id, message_id)
        if message is None:
            return None
        for recipient in message.recipients:
            if recipient.id == recipient_id:
                return recipient
        return None

    def count_attempts_for_recipient(self, recipient_id: str) -> int:
        count = 0
        for message in self.messages.values():
            count += sum(1 for attempt in message.delivery_attempts if attempt.recipient_id == recipient_id)
        return count

    def create_delivery_attempt(self, attempt: DeliveryAttempt):
        message = self.messages[attempt.outbound_message_id]
        stored = FakeAttempt(
            id=str(uuid4()),
            tenant_id=attempt.tenant_id,
            outbound_message_id=attempt.outbound_message_id,
            recipient_id=attempt.recipient_id,
            provider_key=attempt.provider_key,
            provider_message_ref=attempt.provider_message_ref,
            outcome=attempt.outcome,
            attempt_no=attempt.attempt_no,
            response_code=attempt.response_code,
            response_summary=attempt.response_summary,
            error_code=attempt.error_code,
            metadata_json=attempt.metadata_json,
        )
        message.delivery_attempts.append(stored)
        return stored


def _actor(tenant_id: str = "tenant-1") -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"platform.comm.read", "platform.comm.write", "platform.docs.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
    )


class TestCommunicationMetadata(unittest.TestCase):
    def test_expected_comm_tables_are_registered(self) -> None:
        self.assertIn("comm.message_template", Base.metadata.tables)
        self.assertIn("comm.outbound_message", Base.metadata.tables)
        self.assertIn("comm.message_recipient", Base.metadata.tables)
        self.assertIn("comm.delivery_attempt", Base.metadata.tables)

    def test_template_uniqueness_and_delivery_append_only_shape(self) -> None:
        template_constraints = {
            constraint.name
            for constraint in MessageTemplate.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn("uq_comm_message_template_tenant_channel_key_language", template_constraints)
        attempt_columns = {column.name for column in DeliveryAttempt.__table__.columns}
        self.assertNotIn("updated_at", attempt_columns)
        self.assertNotIn("version_no", attempt_columns)
        index_names = {index.name for index in DeliveryAttempt.__table__.indexes if isinstance(index, Index)}
        self.assertIn("ix_comm_delivery_attempt_recipient_attempted_at", index_names)

    def test_recipient_table_is_not_an_opaque_blob(self) -> None:
        ddl = str(CreateTable(MessageRecipient.__table__).compile(dialect=dialect()))
        self.assertIn("destination", ddl)
        self.assertIn("recipient_kind", ddl)
        self.assertIn("user_account_id", ddl)


class TestCommunicationService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeCommunicationRepository()
        self.document_service = FakeDocumentService()
        self.service = CommunicationService(self.repository, document_service=self.document_service)

    def test_template_upsert_and_language_fallback_rendering(self) -> None:
        self.service.upsert_template(
            "tenant-1",
            MessageTemplateUpsert(
                tenant_id="tenant-1",
                channel="email",
                template_key="welcome",
                language_code="de",
                subject_template="Hallo {{name}}",
                body_template="Willkommen {{name}}",
            ),
            _actor(),
        )
        self.service.upsert_template(
            "tenant-1",
            MessageTemplateUpsert(
                tenant_id="tenant-1",
                channel="email",
                template_key="welcome",
                language_code="en",
                subject_template="Hello {{name}}",
                body_template="Welcome {{name}}",
            ),
            _actor(),
        )
        self.service.upsert_template(
            "tenant-1",
            MessageTemplateUpsert(
                tenant_id="tenant-1",
                channel="email",
                template_key="fallback-only",
                language_code="de",
                subject_template="Guten Tag {{name}}",
                body_template="Willkommen zurueck {{name}}",
            ),
            _actor(),
        )
        rendered = self.service.render_outbound_message(
            "tenant-1",
            RenderedMessageCreate(
                tenant_id="tenant-1",
                channel="email",
                template_key="welcome",
                language_code="en",
                placeholders={"name": "Nina"},
                recipients=[MessageRecipientCreate(destination="nina@example.invalid")],
            ),
            _actor(),
        )
        fallback = self.service.render_outbound_message(
            "tenant-1",
            RenderedMessageCreate(
                tenant_id="tenant-1",
                channel="email",
                template_key="fallback-only",
                language_code="en",
                placeholders={"name": "Kai"},
                recipients=[MessageRecipientCreate(destination="kai@example.invalid")],
            ),
            _actor(),
        )

        self.assertEqual(rendered.subject_rendered, "Hello Nina")
        self.assertEqual(fallback.body_rendered, "Willkommen zurueck Kai")

    def test_render_creates_recipients_and_attachment_links(self) -> None:
        self.service.upsert_template(
            "tenant-1",
            MessageTemplateUpsert(
                tenant_id="tenant-1",
                channel="email",
                template_key="report",
                language_code="de",
                subject_template="Bericht {{date}}",
                body_template="Hallo {{name}}",
            ),
            _actor(),
        )

        message = self.service.render_outbound_message(
            "tenant-1",
            RenderedMessageCreate(
                tenant_id="tenant-1",
                channel="email",
                template_key="report",
                language_code="de",
                placeholders={"date": "2026-03-19", "name": "Nina"},
                recipients=[
                    MessageRecipientCreate(destination="nina@example.invalid"),
                    MessageRecipientCreate(destination="+4912345", recipient_kind="cc"),
                ],
                attachment_document_ids=["doc-1", "doc-2"],
                related_entity_type="core.tenant",
                related_entity_id="tenant-1",
            ),
            _actor(),
        )

        self.assertEqual(len(message.recipients), 2)
        self.assertEqual(
            self.document_service.links,
            [
                ("tenant-1", "doc-1", "comm.outbound_message", message.id),
                ("tenant-1", "doc-2", "comm.outbound_message", message.id),
            ],
        )

    def test_missing_placeholder_is_rejected(self) -> None:
        self.service.upsert_template(
            "tenant-1",
            MessageTemplateUpsert(
                tenant_id="tenant-1",
                channel="sms",
                template_key="notice",
                language_code="de",
                body_template="Hallo {{name}} {{code}}",
            ),
            _actor(),
        )
        with self.assertRaises(ApiException):
            self.service.render_outbound_message(
                "tenant-1",
                RenderedMessageCreate(
                    tenant_id="tenant-1",
                    channel="sms",
                    template_key="notice",
                    language_code="de",
                    placeholders={"name": "Nina"},
                    recipients=[MessageRecipientCreate(destination="+491111")],
                ),
                _actor(),
            )

    def test_delivery_attempts_are_append_only_per_recipient(self) -> None:
        self.service.upsert_template(
            "tenant-1",
            MessageTemplateUpsert(
                tenant_id="tenant-1",
                channel="push",
                template_key="shift",
                language_code="de",
                body_template="Schicht {{name}}",
            ),
            _actor(),
        )
        message = self.service.render_outbound_message(
            "tenant-1",
            RenderedMessageCreate(
                tenant_id="tenant-1",
                channel="push",
                template_key="shift",
                language_code="de",
                placeholders={"name": "A"},
                recipients=[MessageRecipientCreate(destination="device-1")],
            ),
            _actor(),
        )
        recipient_id = message.recipients[0].id
        first = self.service.record_delivery_attempt(
            "tenant-1",
            message.id,
            recipient_id,
            DeliveryAttemptCreate(provider_key="noop", outcome="failed", error_code="timeout"),
            _actor(),
        )
        second = self.service.record_delivery_attempt(
            "tenant-1",
            message.id,
            recipient_id,
            DeliveryAttemptCreate(provider_key="noop", outcome="sent", provider_message_ref="msg-1"),
            _actor(),
        )

        self.assertEqual(first.attempt_no, 1)
        self.assertEqual(second.attempt_no, 2)
        stored = self.service.get_outbound_message("tenant-1", message.id, _actor())
        self.assertEqual(stored.body_rendered, "Schicht A")
        self.assertEqual(len(stored.delivery_attempts), 2)


if __name__ == "__main__":
    unittest.main()
