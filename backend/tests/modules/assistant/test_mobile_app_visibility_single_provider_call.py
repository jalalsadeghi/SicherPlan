from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.router import add_assistant_message, router
from app.modules.assistant.schemas import AssistantMessageCreate
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


@dataclass
class _SingleCallDiagnosticProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        if request.available_tools:
            return AssistantProviderResult(
                final_response={},
                raw_text=None,
                requested_tool_calls=[
                    {
                        "id": "fc-diag-1",
                        "name": "assistant_diagnose_employee_shift_visibility",
                        "provider_tool_name": "assistant_diagnose_employee_shift_visibility",
                        "arguments": "{}",
                        "call_id": "call-diag-1",
                    }
                ],
                provider_name="openai",
                provider_mode="openai",
                model_name="gpt-4o",
            )

        sources = []
        if request.grounding_context:
            raw_sources = request.grounding_context.get("sources")
            if isinstance(raw_sources, list):
                sources = [item for item in raw_sources if isinstance(item, dict)]

        links: list[dict[str, Any]] = []
        for source in sources:
            if source.get("source_type") == "allowed_navigation_link":
                facts = source.get("facts")
                if isinstance(facts, dict) and isinstance(facts.get("link"), dict):
                    links.append(facts["link"])
        missing_inputs: list[str] = []
        retrieval_plan = request.grounding_context.get("retrieval_plan") if request.grounding_context else {}
        if isinstance(retrieval_plan, dict):
            raw_missing = retrieval_plan.get("diagnostic_missing_inputs")
            if isinstance(raw_missing, list):
                missing_inputs = [str(item) for item in raw_missing]

        if missing_inputs:
            answer = (
                "Ich habe die typischen Sichtbarkeitsprüfungen vorbereitet. "
                "Bitte nennen Sie mir den Mitarbeiter und das Datum der Schicht, damit ich die mobile Sichtbarkeit gezielt prüfen kann. "
                "Häufige Ursachen sind der mobile Zugang des Mitarbeiters, der Zuweisungsstatus, die Freigabe der Schicht oder die Sichtbarkeit im freigegebenen Mitarbeiterplan."
            )
            next_steps = ["Bitte Mitarbeiter und Datum nennen."]
        else:
            answer = (
                "Ich habe die vorbereiteten Sichtbarkeitsprüfungen ausgewertet. "
                "Die mobile Freigabe hängt typischerweise vom Mitarbeiterzugang, dem aktiven Zuweisungsstatus, dem Freigabestatus der Schicht und der Sichtbarkeit im freigegebenen Mitarbeiterplan ab."
            )
            next_steps = ["Öffnen Sie die Planung und prüfen Sie Freigabe sowie Sichtbarkeitsflags."]

        return AssistantProviderResult(
            final_response={
                "answer": answer,
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": links[:3],
                "missing_permissions": [],
                "next_steps": next_steps,
                "tool_trace_id": None,
            },
            raw_text=answer,
            provider_name="openai",
            provider_mode="openai",
            model_name="gpt-4o",
        )


def _service_with_registry(*tools: _StubTool) -> tuple[AssistantService, InMemoryAssistantRepository, _SingleCallDiagnosticProvider]:
    repository = InMemoryAssistantRepository()
    registry = AssistantToolRegistry()
    for tool in tools:
        registry.register(tool)
    provider = _SingleCallDiagnosticProvider()
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
        provider=provider,
        tool_registry=registry,
    )
    return service, repository, provider


def _generic_prefetch_tools() -> list[_StubTool]:
    return [
        _StubTool(
            "assistant.get_current_user_capabilities",
            {"scope_kind": "tenant", "assistant_capabilities": {"can_chat": True, "can_run_diagnostics": True}},
        ),
        _StubTool(
            "assistant.search_accessible_pages",
            {"pages": [{"page_id": "P-04", "label": "Staffing", "module_key": "planning", "path_template": "/admin/planning-staffing"}]},
        ),
        _StubTool(
            "assistant.get_page_help_manifest",
            {"page_id": "P-04", "page_title": "Staffing", "module_key": "planning", "source_status": "verified"},
        ),
        _StubTool(
            "navigation.build_allowed_link",
            {"allowed": True, "link": {"label": "Staffing", "path": "/admin/planning-staffing", "page_id": "P-04", "reason": "Inspect staffing visibility."}},
        ),
    ]


def test_german_mobile_app_visibility_question_without_employee_or_date_uses_single_provider_call() -> None:
    service, repository, provider = _service_with_registry(*_generic_prefetch_tools())
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    messages_route = next(
        route
        for route in router.routes
        if getattr(route, "path", "") == "/api/assistant/conversations/{conversation_id}/messages"
    )

    payload = add_assistant_message(
        UUID(conversation.id),
        AssistantMessageCreate(
            message="Ich habe einem Mitarbeiter eine Schicht zugewiesen, aber sie wird in der mobilen App nicht angezeigt. Woran könnte das liegen?"
        ),
        _context(),
        service,
    )

    assert messages_route.status_code == 201
    assert payload.response_language == "de"
    assert "Bitte nennen Sie mir den Mitarbeiter und das Datum" in payload.answer
    assert provider.requests[0].available_tools == []
    assert len(provider.requests) == 1


def test_german_mobile_app_visibility_question_with_employee_and_date_runs_prefetch_and_returns_links() -> None:
    service, repository, provider = _service_with_registry(
        *_generic_prefetch_tools(),
        _StubTool(
            "employees.search_employee_by_name",
            {"matches": [{"employee_ref": "emp-1", "display_name": "Markus"}], "match_count": 1, "truncated": False},
        ),
        _StubTool(
            "employees.get_employee_operational_profile",
            {"found": True, "employee": {"employee_ref": "emp-1", "display_name": "Markus", "status": "active", "is_active": True, "has_user_link": True}},
        ),
        _StubTool(
            "employees.get_employee_mobile_access_status",
            {"found": True, "mobile_access": {"has_linked_user_account": True, "self_service_enabled": True, "mobile_context_available": True, "can_receive_released_schedules": False, "blocking_reasons": [{"code": "missing_release", "severity": "blocking", "message": "Shift not released"}]}},
        ),
        _StubTool(
            "employees.get_employee_readiness_summary",
            {"found": True, "readiness": {"employee_status": "active", "has_active_absence_on_date": False, "availability_summary": "available", "qualification_summary": {"has_expired_qualifications": False, "has_missing_required_qualification": False}, "credential_summary": {"has_active_credential": True, "has_expired_credential": False}, "blocking_reasons": []}},
        ),
        _StubTool(
            "planning.find_assignments",
            {"matches": [{"assignment_ref": "asg-1", "shift_ref": "shift-1"}], "match_count": 1, "truncated": False},
        ),
        _StubTool(
            "planning.find_shifts",
            {"matches": [{"shift_ref": "shift-1"}], "match_count": 1, "truncated": False},
        ),
        _StubTool(
            "planning.inspect_assignment",
            {"found": True, "assignment": {"assignment_ref": "asg-1", "shift_ref": "shift-1", "assignment_status": "active"}},
        ),
        _StubTool(
            "planning.inspect_shift_release_state",
            {"found": True, "release_state": {"shift_ref": "shift-1", "shift_release_state": "not_released", "is_released_for_employee_app": False}},
        ),
        _StubTool(
            "planning.inspect_shift_visibility",
            {"found": True, "visibility": {"shift_ref": "shift-1", "visibility_state": "not_visible", "employee_visible": False, "stealth_mode_flag": False, "blocking_reasons": [{"code": "visibility_flag_disabled", "severity": "blocking", "message": "Employee visibility disabled"}]}},
        ),
        _StubTool(
            "field.inspect_released_schedule_visibility",
            {"found": True, "visibility": {"employee_ref": "emp-1", "assignment_ref": "asg-1", "shift_ref": "shift-1", "visible": False, "visibility_state": "not_visible", "blocking_reasons": [{"code": "schedule_not_released", "severity": "blocking", "message": "Released schedule does not include shift"}]}},
        ),
    )
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )

    payload = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="Markus sieht seine zugewiesene Schicht am 1. Mai 2026 nicht in der mobilen App. Woran könnte das liegen?"
        ),
        _context(),
    )

    assert payload.response_language == "de"
    assert payload.links
    assert payload.links[0].page_id == "P-04"
    assert provider.requests[0].available_tools == []
    assert len(provider.requests) == 1


def test_prefetch_path_avoids_502_when_provider_would_otherwise_request_tools() -> None:
    service, repository, provider = _service_with_registry(*_generic_prefetch_tools())
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="Ich habe einem Mitarbeiter eine Arbeitsschicht zugewiesen, diese wird jedoch in der mobilen App nicht angezeigt. Woran könnte das liegen?"
        ),
        _context(),
    )

    assert response.out_of_scope is False
    assert len(provider.requests) == 1
    assert provider.requests[0].available_tools == []
