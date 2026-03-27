"""Reusable audit writers for auth and business-sensitive actions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Protocol
from uuid import UUID

from app.modules.iam.audit_schemas import AuditEventRead, AuditEventWrite, LoginEventRead, LoginEventWrite


class AuditRepository(Protocol):
    def create_login_event(self, payload: LoginEventWrite) -> LoginEventRead: ...
    def create_audit_event(self, payload: AuditEventWrite) -> AuditEventRead: ...


@dataclass(frozen=True, slots=True)
class AuditActor:
    tenant_id: str | None
    user_id: str | None
    session_id: str | None
    request_id: str | None
    source: str = "api"


class AuditService:
    def __init__(self, repository: AuditRepository) -> None:
        self.repository = repository

    def record_login_attempt(self, payload: LoginEventWrite) -> LoginEventRead:
        payload_dict = payload.model_dump()
        payload_dict["identifier"] = payload.identifier.strip()
        payload_dict["metadata_json"] = self._sanitize_json(payload_dict.get("metadata_json", {}))
        sanitized = LoginEventWrite(**payload_dict)
        return self.repository.create_login_event(sanitized)

    def record_business_event(
        self,
        *,
        actor: AuditActor,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str | None = None,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> AuditEventRead:
        return self.repository.create_audit_event(
            AuditEventWrite(
                tenant_id=tenant_id if tenant_id is not None else actor.tenant_id,
                actor_user_id=actor.user_id,
                actor_session_id=actor.session_id,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                request_id=actor.request_id,
                source=actor.source,
                before_json=self._sanitize_json(before_json or {}),
                after_json=self._sanitize_json(after_json or {}),
                metadata_json=self._sanitize_json(metadata_json or {}),
            )
        )

    @classmethod
    def _sanitize_json(cls, value: object) -> object:
        if isinstance(value, dict):
            sanitized: dict[str, object] = {}
            for key, item in value.items():
                if cls._is_sensitive_key(key):
                    continue
                sanitized[key] = cls._sanitize_json(item)
            return sanitized
        if isinstance(value, list):
            return [cls._sanitize_json(item) for item in value]
        if isinstance(value, tuple):
            return [cls._sanitize_json(item) for item in value]
        if isinstance(value, set):
            return [cls._sanitize_json(item) for item in sorted(value, key=repr)]
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime | date | time):
            return value.isoformat()
        if isinstance(value, Enum):
            return cls._sanitize_json(value.value)
        return value

    @staticmethod
    def _is_sensitive_key(key: str) -> bool:
        normalized = key.strip().lower().replace("-", "_")
        if normalized in {
            "password",
            "password_hash",
            "secret",
            "client_secret",
            "api_key",
            "access_token",
            "refresh_token",
            "token",
            "authorization",
            "session_token_hash",
            "token_hash",
        }:
            return True
        return normalized.endswith("_secret") or normalized.endswith("_token")
