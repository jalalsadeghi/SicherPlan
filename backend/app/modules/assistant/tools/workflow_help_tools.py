"""Assistant tools for verified workflow grounding facts."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

from app.modules.assistant.models import AssistantPageRouteCatalog
from app.modules.assistant.navigation import build_allowed_navigation_link
from app.modules.assistant.schemas import (
    AssistantGroundingFactRead,
    AssistantWorkflowHelpInput,
    AssistantWorkflowHelpRead,
)
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)
from app.modules.assistant.workflow_help import WORKFLOW_HELP_SEEDS
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


class AssistantPageCatalogRepository(Protocol):
    def get_page_route_by_page_id(self, *, page_id: str) -> AssistantPageRouteCatalog | None: ...


class SearchWorkflowHelpTool:
    def __init__(self, *, repository: AssistantPageCatalogRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="assistant.search_workflow_help",
            description="Return verified workflow grounding facts and allowed workspace links for a known SicherPlan workflow intent.",
            input_schema=AssistantWorkflowHelpInput,
            output_schema=AssistantWorkflowHelpRead,
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
        seed = WORKFLOW_HELP_SEEDS.get(intent)
        if seed is None:
            payload = AssistantWorkflowHelpRead(
                intent=intent,
                title=intent or "unknown workflow",
                safe_note="No verified workflow grounding is registered for this intent.",
            ).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        facts = [
            AssistantGroundingFactRead(
                kind="workflow_fact",
                code=fact.code,
                title=fact.title,
                detail=fact.detail,
                page_id=fact.page_id,
                action_key=fact.action_key,
                verified=True,
            )
            for fact in seed.facts
        ]
        actor = _to_request_context(context)
        allowed_links = []
        missing_permissions = []
        for page_id in seed.linked_page_ids:
            page = self.repository.get_page_route_by_page_id(page_id=page_id)
            if page is None:
                continue
            decision, link = build_allowed_navigation_link(
                page=page,
                context=actor,
                entity_context=None,
                reason=f"Open workspace for {seed.intent}",
            )
            if link is not None:
                allowed_links.append(link)
            elif decision.missing_permissions:
                missing_permissions.extend(decision.missing_permissions)

        payload = AssistantWorkflowHelpRead(
            intent=seed.intent,
            title=seed.title,
            facts=facts,
            allowed_links=allowed_links,
            missing_permissions=missing_permissions,
            safe_note=None,
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)


def _to_request_context(context: AssistantToolExecutionContext) -> RequestAuthorizationContext:
    scopes = tuple(
        AuthenticatedRoleScope(role_key=role_key, scope_type="tenant")
        for role_key in sorted(context.role_keys)
    ) or (AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),)
    return RequestAuthorizationContext(
        session_id="assistant-tool-session",
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        role_keys=frozenset(context.role_keys),
        permission_keys=frozenset(context.permission_keys),
        scopes=scopes,
        request_id="assistant-tool-request",
    )
