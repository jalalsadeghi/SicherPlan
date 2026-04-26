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
class _LoopingProvider:
    requests: list[AssistantProviderRequest]

    def __init__(self) -> None:
        self.requests = []

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        if len(self.requests) == 1:
            return AssistantProviderResult(
                final_response={},
                raw_text=None,
                requested_tool_calls=[
                    {
                        "id": "fc-1",
                        "name": "assistant.lookup_docs",
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
                "answer": "Open the customer workspace first.",
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text="Open the customer workspace first.",
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


def test_service_feeds_function_call_output_back_into_provider_loop() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )
    provider = _LoopingProvider()
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
        AssistantMessageCreate(message="How do I create a customer?"),
        _context(),
    )

    assert response.answer == "Open the customer workspace first."
    assert len(provider.requests) == 2
    assert provider.requests[0].tool_results == []
    assert provider.requests[1].tool_results == [
        {
            "type": "function_call_output",
            "call_id": "call-1",
            "output": '{"summary": "Resolved customer create"}',
        }
    ]
