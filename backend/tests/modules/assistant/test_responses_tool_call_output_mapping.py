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


class _LookupInput(BaseModel):
    query: str


class _LookupOutput(BaseModel):
    summary: str


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
class _CapturingLoopProvider:
    requests: list[AssistantProviderRequest]

    def __init__(self) -> None:
        self.requests = []

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        if len(self.requests) == 1:
            return AssistantProviderResult(
                final_response={},
                raw_text=None,
                response_id="resp-1",
                output_items=[
                    {
                        "type": "function_call",
                        "id": "fc-1",
                        "call_id": "call-1",
                        "name": "assistant_lookup_docs",
                        "arguments": '{"query":"customer create"}',
                    },
                    {
                        "type": "function_call",
                        "id": "fc-2",
                        "call_id": "call-2",
                        "name": "assistant_missing_tool",
                        "arguments": '{"query":"unknown"}',
                    },
                ],
                requested_tool_calls=[
                    {
                        "id": "fc-1",
                        "name": "assistant_lookup_docs",
                        "provider_tool_name": "assistant_lookup_docs",
                        "arguments": '{"query":"customer create"}',
                        "call_id": "call-1",
                        "response_item": {
                            "type": "function_call",
                            "id": "fc-1",
                            "call_id": "call-1",
                            "name": "assistant_lookup_docs",
                            "arguments": '{"query":"customer create"}',
                        },
                    },
                    {
                        "id": "fc-2",
                        "name": "assistant_missing_tool",
                        "provider_tool_name": "assistant_missing_tool",
                        "arguments": '{"query":"unknown"}',
                        "call_id": "call-2",
                        "response_item": {
                            "type": "function_call",
                            "id": "fc-2",
                            "call_id": "call-2",
                            "name": "assistant_missing_tool",
                            "arguments": '{"query":"unknown"}',
                        },
                    },
                ],
                provider_name="openai",
                provider_mode="openai",
                model_name="gpt-4o",
            )
        return AssistantProviderResult(
            final_response={
                "answer": "Nutzen Sie den Kunden-Workspace.",
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text="Nutzen Sie den Kunden-Workspace.",
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


def test_service_maps_each_tool_output_to_its_matching_call_id() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    provider = _CapturingLoopProvider()
    registry = AssistantToolRegistry()
    registry.register(_LookupTool())
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

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="Wie lege ich einen Kunden an?"),
        _context(),
    )

    assert response.answer == "Nutzen Sie den Kunden-Workspace."
    assert len(provider.requests) == 2
    continuation_outputs = provider.requests[1].continuation_tool_outputs
    assert {item["call_id"] for item in continuation_outputs} == {"call-1", "call-2"}
    assert any(item["output"] == '{"summary": "Resolved customer create"}' for item in continuation_outputs)
    assert any("assistant.tool.unknown_provider_tool_name" in item["output"] for item in continuation_outputs)
    assert provider.requests[1].previous_output_items == [
        {
            "type": "function_call",
            "id": "fc-1",
            "call_id": "call-1",
            "name": "assistant_lookup_docs",
            "arguments": '{"query":"customer create"}',
        },
        {
            "type": "function_call",
            "id": "fc-2",
            "call_id": "call-2",
            "name": "assistant_missing_tool",
            "arguments": '{"query":"unknown"}',
        },
    ]
    assert provider.requests[1].metadata["continuation_mode"] == "stateless"
