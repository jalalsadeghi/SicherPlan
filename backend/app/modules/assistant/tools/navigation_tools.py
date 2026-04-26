"""Assistant tools for route-catalog search and safe link construction."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from app.modules.assistant.models import AssistantPageRouteCatalog
from app.modules.assistant.navigation import build_allowed_navigation_link, can_access_page
from app.modules.assistant.schemas import (
    AssistantAccessiblePageRead,
    AssistantAccessiblePagesSearchInput,
    AssistantAccessiblePagesSearchRead,
    AssistantAllowedNavigationLinkRead,
    AssistantNavigationEntityContextInput,
    AssistantNavigationLinkBuildInput,
)
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)


class AssistantPageCatalogRepository(Protocol):
    def list_active_page_routes(self) -> list[AssistantPageRouteCatalog]: ...

    def get_page_route_by_page_id(self, *, page_id: str) -> AssistantPageRouteCatalog | None: ...


class SearchAccessiblePagesTool:
    def __init__(self, *, repository: AssistantPageCatalogRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="assistant.search_accessible_pages",
            description="Return conservative accessible page hints from the assistant page route catalog.",
            input_schema=AssistantAccessiblePagesSearchInput,
            output_schema=AssistantAccessiblePagesSearchRead,
            required_permissions=["assistant.chat.access"],
            scope_behavior=AssistantToolScopeBehavior.CURRENT_USER,
            classification=AssistantToolClassification.READ_ONLY,
            max_rows=10,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        query = _sanitize_text(getattr(input_data, "query", None), 120)
        query_tokens = {token for token in (query or "").casefold().split() if token}
        module_key = _sanitize_text(getattr(input_data, "module_key", None), 120)
        page_id = _sanitize_text(getattr(input_data, "page_id", None), 120)
        limit = int(getattr(input_data, "limit", 10))

        visible: list[AssistantAccessiblePageRead] = []
        for page in self.repository.list_active_page_routes():
            if module_key and page.module_key != module_key:
                continue
            if page_id and page.page_id != page_id:
                continue
            if query_tokens and not _page_matches_query(page, query_tokens):
                continue
            decision = can_access_page(page=page, context=context.auth_context)
            if not decision.allowed:
                continue
            visible.append(
                AssistantAccessiblePageRead(
                    page_id=page.page_id,
                    label=page.label,
                    route_name=page.route_name,
                    path_template=page.path_template,
                    module_key=page.module_key,
                    can_access=True,
                    reason=decision.reason,
                )
            )

        truncated = len(visible) > limit
        payload = AssistantAccessiblePagesSearchRead(
            pages=visible[:limit],
            truncated=truncated,
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)


class BuildAllowedLinkTool:
    def __init__(self, *, repository: AssistantPageCatalogRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="navigation.build_allowed_link",
            description="Build a safe internal navigation link from the assistant page route catalog.",
            input_schema=AssistantNavigationLinkBuildInput,
            output_schema=AssistantAllowedNavigationLinkRead,
            required_permissions=["assistant.chat.access"],
            scope_behavior=AssistantToolScopeBehavior.CURRENT_USER,
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        page_id = _sanitize_text(getattr(input_data, "page_id", None), 120)
        if page_id is None:
            payload = AssistantAllowedNavigationLinkRead(
                allowed=False,
                link=None,
                missing_permissions=[],
            ).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        page = self.repository.get_page_route_by_page_id(page_id=page_id)
        if page is None or not page.active:
            payload = AssistantAllowedNavigationLinkRead(
                allowed=False,
                link=None,
                missing_permissions=[],
            ).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        entity_context = _entity_context_to_dict(getattr(input_data, "entity_context", None))
        reason = _sanitize_text(getattr(input_data, "reason", None), 240)
        decision, link = build_allowed_navigation_link(
            page=page,
            context=context.auth_context,
            entity_context=entity_context,
            reason=reason,
        )
        payload = AssistantAllowedNavigationLinkRead(
            allowed=decision.allowed,
            link=link,
            missing_permissions=decision.missing_permissions,
        ).model_dump(mode="json")
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=payload,
            entity_refs={"page_id": page.page_id} if link is not None else None,
        )


def _sanitize_text(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:max_length]


def _page_matches_query(page: AssistantPageRouteCatalog, query_tokens: set[str]) -> bool:
    haystack = " ".join(
        part
        for part in [
            page.page_id,
            page.label,
            page.module_key,
            page.route_name or "",
            page.path_template,
        ]
        if part
    ).casefold()
    return all(token in haystack for token in query_tokens)


def _entity_context_to_dict(value: AssistantNavigationEntityContextInput | Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, AssistantNavigationEntityContextInput):
        return value.model_dump(mode="json", exclude_none=True)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    return {}
