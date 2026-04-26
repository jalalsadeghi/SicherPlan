from __future__ import annotations

from types import SimpleNamespace

from app.modules.assistant.openai_client import OpenAIProviderRuntime, OpenAIResponsesProvider
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


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


def test_openai_provider_is_called_for_in_scope_message() -> None:
    response = SimpleNamespace(
        output_parsed={
            "answer": "Use Orders & Planning Records first.",
            "confidence": "high",
            "out_of_scope": False,
            "diagnosis": [],
            "links": [],
            "missing_permissions": [],
            "next_steps": [],
            "tool_trace_id": None,
        },
        output=[],
        usage=SimpleNamespace(input_tokens=123, output_tokens=45),
        output_text="Use Orders & Planning Records first.",
        status="completed",
    )

    class _Responses:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def parse(self, **kwargs):
            self.calls.append(kwargs)
            return response

    class _Client:
        def __init__(self) -> None:
            self.responses = _Responses()

    client = _Client()
    provider = OpenAIResponsesProvider(
        OpenAIProviderRuntime(
            api_key="test-key",
            model_name="gpt-5.5-mini",
            timeout_seconds=45,
            store_responses=False,
            max_input_chars=12000,
        ),
        client_factory=lambda **kwargs: client,
    )
    repository = InMemoryAssistantRepository()
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
            env="development",
            openai_configured=True,
            mock_provider_allowed=False,
            response_model="gpt-5.5-mini",
            store_responses=False,
        ),
        repository=repository,
        provider=provider,
    )

    result = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="I want to create a new order. how can I do?"),
        _context(),
    )

    assert result.answer == "Use Orders & Planning Records first."
    assert len(client.responses.calls) == 1
    call = client.responses.calls[0]
    assert call["model"] == "gpt-5.5-mini"
    assert call["store"] is False
    assert any("Grounding context package" in item["content"] for item in call["input"])
