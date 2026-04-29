"""Central registry for assistant backend tools."""

from __future__ import annotations

from dataclasses import dataclass
import re
from time import perf_counter
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError

from app.modules.assistant.policy import ASSISTANT_CHAT_ACCESS
from app.modules.assistant.tools.base import (
    AssistantTool,
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
)
from app.modules.assistant.tools.errors import (
    AssistantToolDisabledError,
    AssistantToolExecutionError,
    AssistantToolInputValidationError,
    AssistantToolNotFoundError,
    AssistantToolPermissionDeniedError,
    AssistantToolWriteBlockedError,
)
from app.modules.assistant.tools.redaction import redact_tool_payload


_SQL_KEY_RE = re.compile(r"^(sql|raw_sql|statement|sql_query|query_sql)$", re.IGNORECASE)
_SQL_VALUE_RE = re.compile(
    r"\b(select|insert|update|delete|drop|alter|truncate|grant|revoke)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AssistantToolAuditRecord:
    conversation_id: str | None
    message_id: str | None
    tenant_id: str | None
    user_id: str
    tool_name: str
    input_json: dict[str, Any]
    output_json_summary: dict[str, Any] | None
    required_permissions: list[str]
    permission_decision: str
    scope_kind: str
    entity_refs: dict[str, Any] | None
    duration_ms: int | None
    error_code: str | None


class AssistantToolAuditRepository(Protocol):
    def create_tool_call_audit(self, *, record: AssistantToolAuditRecord) -> Any: ...


class AssistantToolRegistry:
    def __init__(
        self,
        *,
        audit_repository: AssistantToolAuditRepository | None = None,
    ) -> None:
        self.audit_repository = audit_repository
        self._tools: dict[str, AssistantTool] = {}

    def register(self, tool: AssistantTool) -> None:
        self._tools[tool.definition.name] = tool

    def get_tool(self, name: str) -> AssistantTool:
        tool = self._tools.get(name)
        if tool is None:
            raise AssistantToolNotFoundError("Requested assistant tool is not registered.")
        return tool

    def list_available_tools(self, *, context: AssistantToolExecutionContext) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda item: item.definition.name):
            definition = tool.definition
            if not definition.enabled:
                continue
            if definition.classification != AssistantToolClassification.READ_ONLY:
                continue
            if not self._has_required_permissions(context, definition):
                continue
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": definition.name,
                        "description": definition.description,
                        "parameters": definition.input_schema.model_json_schema(),
                    },
                }
            )
        return tools

    def execute_tool(
        self,
        *,
        tool_name: str,
        input_data: dict[str, Any],
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        started = perf_counter()
        safe_input = redact_tool_payload(input_data)
        try:
            tool = self.get_tool(tool_name)
            definition = tool.definition
            self._ensure_enabled(definition)
            self._ensure_read_only(definition)
            self._ensure_permissions(context, definition)
            validated_input = self._validate_input(definition.input_schema, input_data)
            result = tool.execute(input_data=validated_input, context=context)
            validated_output = self._validate_output(definition.output_schema, result.data or {})
            duration_ms = max(int((perf_counter() - started) * 1000), 0)
            redacted_output = redact_tool_payload(validated_output)
            safe_result = AssistantToolResult(
                ok=result.ok,
                tool_name=tool_name,
                data=redacted_output,
                error_code=result.error_code,
                error_message=result.error_message,
                missing_permissions=result.missing_permissions,
                redacted_output=redacted_output,
                entity_refs=result.entity_refs,
                duration_ms=duration_ms,
                permission_decision="allowed",
            )
            self._audit(
                context=context,
                definition=definition,
                input_json=safe_input,
                output_json_summary=redacted_output,
                permission_decision="allowed",
                entity_refs=result.entity_refs,
                duration_ms=duration_ms,
                error_code=result.error_code,
            )
            return safe_result
        except AssistantToolPermissionDeniedError as exc:
            duration_ms = max(int((perf_counter() - started) * 1000), 0)
            missing_permissions = _build_missing_permissions(
                required_permissions=self._required_permissions_for_tool(tool_name),
            )
            self._audit(
                context=context,
                definition=None,
                tool_name=tool_name,
                input_json=safe_input,
                output_json_summary=None,
                permission_decision="denied",
                entity_refs=None,
                duration_ms=duration_ms,
                error_code=exc.code,
            )
            return AssistantToolResult(
                ok=False,
                tool_name=tool_name,
                error_code=exc.code,
                error_message="Permission denied.",
                missing_permissions=missing_permissions,
                duration_ms=duration_ms,
                permission_decision="denied",
            )
        except (
            AssistantToolNotFoundError,
            AssistantToolDisabledError,
            AssistantToolWriteBlockedError,
            AssistantToolInputValidationError,
            AssistantToolExecutionError,
        ) as exc:
            duration_ms = max(int((perf_counter() - started) * 1000), 0)
            self._audit(
                context=context,
                definition=None,
                tool_name=tool_name,
                input_json=safe_input,
                output_json_summary=None,
                permission_decision="failed",
                entity_refs=None,
                duration_ms=duration_ms,
                error_code=exc.code,
            )
            return AssistantToolResult(
                ok=False,
                tool_name=tool_name,
                error_code=exc.code,
                error_message=_safe_error_message(exc),
                duration_ms=duration_ms,
                permission_decision="failed",
            )
        except Exception as exc:
            duration_ms = max(int((perf_counter() - started) * 1000), 0)
            self._audit(
                context=context,
                definition=None,
                tool_name=tool_name,
                input_json=safe_input,
                output_json_summary=None,
                permission_decision="failed",
                entity_refs=None,
                duration_ms=duration_ms,
                error_code=AssistantToolExecutionError.code,
            )
            return AssistantToolResult(
                ok=False,
                tool_name=tool_name,
                error_code=AssistantToolExecutionError.code,
                error_message="Tool execution failed safely.",
                duration_ms=duration_ms,
                permission_decision="failed",
            )

    def _ensure_enabled(self, definition: AssistantToolDefinition) -> None:
        if not definition.enabled:
            raise AssistantToolDisabledError("Requested assistant tool is disabled.")

    def _ensure_read_only(self, definition: AssistantToolDefinition) -> None:
        if definition.classification != AssistantToolClassification.READ_ONLY:
            raise AssistantToolWriteBlockedError("Write-capable tools are blocked in this sprint.")

    def _ensure_permissions(
        self,
        context: AssistantToolExecutionContext,
        definition: AssistantToolDefinition,
    ) -> None:
        if ASSISTANT_CHAT_ACCESS not in context.permission_keys:
            raise AssistantToolPermissionDeniedError("Assistant chat access is required.")
        if not self._has_required_permissions(context, definition):
            raise AssistantToolPermissionDeniedError("Required tool permissions are missing.")

    @staticmethod
    def _has_required_permissions(
        context: AssistantToolExecutionContext,
        definition: AssistantToolDefinition,
    ) -> bool:
        return all(permission in context.permission_keys for permission in definition.required_permissions)

    @staticmethod
    def _validate_input(schema: type[BaseModel], input_data: dict[str, Any]) -> BaseModel:
        if _contains_sql_payload(input_data):
            raise AssistantToolInputValidationError("SQL-like tool input is not allowed.")
        try:
            return schema.model_validate(input_data)
        except ValidationError as exc:
            raise AssistantToolInputValidationError("Tool input validation failed.") from exc

    @staticmethod
    def _validate_output(schema: type[BaseModel], output_data: dict[str, Any]) -> dict[str, Any]:
        try:
            return schema.model_validate(output_data).model_dump(mode="json")
        except ValidationError as exc:
            raise AssistantToolExecutionError("Tool output validation failed.") from exc

    def _audit(
        self,
        *,
        context: AssistantToolExecutionContext,
        input_json: dict[str, Any],
        output_json_summary: dict[str, Any] | None,
        permission_decision: str,
        entity_refs: dict[str, Any] | None,
        duration_ms: int | None,
        error_code: str | None,
        definition: AssistantToolDefinition | None = None,
        tool_name: str | None = None,
    ) -> None:
        if self.audit_repository is None:
            return
        effective_name = tool_name or (definition.name if definition is not None else "unknown")
        required_permissions = list(definition.required_permissions) if definition is not None else []
        self.audit_repository.create_tool_call_audit(
            record=AssistantToolAuditRecord(
                conversation_id=context.conversation_id,
                message_id=context.message_id,
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                tool_name=effective_name,
                input_json=input_json,
                output_json_summary=output_json_summary,
                required_permissions=required_permissions,
                permission_decision=permission_decision,
                scope_kind=context.scope_kind,
                entity_refs=entity_refs,
                duration_ms=duration_ms,
                error_code=error_code,
            )
        )

    def _required_permissions_for_tool(self, tool_name: str) -> list[str]:
        tool = self._tools.get(tool_name)
        if tool is None:
            return []
        return list(tool.definition.required_permissions)


def build_default_tool_registry(
    *,
    audit_repository: AssistantToolAuditRepository | None = None,
    page_catalog_repository: Any | None = None,
    page_help_repository: Any | None = None,
    employee_repository: Any | None = None,
    planning_repository: Any | None = None,
    customer_repository: Any | None = None,
    subcontractor_repository: Any | None = None,
    core_repository: Any | None = None,
) -> AssistantToolRegistry:
    from app.modules.assistant.diagnostics.released_schedule_visibility import (
        ReleasedScheduleVisibilityDiagnostics,
        ReleasedScheduleVisibilityRepositoryAdapter,
    )
    from app.modules.assistant.diagnostics.shift_visibility import (
        DiagnoseEmployeeShiftVisibilityTool,
        ShiftVisibilityDiagnosticService,
    )
    from app.modules.assistant.tools.context_tools import GetCurrentPageContextTool
    from app.modules.assistant.tools.employee_tools import (
        GetEmployeeMobileAccessStatusTool,
        GetEmployeeOperationalProfileTool,
        GetEmployeeReadinessSummaryTool,
        SearchEmployeeByNameTool,
    )
    from app.modules.assistant.tools.field_dictionary_tools import (
        ExplainLookupOrOptionTool,
        SearchFieldDictionaryTool,
        SearchLookupDictionaryTool,
        SearchPlatformTermsTool,
    )
    from app.modules.assistant.tools.field_tools import InspectReleasedScheduleVisibilityTool
    from app.modules.assistant.tools.navigation_tools import BuildAllowedLinkTool, SearchAccessiblePagesTool
    from app.modules.assistant.tools.page_help_tools import FindUiActionTool, GetPageHelpManifestTool
    from app.modules.assistant.tools.planning_tools import (
        FindAssignmentsTool,
        FindShiftsTool,
        InspectAssignmentTool,
        InspectAssignmentValidationsTool,
        InspectShiftReleaseStateTool,
        InspectShiftReleaseValidationsTool,
        InspectShiftVisibilityTool,
    )
    from app.modules.assistant.tools.user_tools import GetCurrentUserCapabilitiesTool
    from app.modules.assistant.tools.workflow_help_tools import SearchWorkflowHelpTool
    from app.modules.planning.released_schedule_service import ReleasedScheduleService
    from app.modules.planning.validation_service import PlanningValidationService

    registry = AssistantToolRegistry(audit_repository=audit_repository)
    registry.register(GetCurrentUserCapabilitiesTool())
    registry.register(GetCurrentPageContextTool())
    registry.register(SearchFieldDictionaryTool())
    registry.register(SearchLookupDictionaryTool())
    registry.register(SearchPlatformTermsTool())
    registry.register(
        ExplainLookupOrOptionTool(
            customer_repository=customer_repository,
            subcontractor_repository=subcontractor_repository,
            core_repository=core_repository,
        )
    )
    if page_help_repository is not None:
        registry.register(GetPageHelpManifestTool(repository=page_help_repository))
        registry.register(FindUiActionTool(repository=page_help_repository))
    if page_catalog_repository is not None:
        registry.register(SearchAccessiblePagesTool(repository=page_catalog_repository))
        registry.register(BuildAllowedLinkTool(repository=page_catalog_repository))
        registry.register(SearchWorkflowHelpTool(repository=page_catalog_repository))
    if employee_repository is not None:
        registry.register(SearchEmployeeByNameTool(repository=employee_repository))
        registry.register(GetEmployeeOperationalProfileTool(repository=employee_repository))
        registry.register(GetEmployeeMobileAccessStatusTool(repository=employee_repository))
        registry.register(GetEmployeeReadinessSummaryTool(repository=employee_repository))
    if planning_repository is not None:
        validation_service = PlanningValidationService(planning_repository)
        registry.register(FindShiftsTool(repository=planning_repository))
        registry.register(FindAssignmentsTool(repository=planning_repository))
        registry.register(InspectAssignmentTool(repository=planning_repository))
        registry.register(InspectShiftReleaseStateTool(repository=planning_repository))
        registry.register(InspectShiftVisibilityTool(repository=planning_repository))
        registry.register(
            InspectAssignmentValidationsTool(
                repository=planning_repository,
                validation_service=validation_service,
            )
        )
        registry.register(
            InspectShiftReleaseValidationsTool(
                repository=planning_repository,
                validation_service=validation_service,
            )
        )
    if planning_repository is not None and employee_repository is not None:
        registry.register(
            InspectReleasedScheduleVisibilityTool(
                diagnostics=ReleasedScheduleVisibilityDiagnostics(
                    repository=ReleasedScheduleVisibilityRepositoryAdapter(
                        planning_repository=planning_repository,
                        employee_repository=employee_repository,
                    ),
                    released_schedule_service=ReleasedScheduleService(planning_repository),
                )
            )
        )
    if (
        planning_repository is not None
        and employee_repository is not None
        and page_catalog_repository is not None
    ):
        registry.register(
            DiagnoseEmployeeShiftVisibilityTool(
                diagnostic_service=ShiftVisibilityDiagnosticService(tool_runner=registry)
            )
        )
    return registry


def _build_missing_permissions(*, required_permissions: list[str]) -> list[dict[str, str]]:
    return [
        {
            "permission": permission,
            "reason": "The current user does not have the required permission for this assistant tool.",
        }
        for permission in required_permissions
    ]


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, AssistantToolNotFoundError):
        return "Assistant tool not found."
    if isinstance(exc, AssistantToolDisabledError):
        return "Assistant tool is disabled."
    if isinstance(exc, AssistantToolWriteBlockedError):
        return "Write-capable tools are blocked in this sprint."
    if isinstance(exc, AssistantToolInputValidationError):
        return "Tool input is invalid."
    if isinstance(exc, AssistantToolExecutionError):
        return "Tool execution failed safely."
    return "Tool execution failed safely."


def _contains_sql_payload(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if _SQL_KEY_RE.search(str(key)):
                return True
            if _contains_sql_payload(item):
                return True
        return False
    if isinstance(value, list):
        return any(_contains_sql_payload(item) for item in value[:20])
    if isinstance(value, str):
        return bool(_SQL_VALUE_RE.search(value))
    return False
