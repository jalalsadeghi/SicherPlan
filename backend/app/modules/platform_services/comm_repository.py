"""SQLAlchemy repository for communication templates and outbound history."""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.modules.platform_services.comm_models import (
    DeliveryAttempt,
    MessageRecipient,
    MessageTemplate,
    OutboundMessage,
)


class SqlAlchemyCommunicationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_template(
        self,
        tenant_id: str,
        channel: str,
        template_key: str,
        language_code: str,
    ) -> MessageTemplate | None:
        statement = (
            select(MessageTemplate)
            .where(
                MessageTemplate.tenant_id == tenant_id,
                MessageTemplate.channel == channel,
                MessageTemplate.template_key == template_key,
                MessageTemplate.language_code == language_code,
            )
        )
        return self.session.scalars(statement).one_or_none()

    def upsert_template(self, row: MessageTemplate) -> MessageTemplate:
        existing = self.find_template(row.tenant_id, row.channel, row.template_key, row.language_code)
        if existing is None:
            self.session.add(row)
            self.session.commit()
            self.session.refresh(row)
            return row
        existing.subject_template = row.subject_template
        existing.body_template = row.body_template
        existing.metadata_json = row.metadata_json
        existing.updated_by_user_id = row.updated_by_user_id
        existing.version_no += 1
        self.session.add(existing)
        self.session.commit()
        return existing

    def create_outbound_message(
        self,
        message: OutboundMessage,
        recipients: list[MessageRecipient],
    ) -> OutboundMessage:
        self.session.add(message)
        self.session.flush()
        for recipient in recipients:
            recipient.outbound_message_id = message.id
            self.session.add(recipient)
        self.session.commit()
        return self.get_outbound_message(message.tenant_id, message.id) or message

    def get_outbound_message(self, tenant_id: str, message_id: str) -> OutboundMessage | None:
        statement = self._message_query().where(OutboundMessage.tenant_id == tenant_id, OutboundMessage.id == message_id)
        return self.session.scalars(statement).unique().one_or_none()

    def get_recipient(self, tenant_id: str, message_id: str, recipient_id: str) -> MessageRecipient | None:
        statement = (
            select(MessageRecipient)
            .where(
                MessageRecipient.tenant_id == tenant_id,
                MessageRecipient.outbound_message_id == message_id,
                MessageRecipient.id == recipient_id,
            )
        )
        return self.session.scalars(statement).one_or_none()

    def count_attempts_for_recipient(self, recipient_id: str) -> int:
        statement = select(func.count(DeliveryAttempt.id)).where(DeliveryAttempt.recipient_id == recipient_id)
        return int(self.session.scalar(statement) or 0)

    def create_delivery_attempt(self, attempt: DeliveryAttempt) -> DeliveryAttempt:
        self.session.add(attempt)
        self.session.commit()
        self.session.refresh(attempt)
        return attempt

    @staticmethod
    def _message_query() -> Select[tuple[OutboundMessage]]:
        return (
            select(OutboundMessage)
            .options(joinedload(OutboundMessage.recipients))
            .options(joinedload(OutboundMessage.delivery_attempts))
        )
