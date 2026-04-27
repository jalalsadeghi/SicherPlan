from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import AssistantToolRegistry
from app.modules.assistant.tools.base import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


class _DiagnosticInput(BaseModel):
    employee_name: str | None = None


class _DiagnosticOutput(BaseModel):
    status: str
    summary: str


class _ShiftVisibilityDiagnosticTool:
    definition = AssistantToolDefinition(
        name="assistant.diagnose_employee_shift_visibility",
        description="Inspect why an assigned shift is not visible in the employee app.",
        input_schema=_DiagnosticInput,
        output_schema=_DiagnosticOutput,
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
        employee_name = getattr(input_data, "employee_name", None) or "Mitarbeiter"
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data={
                "status": "not_visible",
                "summary": f"Die Schicht von {employee_name} ist nicht für die Mitarbeiter-App freigegeben.",
            },
            redacted_output={
                "status": "not_visible",
                "summary": f"Die Schicht von {employee_name} ist nicht für die Mitarbeiter-App freigegeben.",
            },
        )


@dataclass
class _OperationalDiagnosticProvider:
    requests: list[AssistantProviderRequest]

    def __init__(self) -> None:
        self.requests = []

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        if len(self.requests) == 1:
            return AssistantProviderResult(
                final_response={},
                raw_text=None,
                response_id="resp-diag-1",
                output_items=[
                    {
                        "type": "function_call",
                        "id": "fc-diag-1",
                        "call_id": "call-diag-1",
                        "name": "assistant_diagnose_employee_shift_visibility",
                        "arguments": '{"employee_name":"Markus"}',
                    }
                ],
                requested_tool_calls=[
                    {
                        "id": "fc-diag-1",
                        "name": "assistant_diagnose_employee_shift_visibility",
                        "provider_tool_name": "assistant_diagnose_employee_shift_visibility",
                        "arguments": '{"employee_name":"Markus"}',
                        "call_id": "call-diag-1",
                        "response_item": {
                            "type": "function_call",
                            "id": "fc-diag-1",
                            "call_id": "call-diag-1",
                            "name": "assistant_diagnose_employee_shift_visibility",
                            "arguments": '{"employee_name":"Markus"}',
                        },
                    }
                ],
                provider_name="openai",
                provider_mode="openai",
                model_name="gpt-4o",
            )
        return AssistantProviderResult(
            final_response={
                "answer": "Ich habe die Freigabe geprüft. Die Schicht ist Markus zugewiesen, aber noch nicht für die Mitarbeiter-App freigegeben.",
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text="Ich habe die Freigabe geprüft. Die Schicht ist Markus zugewiesen, aber noch nicht für die Mitarbeiter-App freigegeben.",
            provider_name="openai",
            provider_mode="openai",
            model_name="gpt-4o",
        )


def _context() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"assistant.chat.access"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )


def test_german_shift_visibility_question_completes_tool_continuation_loop() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    provider = _OperationalDiagnosticProvider()
    registry = AssistantToolRegistry()
    registry.register(_ShiftVisibilityDiagnosticTool())
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            env="development",
            openai_configured=True,
            mock_provider_allowed=False,
            response_model="gpt-4o",
            store_responses=False,
            max_tool_calls=8,
        ),
        repository=repository,
        provider=provider,
        tool_registry=registry,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="Ich habe einem Mitarbeiter eine Arbeitsschicht zugewiesen, diese wird jedoch in der mobilen App nicht angezeigt. Woran könnte das liegen?"
        ),
        _context(),
    )

    assert response.response_language == "de"
    assert response.answer.startswith("Ich habe die Freigabe geprüft.")
    assert len(provider.requests) == 2
    assert provider.requests[0].grounding_context is not None
    assert provider.requests[1].metadata["continuation_mode"] == "stateless"
    assert provider.requests[1].previous_response_id is None
    assert provider.requests[1].previous_output_items == [
        {
            "type": "function_call",
            "id": "fc-diag-1",
            "call_id": "call-diag-1",
            "name": "assistant_diagnose_employee_shift_visibility",
            "arguments": '{"employee_name":"Markus"}',
        }
    ]
    assert any(
        item.get("type") == "function_call_output"
        and item.get("call_id") == "call-diag-1"
        and item.get("output")
        == '{"status": "not_visible", "summary": "Die Schicht von Markus ist nicht für die Mitarbeiter-App freigegeben."}'
        for item in provider.requests[1].continuation_tool_outputs
    )
