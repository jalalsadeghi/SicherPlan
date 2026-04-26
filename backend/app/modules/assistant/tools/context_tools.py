"""Assistant tools for frontend page-context hints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.modules.assistant.knowledge.types import PAGE_ID_TO_MODULE_KEY
from app.modules.assistant.schemas import (
    AssistantCurrentPageContextInput,
    AssistantCurrentPageContextRead,
)
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)


_SUSPICIOUS_QUERY_KEYS = {
    "token",
    "jwt",
    "password",
    "secret",
    "reset",
    "code",
    "auth",
    "apikey",
    "api_key",
}
_MAX_QUERY_ITEMS = 10
_MAX_PATH_LEN = 500
_MAX_ROUTE_NAME_LEN = 255
_MAX_PAGE_ID_LEN = 120
_MAX_QUERY_VALUE_LEN = 120


class GetCurrentPageContextTool:
    definition = AssistantToolDefinition(
        name="assistant.get_current_page_context",
        description="Normalize current frontend route context as a non-authoritative assistant hint.",
        input_schema=AssistantCurrentPageContextInput,
        output_schema=AssistantCurrentPageContextRead,
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
        del context
        safe_query = _sanitize_query(getattr(input_data, "query", None) or {})
        path = _bound_text(getattr(input_data, "path", None), _MAX_PATH_LEN)
        route_name = _bound_text(getattr(input_data, "route_name", None), _MAX_ROUTE_NAME_LEN)
        page_id = _bound_text(getattr(input_data, "page_id", None), _MAX_PAGE_ID_LEN)
        module_hint = _infer_module_hint(path=path, route_name=route_name, page_id=page_id)
        is_known_page = _is_known_page(path=path, route_name=route_name, page_id=page_id)
        payload = AssistantCurrentPageContextRead(
            path=path,
            route_name=route_name,
            page_id=page_id,
            module_hint=module_hint,
            ui_locale=_bound_text(getattr(input_data, "ui_locale", None), 16),
            timezone=_bound_text(getattr(input_data, "timezone", None), 64),
            safe_query=safe_query,
            is_known_page=is_known_page,
            is_authoritative=False,
            notes=["Frontend route context is a hint only. Backend permissions still apply."],
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)
def _sanitize_query(values: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in list(values.items())[:_MAX_QUERY_ITEMS]:
        key_text = str(key).strip()[:64]
        if not key_text:
            continue
        if key_text.casefold() in _SUSPICIOUS_QUERY_KEYS:
            continue
        sanitized_value = _sanitize_query_value(value)
        if sanitized_value is not None:
            safe[key_text] = sanitized_value
    return safe


def _sanitize_query_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, float, int)):
        return value
    if isinstance(value, str):
        return value.strip()[:_MAX_QUERY_VALUE_LEN]
    if isinstance(value, list):
        return [item for item in (_sanitize_query_value(row) for row in value[:10]) if item is not None]
    return None


def _bound_text(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:max_length]


def _infer_module_hint(*, path: str | None, route_name: str | None, page_id: str | None) -> str | None:
    if page_id and page_id in PAGE_ID_TO_MODULE_KEY:
        return PAGE_ID_TO_MODULE_KEY[page_id]
    if path:
        lowered = path.casefold()
        if "planning" in lowered:
            return "planning"
        if "employee" in lowered:
            return "employees"
        if "customer" in lowered:
            return "customers"
        if "portal" in lowered:
            return "customer_portal"
    if route_name:
        lowered = route_name.casefold()
        if "planning" in lowered:
            return "planning"
        if "employee" in lowered:
            return "employees"
    return None


def _is_known_page(*, path: str | None, route_name: str | None, page_id: str | None) -> bool:
    known_page_ids = {"P-04", "E-01", "CP-01", "SP-01", "P-03", "P-05", "FI-01", "REP-01"}
    known_route_names = {
        "SicherPlanPlanningStaffing",
        "SicherPlanEmployees",
        "SicherPlanCustomerPortalOverview",
        "SicherPlanSubcontractorPortal",
        "SicherPlanPlanningShifts",
        "SicherPlanFinanceActuals",
        "SicherPlanReporting",
    }
    known_paths = {
        "/admin/planning-staffing",
        "/admin/employees",
        "/portal/customer/overview",
        "/portal/subcontractor",
        "/admin/planning-shifts",
        "/admin/finance-actuals",
        "/admin/reporting",
    }
    if page_id and page_id in known_page_ids:
        return True
    if route_name and route_name in known_route_names:
        return True
    return bool(path and path in known_paths)
