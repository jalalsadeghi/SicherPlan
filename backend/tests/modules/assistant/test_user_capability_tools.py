from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.modules.assistant.models import AssistantPageRouteCatalog
from app.modules.assistant.page_catalog_seed import ASSISTANT_PAGE_ROUTE_SEEDS
from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from app.modules.assistant.models import AssistantConversation, AssistantMessage
from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


@dataclass
class _InMemoryAssistantRepository:
    conversations: dict[str, AssistantConversation] = field(default_factory=dict)
    messages: dict[str, list[AssistantMessage]] = field(default_factory=dict)
    audits: list[object] = field(default_factory=list)
    page_routes: list[AssistantPageRouteCatalog] = field(default_factory=list)
    counter: int = 0

    def create_conversation(
        self,
        *,
        tenant_id: str | None,
        user_id: str,
        title: str | None,
        locale: str | None,
        last_route_name: str | None,
        last_route_path: str | None,
    ) -> AssistantConversation:
        now = self._next_time()
        conversation = AssistantConversation(
            id=str(uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            locale=locale,
            status="active",
            last_route_name=last_route_name,
            last_route_path=last_route_path,
            created_at=now,
            updated_at=now,
            archived_at=None,
        )
        self.conversations[conversation.id] = conversation
        self.messages[conversation.id] = []
        return conversation

    def get_conversation_for_user(self, *, conversation_id: str, tenant_id: str | None, user_id: str) -> AssistantConversation | None:
        conversation = self.conversations.get(conversation_id)
        if conversation is None or conversation.user_id != user_id or conversation.tenant_id != tenant_id:
            return None
        return conversation

    def list_messages_for_conversation(self, conversation_id: str) -> list[AssistantMessage]:
        return self.messages.get(conversation_id, [])

    def update_conversation_route_context(self, conversation: AssistantConversation, *, last_route_name: str | None, last_route_path: str | None) -> None:
        conversation.last_route_name = last_route_name
        conversation.last_route_path = last_route_path

    def create_messages(self, conversation: AssistantConversation, messages: list[AssistantMessage]) -> list[AssistantMessage]:
        self.messages.setdefault(conversation.id, []).extend(messages)
        return messages

    def update_message_payload(self, message: AssistantMessage, *, structured_payload: dict[str, object]) -> None:
        message.structured_payload = structured_payload

    def create_tool_call_audit(self, *, record) -> object:  # noqa: ANN001, ANN201
        self.audits.append(record)
        return record

    def list_active_page_routes(self) -> list[AssistantPageRouteCatalog]:
        return [row for row in self.page_routes if row.active]

    def get_page_route_by_page_id(self, *, page_id: str) -> AssistantPageRouteCatalog | None:
        for row in self.page_routes:
            if row.page_id == page_id:
                return row
        return None

    def _next_time(self) -> datetime:
        base = datetime(2026, 4, 26, 12, 0, 0, tzinfo=UTC)
        next_value = base + timedelta(seconds=self.counter)
        self.counter += 1
        return next_value


def _context(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(
            AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),
            AuthenticatedRoleScope(role_key="tenant_admin", scope_type="branch", branch_id="branch-1"),
        ),
        request_id="assistant-req-1",
    )


def _service(repository: _InMemoryAssistantRepository, *, enabled: bool = True) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=enabled,
            provider_mode="mock",
            max_input_chars=400,
            max_context_chunks=4,
        ),
        repository=repository,
        provider=MockAssistantProvider(),
        knowledge_retriever=None,
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
        ),
    )


def _repository() -> _InMemoryAssistantRepository:
    repository = _InMemoryAssistantRepository()
    repository.page_routes = [
        AssistantPageRouteCatalog(
            id=str(uuid4()),
            page_id=seed.page_id,
            label=seed.label,
            route_name=seed.route_name,
            path_template=seed.path_template,
            module_key=seed.module_key,
            api_families=list(seed.api_families) or None,
            required_permissions=list(seed.required_permissions) or None,
            allowed_role_keys=list(seed.allowed_role_keys) or None,
            scope_kind=seed.scope_kind,
            supports_entity_deep_link=seed.supports_entity_deep_link,
            entity_param_map=seed.entity_param_map,
            active=seed.active,
        )
        for seed in ASSISTANT_PAGE_ROUTE_SEEDS
    ]
    return repository


def test_current_user_capabilities_are_returned_for_authorized_user() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="assistant.get_current_user_capabilities",
        input_data={},
        actor=_context("assistant.chat.access", "assistant.diagnostics.read", "assistant.knowledge.read"),
    )

    assert result.ok is True
    assert result.data["user_id"] == "assistant-user-1"
    assert result.data["tenant_id"] == "tenant-1"
    assert result.data["scope_kind"] == "branch"
    assert result.data["assistant_capabilities"]["can_chat"] is True
    assert result.data["assistant_capabilities"]["can_run_diagnostics"] is True
    assert result.data["assistant_capabilities"]["can_use_knowledge"] is True
    assert result.data["scope_summary"]["branch_ids"] == ["branch-1"]
    assert repository.audits[0].tool_name == "assistant.get_current_user_capabilities"


def test_disabled_assistant_blocks_tool_execution() -> None:
    repository = _repository()
    try:
        _service(repository, enabled=False).execute_registered_tool(
            tool_name="assistant.get_current_user_capabilities",
            input_data={},
            actor=_context("assistant.chat.access"),
        )
    except Exception as exc:
        assert getattr(exc, "code", None) == "assistant.disabled"
    else:
        raise AssertionError("Expected assistant.disabled ApiException")


def test_missing_assistant_chat_access_blocks_tool_execution() -> None:
    repository = _repository()
    try:
        _service(repository).execute_registered_tool(
            tool_name="assistant.get_current_user_capabilities",
            input_data={},
            actor=_context(),
        )
    except Exception as exc:
        assert getattr(exc, "code", None) == "iam.authorization.permission_denied"
    else:
        raise AssertionError("Expected permission-denied ApiException")


def test_user_supplied_tenant_role_and_permission_data_is_ignored() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="assistant.get_current_user_capabilities",
        input_data={
            "tenant_id": "forged-tenant",
            "role_keys": ["platform_admin"],
            "permission_keys": ["assistant.admin"],
        },
        actor=_context("assistant.chat.access"),
    )

    assert result.ok is True
    assert result.data["tenant_id"] == "tenant-1"
    assert result.data["role_keys"] == ["tenant_admin"]
    assert "assistant.admin" not in result.data["permission_keys"]


def test_service_lists_only_currently_allowed_default_tools() -> None:
    repository = _repository()
    tools = _service(repository).list_available_tools(actor=_context("assistant.chat.access"))

    assert [tool["function"]["name"] for tool in tools] == [
        "assistant.get_current_page_context",
        "assistant.get_current_user_capabilities",
        "assistant.search_accessible_pages",
        "assistant.search_workflow_help",
        "navigation.build_allowed_link",
    ]


def test_no_openai_api_key_is_required_for_capability_tools() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="assistant.get_current_user_capabilities",
        input_data={},
        actor=_context("assistant.chat.access"),
    )

    assert result.ok is True
