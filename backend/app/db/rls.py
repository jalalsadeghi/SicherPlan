"""Helpers for optional PostgreSQL row-level-security session context."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings


def apply_rls_context(
    session: Session,
    *,
    tenant_id: str | None,
    bypass: bool = False,
    mode: str | None = None,
) -> None:
    """Apply a trusted per-session RLS context for the current transaction."""

    session.execute(
        text(
            """
            SELECT
                set_config('app.rls_mode', :mode, true),
                set_config('app.rls_bypass', :bypass, true),
                set_config('app.tenant_id', :tenant_id, true)
            """
        ),
        {
            "mode": mode or ("enforce" if settings.db_rls_enabled else settings.db_rls_default_mode),
            "bypass": "on" if bypass else "off",
            "tenant_id": tenant_id or "",
        },
    )


def clear_rls_context(session: Session) -> None:
    session.execute(
        text(
            """
            SELECT
                set_config('app.rls_mode', 'off', true),
                set_config('app.rls_bypass', 'off', true),
                set_config('app.tenant_id', '', true)
            """
        )
    )


@contextmanager
def rls_session_context(
    session: Session,
    *,
    tenant_id: str | None,
    bypass: bool = False,
    mode: str | None = None,
) -> Iterator[Session]:
    apply_rls_context(session, tenant_id=tenant_id, bypass=bypass, mode=mode)
    try:
        yield session
    finally:
        clear_rls_context(session)
