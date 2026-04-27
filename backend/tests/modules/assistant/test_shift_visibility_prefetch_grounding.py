from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolRegistry,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)
from tests.modules.assistant.test_operational_diagnostic_tool_loop import _context
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


class _AnyPayload(BaseModel):
    model_config = ConfigDict(extra="allow")


@dataclass
class _StubTool:
    name: str
    payload: dict[str, Any]
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.definition = AssistantToolDefinition(
            name=self.name,
            description=self.name,
            input_schema=_AnyPayload,
            output_schema=_AnyPayload,
            required_permissions=["assistant.chat.access"],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        del context
        self.calls.append(input_data.model_dump(mode="json", exclude_none=True))
        return AssistantToolResult(
            ok=True,
            tool_name=self.name,
            data=self.payload,
            redacted_output=self.payload,
        )


def _service_with_registry(*tools: _StubTool) -> tuple[AssistantService, InMemoryAssistantRepository]:
    repository = InMemoryAssistantRepository()
    registry = AssistantToolRegistry()
    for tool in tools:
        registry.register(tool)
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            env="development",
            openai_configured=True,
            mock_provider_allowed=False,
            response_model="gpt-4o",
            store_responses=False,
            max_tool_calls=4,
        ),
        repository=repository,
        provider=MockAssistantProvider(),
        tool_registry=registry,
    )
    return service, repository


def test_prefetch_grounding_adds_generic_diagnostic_fact_and_missing_inputs() -> None:
    capabilities = _StubTool(
        "assistant.get_current_user_capabilities",
        {
            "scope_kind": "tenant",
            "assistant_capabilities": {
                "can_chat": True,
                "can_run_diagnostics": True,
                "can_receive_navigation_links": True,
            },
        },
    )
    accessible_page = _StubTool(
        "assistant.search_accessible_pages",
        {"pages": [{"page_id": "E-01", "label": "Mitarbeiter", "module_key": "employees", "path_template": "/admin/employees"}]},
    )
    page_help = _StubTool(
        "assistant.get_page_help_manifest",
        {"page_id": "E-01", "page_title": "Mitarbeiter", "module_key": "employees", "source_status": "verified"},
    )
    link_builder = _StubTool(
        "navigation.build_allowed_link",
        {
            "allowed": True,
            "link": {"label": "Mitarbeiter", "path": "/admin/employees", "page_id": "E-01"},
        },
    )
    service, repository = _service_with_registry(capabilities, accessible_page, page_help, link_builder)
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )

    grounding_context, summaries = service._build_grounding_context(  # noqa: SLF001
        conversation=conversation,
        cleaned_message="Ich habe einem Mitarbeiter eine Schicht zugewiesen, aber sie wird in der mobilen App nicht angezeigt. Woran könnte das liegen?",
        route_context=None,
        detected_language="de",
        response_language="de",
        actor=_context(),
    )

    assert grounding_context.retrieval_plan["diagnostic_intent"] == "employee_shift_not_visible_in_mobile_app"
    assert "employee_name" in grounding_context.retrieval_plan["diagnostic_missing_inputs"]
    source_types = {source.source_type for source in grounding_context.sources}
    assert "diagnostic_fact" in source_types
    assert "missing_diagnostic_input" in source_types
    assert "allowed_navigation_link" in source_types
    assert "tool_result_summary" in source_types
    assert any(item.tool_name == "assistant.get_current_user_capabilities" for item in summaries)
    assert any(item.tool_name == "navigation.build_allowed_link" for item in summaries)


def test_prefetch_grounding_runs_specific_employee_and_visibility_checks_when_inputs_exist() -> None:
    capabilities = _StubTool("assistant.get_current_user_capabilities", {"scope_kind": "tenant"})
    accessible_page = _StubTool("assistant.search_accessible_pages", {"pages": []})
    page_help = _StubTool("assistant.get_page_help_manifest", {"page_id": "P-04", "page_title": "Staffing", "module_key": "planning", "source_status": "verified"})
    employee_search = _StubTool(
        "employees.search_employee_by_name",
        {"matches": [{"employee_ref": "emp-1", "display_name": "Markus"}], "match_count": 1, "truncated": False},
    )
    employee_profile = _StubTool(
        "employees.get_employee_operational_profile",
        {"found": True, "employee": {"employee_ref": "emp-1", "display_name": "Markus", "status": "active", "is_active": True, "has_user_link": True}},
    )
    mobile_access = _StubTool(
        "employees.get_employee_mobile_access_status",
        {"found": True, "mobile_access": {"has_linked_user_account": True, "self_service_enabled": True, "mobile_context_available": True, "can_receive_released_schedules": False, "blocking_reasons": [{"code": "missing_release", "severity": "blocking", "message": "Shift not released"}]}},
    )
    readiness = _StubTool(
        "employees.get_employee_readiness_summary",
        {"found": True, "readiness": {"employee_status": "active", "has_active_absence_on_date": False, "availability_summary": "available", "qualification_summary": {"has_expired_qualifications": False, "has_missing_required_qualification": False}, "credential_summary": {"has_active_credential": True, "has_expired_credential": False}, "blocking_reasons": []}},
    )
    assignments = _StubTool(
        "planning.find_assignments",
        {"matches": [{"assignment_ref": "asg-1", "shift_ref": "shift-1"}], "match_count": 1, "truncated": False},
    )
    shifts = _StubTool(
        "planning.find_shifts",
        {"matches": [{"shift_ref": "shift-1"}], "match_count": 1, "truncated": False},
    )
    inspect_assignment = _StubTool(
        "planning.inspect_assignment",
        {"found": True, "assignment": {"assignment_ref": "asg-1", "shift_ref": "shift-1", "assignment_status": "active"}},
    )
    release_state = _StubTool(
        "planning.inspect_shift_release_state",
        {"found": True, "release_state": {"shift_ref": "shift-1", "shift_release_state": "not_released", "is_released_for_employee_app": False}},
    )
    visibility = _StubTool(
        "planning.inspect_shift_visibility",
        {"found": True, "visibility": {"shift_ref": "shift-1", "visibility_state": "not_visible", "employee_visible": False, "stealth_mode_flag": False, "blocking_reasons": [{"code": "visibility_flag_disabled", "severity": "blocking", "message": "Employee visibility disabled"}]}},
    )
    released_schedule = _StubTool(
        "field.inspect_released_schedule_visibility",
        {"found": True, "visibility": {"employee_ref": "emp-1", "assignment_ref": "asg-1", "shift_ref": "shift-1", "visible": False, "visibility_state": "not_visible", "blocking_reasons": [{"code": "schedule_not_released", "severity": "blocking", "message": "Released schedule does not include shift"}]}},
    )
    link_builder = _StubTool(
        "navigation.build_allowed_link",
        {"allowed": True, "link": {"label": "Planung", "path": "/admin/planning-staffing", "page_id": "P-04"}},
    )
    service, repository = _service_with_registry(
        capabilities,
        accessible_page,
        page_help,
        employee_search,
        employee_profile,
        mobile_access,
        readiness,
        assignments,
        shifts,
        inspect_assignment,
        release_state,
        visibility,
        released_schedule,
        link_builder,
    )
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )

    grounding_context, _summaries = service._build_grounding_context(  # noqa: SLF001
        conversation=conversation,
        cleaned_message="Markus sieht seine zugewiesene Schicht am 1. Mai 2026 nicht in der mobilen App. Woran könnte das liegen?",
        route_context={"page_id": "P-04"},
        detected_language="de",
        response_language="de",
        actor=_context(),
    )

    assert grounding_context.retrieval_plan["diagnostic_intent"] == "employee_shift_not_visible_in_mobile_app"
    assert employee_search.calls
    assert employee_profile.calls
    assert mobile_access.calls
    assert readiness.calls
    assert assignments.calls
    assert shifts.calls
    assert inspect_assignment.calls
    assert release_state.calls
    assert visibility.calls
    assert released_schedule.calls
    assert any(
        source.source_type == "tool_result_summary"
        and source.source_name == "Released schedule visibility"
        for source in grounding_context.sources
    )
