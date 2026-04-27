from __future__ import annotations

from app.modules.assistant.provider import AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


class _CapturingProvider:
    def __init__(self) -> None:
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": "Generic but grounded-safe answer.",
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text="Generic but grounded-safe answer.",
            provider_mode="openai",
            model_name="gpt-test",
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


def test_how_to_confidence_is_reduced_when_only_shallow_sources_exist() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    provider = _CapturingProvider()
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-test",
        ),
        repository=repository,
        provider=provider,
        tool_registry=None,
        knowledge_retriever=None,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="Wie registriere ich einen neuen Vertrag?"),
        _context(),
    )

    assert response.confidence.value == "low"
    assert response.rag_trace is not None
    assert response.rag_trace.content_bearing_source_count == 0
    assert "content_bearing_sources" in response.rag_trace.missing_context
    assert response.source_basis == []
    assert provider.requests[0].grounding_context is not None
