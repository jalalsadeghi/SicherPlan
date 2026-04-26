"""SQLAlchemy repository for assistant persistence."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.assistant.models import (
    AssistantConversation,
    AssistantFeedback,
    AssistantMessage,
    AssistantPageHelpManifest,
    AssistantPageRouteCatalog,
    AssistantToolCall,
)
from app.modules.assistant.tools.registry import AssistantToolAuditRecord


class SqlAlchemyAssistantRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

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
        conversation = AssistantConversation(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            locale=locale,
            status="active",
            last_route_name=last_route_name,
            last_route_path=last_route_path,
        )
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def get_conversation_for_user(
        self,
        *,
        conversation_id: str,
        tenant_id: str | None,
        user_id: str,
    ) -> AssistantConversation | None:
        statement = (
            select(AssistantConversation)
            .options(selectinload(AssistantConversation.messages))
            .where(
                AssistantConversation.id == conversation_id,
                AssistantConversation.user_id == user_id,
            )
        )
        if tenant_id is None:
            statement = statement.where(AssistantConversation.tenant_id.is_(None))
        else:
            statement = statement.where(AssistantConversation.tenant_id == tenant_id)
        conversation = self.session.scalars(statement).one_or_none()
        if conversation is None:
            return None
        conversation.messages.sort(key=lambda row: row.created_at)
        return conversation

    def list_messages_for_conversation(self, conversation_id: str) -> list[AssistantMessage]:
        statement = (
            select(AssistantMessage)
            .where(AssistantMessage.conversation_id == conversation_id)
            .order_by(AssistantMessage.created_at.asc(), AssistantMessage.id.asc())
        )
        return list(self.session.scalars(statement).all())

    def update_conversation_route_context(
        self,
        conversation: AssistantConversation,
        *,
        last_route_name: str | None,
        last_route_path: str | None,
    ) -> None:
        conversation.last_route_name = last_route_name
        conversation.last_route_path = last_route_path
        conversation.updated_at = datetime.now(UTC)
        self.session.add(conversation)

    def create_messages(
        self,
        conversation: AssistantConversation,
        messages: Sequence[AssistantMessage],
    ) -> list[AssistantMessage]:
        self.session.add(conversation)
        for message in messages:
            self.session.add(message)
        self.session.commit()
        for message in messages:
            self.session.refresh(message)
        self.session.refresh(conversation)
        return list(messages)

    def update_message_payload(
        self,
        message: AssistantMessage,
        *,
        structured_payload: dict[str, object],
    ) -> None:
        message.structured_payload = structured_payload
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)

    def get_message_for_conversation(
        self,
        *,
        conversation_id: str,
        message_id: str,
    ) -> AssistantMessage | None:
        statement = select(AssistantMessage).where(
            AssistantMessage.conversation_id == conversation_id,
            AssistantMessage.id == message_id,
        )
        return self.session.scalars(statement).one_or_none()

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
        statement = select(AssistantFeedback).where(
            AssistantFeedback.conversation_id == conversation_id,
            AssistantFeedback.message_id == message_id,
            AssistantFeedback.user_id == user_id,
        )
        row = self.session.scalars(statement).one_or_none()
        if row is None:
            row = AssistantFeedback(
                conversation_id=conversation_id,
                message_id=message_id,
                tenant_id=tenant_id,
                user_id=user_id,
                rating=rating,
                comment=comment,
            )
            self.session.add(row)
        else:
            row.tenant_id = tenant_id
            row.rating = rating
            row.comment = comment
            self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def create_tool_call_audit(
        self,
        *,
        record: AssistantToolAuditRecord,
    ) -> AssistantToolCall:
        row = AssistantToolCall(
            conversation_id=record.conversation_id,
            message_id=record.message_id,
            tenant_id=record.tenant_id,
            user_id=record.user_id,
            tool_name=record.tool_name,
            input_json=record.input_json,
            output_json_summary=record.output_json_summary,
            required_permissions=record.required_permissions,
            permission_decision=record.permission_decision,
            scope_kind=record.scope_kind,
            entity_refs=record.entity_refs,
            duration_ms=record.duration_ms,
            error_code=record.error_code,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_active_page_routes(self) -> list[AssistantPageRouteCatalog]:
        statement = (
            select(AssistantPageRouteCatalog)
            .where(AssistantPageRouteCatalog.active.is_(True))
            .order_by(
                AssistantPageRouteCatalog.module_key.asc(),
                AssistantPageRouteCatalog.page_id.asc(),
                AssistantPageRouteCatalog.path_template.asc(),
            )
        )
        return list(self.session.scalars(statement).all())

    def get_page_route_by_page_id(self, *, page_id: str) -> AssistantPageRouteCatalog | None:
        statement = (
            select(AssistantPageRouteCatalog)
            .where(AssistantPageRouteCatalog.page_id == page_id)
            .order_by(AssistantPageRouteCatalog.active.desc(), AssistantPageRouteCatalog.path_template.asc())
        )
        return self.session.scalars(statement).first()

    def get_page_help_manifest(
        self,
        *,
        page_id: str,
        language_code: str | None = None,
    ) -> AssistantPageHelpManifest | None:
        candidates: list[str | None] = []
        if language_code:
            candidates.append(language_code)
        for fallback in ("en", "de", None):
            if fallback not in candidates:
                candidates.append(fallback)

        for candidate in candidates:
            statement = (
                select(AssistantPageHelpManifest)
                .where(
                    AssistantPageHelpManifest.page_id == page_id,
                    AssistantPageHelpManifest.status.in_(("active", "unverified")),
                )
                .order_by(
                    AssistantPageHelpManifest.manifest_version.desc(),
                    AssistantPageHelpManifest.updated_at.desc(),
                )
            )
            if candidate is None:
                statement = statement.where(AssistantPageHelpManifest.language_code.is_(None))
            else:
                statement = statement.where(AssistantPageHelpManifest.language_code == candidate)
            row = self.session.scalars(statement).first()
            if row is not None:
                return row
        return None

    def upsert_page_help_manifest(
        self,
        *,
        page_id: str,
        route_name: str | None,
        path_template: str | None,
        module_key: str,
        language_code: str | None,
        manifest_version: int,
        status: str,
        manifest_json: dict[str, object],
        verified_from: list[dict[str, object]] | None,
    ) -> tuple[AssistantPageHelpManifest, bool]:
        statement = (
            select(AssistantPageHelpManifest)
            .where(
                AssistantPageHelpManifest.page_id == page_id,
                AssistantPageHelpManifest.language_code == language_code,
                AssistantPageHelpManifest.manifest_version == manifest_version,
            )
        )
        row = self.session.scalars(statement).one_or_none()
        created = False
        if row is None:
            row = AssistantPageHelpManifest(
                page_id=page_id,
                route_name=route_name,
                path_template=path_template,
                module_key=module_key,
                language_code=language_code,
                manifest_version=manifest_version,
                status=status,
                manifest_json=manifest_json,
                verified_from=verified_from,
            )
            self.session.add(row)
            created = True
        else:
            row.route_name = route_name
            row.path_template = path_template
            row.module_key = module_key
            row.status = status
            row.manifest_json = manifest_json
            row.verified_from = verified_from
            self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row, created
