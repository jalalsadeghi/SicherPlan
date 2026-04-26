"""Assistant tools for verified UI page-help manifests."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from app.modules.assistant.schemas import (
    AssistantFindUiActionInput,
    AssistantFindUiActionRead,
    AssistantMissingPermission,
    AssistantPageHelpActionRead,
    AssistantPageHelpFieldRead,
    AssistantPageHelpFormSectionRead,
    AssistantPageHelpManifestInput,
    AssistantPageHelpManifestRead,
    AssistantPageHelpPostStepRead,
    AssistantPageHelpSidebarItemRead,
    AssistantPageHelpVerifiedFromRead,
)
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)


class AssistantPageHelpRepository(Protocol):
    def get_page_help_manifest(
        self,
        *,
        page_id: str,
        language_code: str | None = None,
    ): ...


def _normalize_language_code(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().lower()
    if not cleaned:
        return None
    if "-" in cleaned:
        cleaned = cleaned.split("-", 1)[0]
    return cleaned


def _safe_manifest_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _is_action_allowed(action: dict[str, Any], context: AssistantToolExecutionContext) -> bool:
    permissions = action.get("required_permissions") or []
    if not isinstance(permissions, list):
        return False
    return all(isinstance(item, str) and item in context.permission_keys for item in permissions)


def _filter_manifest_actions(
    manifest_json: dict[str, Any],
    *,
    context: AssistantToolExecutionContext,
) -> list[AssistantPageHelpActionRead]:
    actions: list[AssistantPageHelpActionRead] = []
    for item in manifest_json.get("primary_actions", []):
        if not isinstance(item, dict):
            continue
        if item.get("verified") is not True:
            continue
        if not _is_action_allowed(item, context):
            continue
        actions.append(
            AssistantPageHelpActionRead(
                action_key=str(item.get("action_key", "")),
                label=str(item.get("label", "")),
                action_type=str(item.get("action_type", "button")),
                selector=item.get("selector"),
                test_id=item.get("test_id"),
                location=item.get("location"),
                required_permissions=[
                    str(permission)
                    for permission in item.get("required_permissions", [])
                    if isinstance(permission, str)
                ],
                opens=item.get("opens"),
                result=item.get("result"),
                verified=bool(item.get("verified", False)),
                allowed=True,
            )
        )
    return actions


def _manifest_read_from_row(
    row,
    *,
    context: AssistantToolExecutionContext,
) -> AssistantPageHelpManifestRead:
    manifest_json = _safe_manifest_json(row.manifest_json)
    actions = _filter_manifest_actions(manifest_json, context=context)
    return AssistantPageHelpManifestRead(
        page_id=row.page_id,
        page_title=str(manifest_json.get("page_title") or row.page_id),
        route_name=row.route_name,
        path_template=row.path_template,
        module_key=row.module_key,
        language_code=row.language_code,
        source_status=str(manifest_json.get("source_status") or row.status),
        sidebar_path=[
            AssistantPageHelpSidebarItemRead.model_validate(item)
            for item in manifest_json.get("sidebar_path", [])
            if isinstance(item, dict)
        ],
        actions=actions,
        form_sections=[
            AssistantPageHelpFormSectionRead(
                section_key=str(item.get("section_key", "")),
                title=str(item.get("title", "")),
                verified=bool(item.get("verified", False)),
                fields=[
                    AssistantPageHelpFieldRead.model_validate(field)
                    for field in item.get("fields", [])
                    if isinstance(field, dict)
                ],
            )
            for item in manifest_json.get("form_sections", [])
            if isinstance(item, dict)
        ],
        post_create_steps=[
            AssistantPageHelpPostStepRead.model_validate(item)
            for item in manifest_json.get("post_create_steps", [])
            if isinstance(item, dict)
        ],
        verified_from=[
            AssistantPageHelpVerifiedFromRead.model_validate(item)
            for item in (row.verified_from or [])
            if isinstance(item, dict)
        ],
    )


class GetPageHelpManifestTool:
    def __init__(self, *, repository: AssistantPageHelpRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="assistant.get_page_help_manifest",
            description="Return verified page-help metadata and allowed UI actions for one page.",
            input_schema=AssistantPageHelpManifestInput,
            output_schema=AssistantPageHelpManifestRead,
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
        page_id = getattr(input_data, "page_id", None)
        if not page_id:
            payload = AssistantPageHelpManifestRead(
                page_id="unknown",
                page_title="Unknown page",
                module_key="unknown",
                source_status="unverified",
            ).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)
        row = self.repository.get_page_help_manifest(
            page_id=page_id,
            language_code=_normalize_language_code(getattr(input_data, "language_code", None)),
        )
        if row is None:
            payload = AssistantPageHelpManifestRead(
                page_id=page_id,
                page_title=page_id,
                module_key="unknown",
                language_code=_normalize_language_code(getattr(input_data, "language_code", None)),
                source_status="unverified",
            ).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=_manifest_read_from_row(row, context=context).model_dump(mode="json"),
            entity_refs={"page_id": row.page_id},
        )


class FindUiActionTool:
    def __init__(self, *, repository: AssistantPageHelpRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="assistant.find_ui_action",
            description="Find one verified UI action for a known assistant intent without guessing labels.",
            input_schema=AssistantFindUiActionInput,
            output_schema=AssistantFindUiActionRead,
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
        intent = str(getattr(input_data, "intent", "")).strip()
        page_id = getattr(input_data, "page_id", None) or "E-01"
        row = self.repository.get_page_help_manifest(
            page_id=page_id,
            language_code=_normalize_language_code(getattr(input_data, "language_code", None)),
        )
        if row is None:
            payload = AssistantFindUiActionRead(
                page_id=page_id,
                intent=intent,
                source_status="unverified",
                safe_note="No verified UI action is registered for this page and intent.",
            ).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        manifest_json = _safe_manifest_json(row.manifest_json)
        action_entry = None
        if intent == "create_employee":
            for item in manifest_json.get("primary_actions", []):
                if isinstance(item, dict) and item.get("action_key") == "employees.create.open":
                    action_entry = item
                    break

        if not isinstance(action_entry, dict) or action_entry.get("verified") is not True:
            payload = AssistantFindUiActionRead(
                page_id=row.page_id,
                page_title=str(manifest_json.get("page_title") or row.page_id),
                route_name=row.route_name,
                path_template=row.path_template,
                source_status=str(manifest_json.get("source_status") or row.status),
                intent=intent,
                safe_note="Exact current UI action is not verified for this intent.",
            ).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        allowed = _is_action_allowed(action_entry, context)
        permissions = [
            str(permission)
            for permission in action_entry.get("required_permissions", [])
            if isinstance(permission, str)
        ]
        payload = AssistantFindUiActionRead(
            page_id=row.page_id,
            page_title=str(manifest_json.get("page_title") or row.page_id),
            route_name=row.route_name,
            path_template=row.path_template,
            source_status=str(manifest_json.get("source_status") or row.status),
            intent=intent,
            action=AssistantPageHelpActionRead(
                action_key=str(action_entry.get("action_key", "")),
                label=str(action_entry.get("label", "")),
                action_type=str(action_entry.get("action_type", "button")),
                selector=action_entry.get("selector"),
                test_id=action_entry.get("test_id"),
                location=action_entry.get("location"),
                required_permissions=permissions,
                opens=action_entry.get("opens"),
                result=action_entry.get("result"),
                verified=True,
                allowed=allowed,
            ),
            form_sections=[
                AssistantPageHelpFormSectionRead(
                    section_key=str(item.get("section_key", "")),
                    title=str(item.get("title", "")),
                    verified=bool(item.get("verified", False)),
                    fields=[
                        AssistantPageHelpFieldRead.model_validate(field)
                        for field in item.get("fields", [])
                        if isinstance(field, dict)
                    ],
                )
                for item in manifest_json.get("form_sections", [])
                if isinstance(item, dict)
            ],
            sidebar_path=[
                AssistantPageHelpSidebarItemRead.model_validate(item)
                for item in manifest_json.get("sidebar_path", [])
                if isinstance(item, dict)
            ],
            missing_permissions=(
                []
                if allowed
                else [
                    AssistantMissingPermission(
                        permission=permission,
                        reason="The current user does not have the required permission for this verified UI action.",
                    )
                    for permission in permissions
                ]
            ),
            safe_note=None if allowed else "The exact action is verified, but it is not allowed for the current user.",
        ).model_dump(mode="json")
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=payload,
            entity_refs={"page_id": row.page_id, "action_key": "employees.create.open"},
        )
