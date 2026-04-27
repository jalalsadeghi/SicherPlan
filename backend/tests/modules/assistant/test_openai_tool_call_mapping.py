from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import AssistantToolAuditRecord, AssistantToolRegistry
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


class _LookupInput(BaseModel):
    query: str


class _LookupOutput(BaseModel):
    summary: str


class _CapturingAuditRepository:
    def __init__(self) -> None:
        self.records: list[AssistantToolAuditRecord] = []

    def create_tool_call_audit(self, *, record: AssistantToolAuditRecord):
        self.records.append(record)
        return record


class _LookupTool:
    definition = AssistantToolDefinition(
        name="assistant.lookup_docs",
        description="Look up verified docs.",
        input_schema=_LookupInput,
        output_schema=_LookupOutput,
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
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data={"summary": f"Resolved {input_data.query}"},
            redacted_output={"summary": f"Resolved {input_data.query}"},
        )


@dataclass
class _MappingProvider:
    requests: list[AssistantProviderRequest]

    def __init__(self, *, tool_name: str) -> None:
        self.requests = []
        self.tool_name = tool_name

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        if len(self.requests) == 1:
            return AssistantProviderResult(
                final_response={},
                raw_text=None,
                requested_tool_calls=[
                    {
                        "id": "fc-1",
                        "name": self.tool_name,
                        "arguments": '{"query": "customer create"}',
                        "call_id": "call-1",
                    }
                ],
                provider_name="openai",
                provider_mode="openai",
                model_name="gpt-4o",
            )
        return AssistantProviderResult(
            final_response={
                "answer": "Done",
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text="Done",
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


def _service(provider, registry: AssistantToolRegistry) -> tuple[AssistantService, InMemoryAssistantRepository]:
    repository = InMemoryAssistantRepository()
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
    return service, repository


def test_provider_tool_call_name_is_mapped_back_to_internal_name_before_execution() -> None:
    audit_repository = _CapturingAuditRepository()
    registry = AssistantToolRegistry(audit_repository=audit_repository)
    registry.register(_LookupTool())
    provider = _MappingProvider(tool_name="assistant_lookup_docs")
    service, repository = _service(provider, registry)
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="How do I create a customer?"),
        _context(),
    )

    assert response.answer == "Done"
    matched = [record for record in audit_repository.records if record.tool_name == "assistant.lookup_docs"]
    assert matched
    assert matched[-1].tool_name == "assistant.lookup_docs"


def test_unknown_provider_tool_name_is_rejected_safely() -> None:
    audit_repository = _CapturingAuditRepository()
    registry = AssistantToolRegistry(audit_repository=audit_repository)
    registry.register(_LookupTool())
    provider = _MappingProvider(tool_name="unknown_provider_tool")
    service, repository = _service(provider, registry)
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="How do I create a customer?"),
        _context(),
    )

    assert response.answer == "Done"
    assert not any(record.tool_name == "assistant.lookup_docs" for record in audit_repository.records)
    assert any(
        item == {
            "type": "function_call_output",
            "call_id": "call-1",
            "output": '{"error_code": "assistant.tool.unknown_provider_tool_name", "error_message": "Unknown provider tool alias requested.", "ok": false, "provider_tool_name": "unknown_provider_tool"}',
        }
        for item in provider.requests[1].tool_results
    )
