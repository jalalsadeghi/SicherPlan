"""Read-only assistant tools for field and employee self-service visibility diagnostics."""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.assistant.diagnostics.released_schedule_visibility import (
    DENIED_PORTAL_ROLES,
    ReleasedScheduleVisibilityDiagnostics,
)
from app.modules.assistant.policy import ASSISTANT_DIAGNOSTICS_READ
from app.modules.assistant.schemas import (
    AssistantFieldReleasedScheduleVisibilityInput,
    AssistantFieldReleasedScheduleVisibilityRead,
)
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)
from app.modules.assistant.tools.errors import AssistantToolPermissionDeniedError
from app.modules.assistant.tools.redaction import redact_tool_payload


class InspectReleasedScheduleVisibilityTool:
    def __init__(self, *, diagnostics: ReleasedScheduleVisibilityDiagnostics) -> None:
        self.diagnostics = diagnostics
        self.definition = AssistantToolDefinition(
            name="field.inspect_released_schedule_visibility",
            description="Inspect whether an employee released schedule entry should be visible in employee self-service or mobile.",
            input_schema=AssistantFieldReleasedScheduleVisibilityInput,
            output_schema=AssistantFieldReleasedScheduleVisibilityRead,
            required_permissions=["assistant.chat.access"],
            scope_behavior=AssistantToolScopeBehavior.EMPLOYEE_SELF_SERVICE,
            redaction_policy="released_schedule_visibility_safe",
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        if context.role_keys & DENIED_PORTAL_ROLES:
            raise AssistantToolPermissionDeniedError("Portal users may not inspect employee self-service schedule visibility.")
        if "employee_user" not in context.role_keys and ASSISTANT_DIAGNOSTICS_READ not in context.permission_keys:
            raise AssistantToolPermissionDeniedError("Assistant diagnostics access is required for internal schedule visibility checks.")

        result = self.diagnostics.inspect(
            actor=context.auth_context,
            employee_ref=getattr(input_data, "employee_ref", None),
            assignment_ref=getattr(input_data, "assignment_ref", None),
            shift_ref=getattr(input_data, "shift_ref", None),
            date_value=getattr(input_data, "date", None),
            date_from=getattr(input_data, "date_from", None),
            date_to=getattr(input_data, "date_to", None),
            target_channel=getattr(input_data, "target_channel", None),
        )
        payload = result.model_dump(mode="json")
        entity_refs = {
            key: payload["visibility"].get(key)
            for key in ("employee_ref", "assignment_ref", "shift_ref")
            if payload.get("visibility") and payload["visibility"].get(key) is not None
        }
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=payload,
            redacted_output=redact_tool_payload(payload),
            entity_refs=entity_refs or None,
        )
