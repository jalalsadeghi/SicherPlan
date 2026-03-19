"""Template render and outbound-message services for email, SMS, and push history."""

from __future__ import annotations

from dataclasses import asdict
import re
from dataclasses import dataclass
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.comm_models import DeliveryAttempt, MessageRecipient, MessageTemplate, OutboundMessage
from app.modules.platform_services.comm_schemas import (
    DeliveryAttemptCreate,
    DeliveryAttemptRead,
    MessageTemplateRead,
    MessageTemplateUpsert,
    OutboundMessageRead,
    RenderedMessageCreate,
)
from app.modules.platform_services.docs_schemas import DocumentLinkCreate
from app.modules.platform_services.docs_service import DocumentService


TEMPLATE_VARIABLE_PATTERN = re.compile(r"{{\s*([A-Za-z0-9_]+)\s*}}")
SUPPORTED_LANGUAGES = frozenset({"de", "en"})


class CommunicationRepository(Protocol):
    def find_template(self, tenant_id: str, channel: str, template_key: str, language_code: str): ...  # noqa: ANN001
    def upsert_template(self, row: MessageTemplate) -> MessageTemplate: ...
    def create_outbound_message(self, message: OutboundMessage, recipients: list[MessageRecipient]) -> OutboundMessage: ...
    def get_outbound_message(self, tenant_id: str, message_id: str) -> OutboundMessage | None: ...
    def get_recipient(self, tenant_id: str, message_id: str, recipient_id: str) -> MessageRecipient | None: ...
    def count_attempts_for_recipient(self, recipient_id: str) -> int: ...
    def create_delivery_attempt(self, attempt: DeliveryAttempt) -> DeliveryAttempt: ...


@dataclass(frozen=True, slots=True)
class ProviderDispatchRequest:
    message_id: str
    channel: str
    recipient_id: str
    destination: str
    rendered_subject: str | None
    rendered_body: str


class ProviderDispatchAdapter(Protocol):
    def build_dispatch_request(
        self,
        *,
        message_id: str,
        channel: str,
        recipient_id: str,
        destination: str,
        rendered_subject: str | None,
        rendered_body: str,
    ) -> ProviderDispatchRequest: ...


class NoopProviderDispatchAdapter:
    def build_dispatch_request(
        self,
        *,
        message_id: str,
        channel: str,
        recipient_id: str,
        destination: str,
        rendered_subject: str | None,
        rendered_body: str,
    ) -> ProviderDispatchRequest:
        return ProviderDispatchRequest(
            message_id=message_id,
            channel=channel,
            recipient_id=recipient_id,
            destination=destination,
            rendered_subject=rendered_subject,
            rendered_body=rendered_body,
        )


class CommunicationService:
    def __init__(
        self,
        repository: CommunicationRepository,
        *,
        document_service: DocumentService,
        dispatch_adapter: ProviderDispatchAdapter | None = None,
    ) -> None:
        self.repository = repository
        self.document_service = document_service
        self.dispatch_adapter = dispatch_adapter or NoopProviderDispatchAdapter()

    def upsert_template(
        self,
        tenant_id: str,
        payload: MessageTemplateUpsert,
        actor: RequestAuthorizationContext,
    ) -> MessageTemplateRead:
        self._ensure_tenant_scope(actor, tenant_id)
        self._ensure_supported_language(payload.language_code)
        row = self.repository.upsert_template(
            MessageTemplate(
                tenant_id=tenant_id,
                channel=payload.channel,
                template_key=payload.template_key,
                language_code=payload.language_code,
                subject_template=payload.subject_template,
                body_template=payload.body_template,
                metadata_json=payload.metadata_json,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        return MessageTemplateRead.model_validate(row)

    def render_outbound_message(
        self,
        tenant_id: str,
        payload: RenderedMessageCreate,
        actor: RequestAuthorizationContext,
    ) -> OutboundMessageRead:
        self._ensure_tenant_scope(actor, tenant_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "core.validation.tenant_mismatch", "errors.docs.document.tenant_mismatch")
        template = self._resolve_template(tenant_id, payload.channel, payload.template_key, payload.language_code)
        rendered_subject = self._render(template.subject_template, payload.placeholders)
        rendered_body = self._render(template.body_template, payload.placeholders)
        recipients = [
            MessageRecipient(
                tenant_id=tenant_id,
                outbound_message_id="",
                recipient_kind=recipient.recipient_kind,
                destination=recipient.destination,
                display_name=recipient.display_name,
                user_account_id=recipient.user_account_id,
                metadata_json=recipient.metadata_json,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
            for recipient in payload.recipients
        ]
        dispatch_preview = [
            asdict(
                self.dispatch_adapter.build_dispatch_request(
                    message_id="pending",
                    channel=payload.channel,
                    recipient_id=f"preview-{index}",
                    destination=recipient.destination,
                    rendered_subject=rendered_subject,
                    rendered_body=rendered_body,
                )
            )
            for index, recipient in enumerate(payload.recipients, start=1)
        ]
        outbound_message = self.repository.create_outbound_message(
            OutboundMessage(
                tenant_id=tenant_id,
                template_id=template.id,
                channel=payload.channel,
                template_key=payload.template_key,
                language_code=template.language_code,
                subject_rendered=rendered_subject,
                body_rendered=rendered_body,
                related_entity_type=payload.related_entity_type,
                related_entity_id=payload.related_entity_id,
                metadata_json={
                    **payload.metadata_json,
                    "dispatch_preview": dispatch_preview,
                },
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            ),
            recipients,
        )
        for document_id in payload.attachment_document_ids:
            self._attach_document(tenant_id, outbound_message.id, document_id, actor)
        return OutboundMessageRead.model_validate(
            self.repository.get_outbound_message(tenant_id, outbound_message.id) or outbound_message
        )

    def record_delivery_attempt(
        self,
        tenant_id: str,
        message_id: str,
        recipient_id: str,
        payload: DeliveryAttemptCreate,
        actor: RequestAuthorizationContext,
    ) -> DeliveryAttemptRead:
        self._ensure_tenant_scope(actor, tenant_id)
        outbound_message = self.repository.get_outbound_message(tenant_id, message_id)
        if outbound_message is None:
            raise ApiException(404, "comm.message.not_found", "errors.comm.message.not_found")
        recipient = self.repository.get_recipient(tenant_id, message_id, recipient_id)
        if recipient is None:
            raise ApiException(
                404,
                "comm.delivery_attempt.recipient_not_found",
                "errors.comm.delivery_attempt.recipient_not_found",
            )
        attempt = self.repository.create_delivery_attempt(
            DeliveryAttempt(
                tenant_id=tenant_id,
                outbound_message_id=message_id,
                recipient_id=recipient_id,
                provider_key=payload.provider_key,
                provider_message_ref=payload.provider_message_ref,
                outcome=payload.outcome,
                attempt_no=self.repository.count_attempts_for_recipient(recipient_id) + 1,
                response_code=payload.response_code,
                response_summary=payload.response_summary,
                error_code=payload.error_code,
                metadata_json=payload.metadata_json,
            )
        )
        return DeliveryAttemptRead.model_validate(attempt)

    def get_outbound_message(
        self,
        tenant_id: str,
        message_id: str,
        actor: RequestAuthorizationContext,
    ) -> OutboundMessageRead:
        self._ensure_tenant_scope(actor, tenant_id)
        outbound_message = self.repository.get_outbound_message(tenant_id, message_id)
        if outbound_message is None:
            raise ApiException(404, "comm.message.not_found", "errors.comm.message.not_found")
        return OutboundMessageRead.model_validate(outbound_message)

    def _attach_document(
        self,
        tenant_id: str,
        outbound_message_id: str,
        document_id: str,
        actor: RequestAuthorizationContext,
    ) -> None:
        try:
            self.document_service.get_document(tenant_id, document_id, actor)
        except ApiException as exc:
            if exc.code == "docs.document.not_found":
                raise ApiException(
                    404,
                    "comm.attachment.document_not_found",
                    "errors.comm.attachment.document_not_found",
                    {"document_id": document_id},
                ) from exc
            raise
        self.document_service.add_document_link(
            tenant_id,
            document_id,
            DocumentLinkCreate(
                owner_type="comm.outbound_message",
                owner_id=outbound_message_id,
                relation_type="attachment",
            ),
            actor,
        )

    def _resolve_template(
        self,
        tenant_id: str,
        channel: str,
        template_key: str,
        requested_language: str,
    ) -> MessageTemplate:
        self._ensure_supported_language(requested_language)
        template = self.repository.find_template(tenant_id, channel, template_key, requested_language)
        if template is None and requested_language != "de":
            template = self.repository.find_template(tenant_id, channel, template_key, "de")
        if template is None:
            raise ApiException(404, "comm.template.not_found", "errors.comm.template.not_found")
        return template

    @staticmethod
    def _render(template: str | None, placeholders: dict[str, object]) -> str | None:
        if template is None:
            return None

        missing: set[str] = set()

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            if key not in placeholders:
                missing.add(key)
                return match.group(0)
            return str(placeholders[key])

        rendered = TEMPLATE_VARIABLE_PATTERN.sub(replace, template)
        if missing:
            raise ApiException(
                400,
                "comm.render.missing_placeholder",
                "errors.comm.render.missing_placeholder",
                {"missing_keys": sorted(missing)},
            )
        return rendered

    @staticmethod
    def _ensure_supported_language(language_code: str) -> None:
        if language_code not in SUPPORTED_LANGUAGES:
            raise ApiException(
                400,
                "comm.template.language_not_supported",
                "errors.comm.template.language_not_supported",
                {"language_code": language_code},
            )

    @staticmethod
    def _ensure_tenant_scope(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.is_platform_admin or actor.tenant_id == tenant_id:
            return
        raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")
