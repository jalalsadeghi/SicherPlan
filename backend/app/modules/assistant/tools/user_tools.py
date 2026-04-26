"""Assistant tools for current-user capability summaries."""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.assistant.policy import (
    can_user_chat,
    can_user_receive_navigation_links,
    can_user_reindex_knowledge,
    can_user_run_diagnostics,
    can_user_use_knowledge,
)
from app.modules.assistant.schemas import (
    AssistantCapabilitiesFlagsRead,
    AssistantCurrentUserCapabilitiesInput,
    AssistantCurrentUserCapabilitiesRead,
    AssistantScopeSummaryRead,
)
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)


class GetCurrentUserCapabilitiesTool:
    definition = AssistantToolDefinition(
        name="assistant.get_current_user_capabilities",
        description="Return a redacted summary of the current authenticated user's assistant-relevant capabilities.",
        input_schema=AssistantCurrentUserCapabilitiesInput,
        output_schema=AssistantCurrentUserCapabilitiesRead,
        required_permissions=["assistant.chat.access"],
        scope_behavior=AssistantToolScopeBehavior.CURRENT_USER,
        classification=AssistantToolClassification.READ_ONLY,
        redaction_policy="default",
    )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        del input_data
        auth = context.auth_context
        scope_summary = AssistantScopeSummaryRead(
            branch_ids=sorted({scope.branch_id for scope in auth.scopes if scope.branch_id}),
            mandate_ids=sorted({scope.mandate_id for scope in auth.scopes if scope.mandate_id}),
            customer_ids=sorted({scope.customer_id for scope in auth.scopes if scope.customer_id}),
            subcontractor_ids=sorted({scope.subcontractor_id for scope in auth.scopes if scope.subcontractor_id}),
        )
        payload = AssistantCurrentUserCapabilitiesRead(
            user_id=auth.user_id,
            tenant_id=auth.tenant_id,
            scope_kind=context.scope_kind,
            role_keys=sorted(auth.role_keys),
            permission_keys=sorted(auth.permission_keys),
            assistant_capabilities=AssistantCapabilitiesFlagsRead(
                can_chat=can_user_chat(auth),
                can_run_diagnostics=can_user_run_diagnostics(auth),
                can_use_knowledge=can_user_use_knowledge(auth),
                can_reindex_knowledge=can_user_reindex_knowledge(auth),
                can_receive_navigation_links=can_user_receive_navigation_links(auth),
            ),
            scope_summary=scope_summary,
            redactions_applied=True,
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)
