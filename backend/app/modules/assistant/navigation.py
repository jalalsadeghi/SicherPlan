"""Safe assistant navigation helpers backed by the page route catalog."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.parse import urlencode

from app.modules.assistant.models import AssistantPageRouteCatalog
from app.modules.assistant.schemas import AssistantMissingPermission, AssistantNavigationLink
from app.modules.iam.authz import RequestAuthorizationContext


@dataclass(frozen=True, slots=True)
class AssistantPageAccessDecision:
    allowed: bool
    reason: str
    missing_permissions: list[AssistantMissingPermission]


def can_access_page(
    *,
    page: AssistantPageRouteCatalog,
    context: RequestAuthorizationContext,
) -> AssistantPageAccessDecision:
    if not page.active:
        return AssistantPageAccessDecision(
            allowed=False,
            reason="The requested page is not active in the current route catalog.",
            missing_permissions=[],
        )

    allowed_role_keys = set(page.allowed_role_keys or [])
    if allowed_role_keys and not (allowed_role_keys & set(context.role_keys)):
        return AssistantPageAccessDecision(
            allowed=False,
            reason="Current user role does not match the route authority for this page.",
            missing_permissions=[
                AssistantMissingPermission(
                    permission="route.authority",
                    reason=f"Allowed roles: {', '.join(sorted(allowed_role_keys))}.",
                )
            ],
        )

    required_permissions = [item for item in (page.required_permissions or []) if item]
    missing = [item for item in required_permissions if item not in context.permission_keys]
    if missing:
        return AssistantPageAccessDecision(
            allowed=False,
            reason="Current user lacks one or more required permissions for this page.",
            missing_permissions=[
                AssistantMissingPermission(
                    permission=item,
                    reason="Current user cannot access this workspace under the backend permission policy.",
                )
                for item in missing
            ],
        )

    return AssistantPageAccessDecision(
        allowed=True,
        reason=_access_reason(page),
        missing_permissions=[],
    )


def build_allowed_navigation_link(
    *,
    page: AssistantPageRouteCatalog,
    context: RequestAuthorizationContext,
    entity_context: dict[str, Any] | None,
    reason: str | None,
) -> tuple[AssistantPageAccessDecision, AssistantNavigationLink | None]:
    decision = can_access_page(page=page, context=context)
    if not decision.allowed:
        return decision, None

    path = build_catalog_path(page=page, entity_context=entity_context)
    link = AssistantNavigationLink(
        label=page.label,
        path=path,
        route_name=page.route_name,
        page_id=page.page_id,
        reason=_sanitize_reason(reason),
    )
    return decision, link


def build_catalog_path(
    *,
    page: AssistantPageRouteCatalog,
    entity_context: dict[str, Any] | None,
) -> str:
    base_path = page.path_template
    query = _sanitize_entity_context(page=page, entity_context=entity_context)
    if not query:
        return base_path
    return f"{base_path}?{urlencode(query)}"


def _sanitize_entity_context(
    *,
    page: AssistantPageRouteCatalog,
    entity_context: dict[str, Any] | None,
) -> dict[str, str]:
    if not page.supports_entity_deep_link or not page.entity_param_map or not entity_context:
        return {}
    safe: dict[str, str] = {}
    for source_key, target_key in page.entity_param_map.items():
        raw_value = entity_context.get(source_key)
        cleaned = _sanitize_entity_value(source_key, raw_value)
        if cleaned is not None:
            safe[target_key] = cleaned
    return safe


def _sanitize_entity_value(key: str, value: Any) -> str | None:
    if value is None:
        return None
    if key == "date":
        if not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value.strip()).isoformat()
        except ValueError:
            return None
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > 120:
        cleaned = cleaned[:120]
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_:")
    if any(char not in allowed for char in cleaned):
        return None
    return cleaned


def _sanitize_reason(reason: str | None) -> str | None:
    if reason is None:
        return None
    cleaned = reason.strip()
    if not cleaned:
        return None
    return cleaned[:240]


def _access_reason(page: AssistantPageRouteCatalog) -> str:
    if page.required_permissions:
        return "User has the required page permission or matching route authority."
    return "User matches the route authority for this page."
