from __future__ import annotations

from dataclasses import dataclass

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _repository as page_help_repository


@dataclass
class _CapturingProvider:
    requests: list[AssistantProviderRequest]

    def __init__(self) -> None:
        self.requests = []

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": "Use the grounded workflow package.",
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text="Use the grounded workflow package.",
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
        )


def _context(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )


def test_grounding_package_is_compact_scored_and_explained() -> None:
    repository = page_help_repository()
    provider = _CapturingProvider()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
            max_grounding_sources=10,
            max_grounding_chars_per_source=1200,
            max_total_grounding_chars=9000,
        ),
        repository=repository,
        provider=provider,
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            page_help_repository=repository,
        ),
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="How do I create a new customer?"),
        _context("assistant.chat.access", "customers.customer.read"),
    )

    assert response.out_of_scope is False
    grounding = provider.requests[0].grounding_context
    assert grounding is not None
    assert grounding["query_expansion"]["detected_terms"]
    assert len(grounding["sources"]) <= 10
    total_chars = 0
    for source in grounding["sources"]:
        assert source["score"] is not None
        assert source["why_selected"]
        assert source["content"] or source["facts"]
        if source["content"]:
            assert len(source["content"]) <= 1200
            total_chars += len(source["content"])
        total_chars += len(str(source["facts"]))
    assert total_chars <= 9000
    assert any(source["content_bearing"] for source in grounding["sources"])
