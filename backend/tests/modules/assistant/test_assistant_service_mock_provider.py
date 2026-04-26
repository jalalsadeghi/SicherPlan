from __future__ import annotations

from dataclasses import dataclass, field

from app.errors import ApiException
from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from app.modules.assistant.knowledge.types import KnowledgeChunkCandidate
from app.modules.assistant.provider import (
    AssistantProviderRequest,
    AssistantProviderResult,
    AssistantProviderConfigurationError,
    MockAssistantProvider,
    mock_provider_answer,
)
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


@dataclass
class _KnowledgeRepository:
    candidates: list[KnowledgeChunkCandidate] = field(default_factory=list)

    def list_active_chunk_candidates(
        self,
        *,
        source_type: str | None = None,
        candidate_limit: int = 200,
    ) -> list[KnowledgeChunkCandidate]:
        filtered = [
            item
            for item in self.candidates
            if source_type is None or item.source_type == source_type
        ]
        return filtered[:candidate_limit]


class _CapturingProvider:
    def __init__(self) -> None:
        self.requests: list[AssistantProviderRequest] = []

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": mock_provider_answer(request.response_language),
                "confidence": "low",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text=mock_provider_answer(request.response_language),
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


def _service(repository: InMemoryAssistantRepository, provider) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="mock",
            max_input_chars=400,
            max_tool_calls=8,
            max_context_chunks=4,
        ),
        repository=repository,
        provider=provider,
    )


def test_service_uses_mock_provider_for_in_scope_question() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )
    provider = MockAssistantProvider()
    response = _service(repository, provider).add_message(
        conversation.id,
        AssistantMessageCreate(message="How do I reset employee access in SicherPlan?"),
        _context(),
    )

    assert response.out_of_scope is False
    assert response.answer == mock_provider_answer(response.response_language)
    assert provider.call_count == 1


def test_service_does_not_call_provider_for_out_of_scope_question() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )
    provider = MockAssistantProvider()
    response = _service(repository, provider).add_message(
        conversation.id,
        AssistantMessageCreate(message="What is the weather in Hamburg?"),
        _context(),
    )

    assert response.out_of_scope is True
    assert provider.call_count == 0


def test_service_maps_provider_error_to_safe_api_exception() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )
    provider = MockAssistantProvider(
        raise_error=AssistantProviderConfigurationError(
            "SP_AI_PROVIDER=openai is reserved for AI-11 and is not implemented in this task."
        )
    )
    try:
        _service(repository, provider).add_message(
            conversation.id,
            AssistantMessageCreate(message="How do I reset employee access in SicherPlan?"),
            _context(),
        )
    except ApiException as exc:
        assert exc.status_code == 503
        assert exc.code == "assistant.provider.unavailable"
    else:
        raise AssertionError("Expected ApiException")


def test_service_includes_retrieved_knowledge_chunks_in_provider_request() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )
    provider = _CapturingProvider()
    knowledge_retriever = AssistantKnowledgeRetriever(
        repository=_KnowledgeRepository(
            [
                KnowledgeChunkCandidate(
                    chunk_id="chunk-1",
                    source_id="source-1",
                    source_name="Planning Manual",
                    source_type="repository_docs",
                    source_path="/docs/planning.md",
                    chunk_index=0,
                    title="Employee app visibility",
                    content="If Markus is not visible in the employee app, check the linked employee access and release state.",
                    language_code="en",
                    module_key="employees",
                    page_id="E-01",
                    role_keys=[],
                    permission_keys=[],
                    token_count=12,
                )
            ]
        ),
        max_context_chunks=4,
        max_input_chars=400,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="mock",
            max_input_chars=400,
            max_tool_calls=8,
            max_context_chunks=4,
        ),
        repository=repository,
        provider=provider,
        knowledge_retriever=knowledge_retriever,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="How do I reset employee access in SicherPlan?",
            route_context={"page_id": "E-01"},
        ),
        _context(),
    )

    assert response.out_of_scope is False
    assert len(provider.requests) == 1
    assert provider.requests[0].knowledge_chunks[0]["chunk_id"] == "chunk-1"
    assert provider.requests[0].knowledge_chunks[0]["page_id"] == "E-01"
    assert provider.requests[0].grounding_context is not None
    assert any(
        source["source_type"] == "knowledge_chunk" and source["page_id"] == "E-01"
        for source in provider.requests[0].grounding_context["sources"]
    )
