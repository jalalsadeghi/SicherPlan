"""Adapter seams for password reset delivery and future MFA/SSO hooks."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PasswordResetDelivery:
    token_id: str
    tenant_id: str
    user_account_id: str
    email: str
    locale: str
    reset_token: str


class PasswordResetNotifier(Protocol):
    def send_password_reset(self, delivery: PasswordResetDelivery) -> str | None: ...


class AuthExtensionHooks(Protocol):
    def mfa_required(self, user_id: str) -> bool: ...

    def sso_hints(self) -> list[str]: ...


class LoggingPasswordResetNotifier:
    """Development-safe reset delivery seam until platform messaging lands."""

    def send_password_reset(self, delivery: PasswordResetDelivery) -> str | None:
        logger.info(
            "iam.password_reset.requested",
            extra={
                "token_id": delivery.token_id,
                "tenant_id": delivery.tenant_id,
                "user_account_id": delivery.user_account_id,
                "email": delivery.email,
            },
        )
        return f"dev-log:{delivery.token_id}"


class DefaultAuthExtensionHooks:
    def mfa_required(self, user_id: str) -> bool:
        return False

    def sso_hints(self) -> list[str]:
        return []
