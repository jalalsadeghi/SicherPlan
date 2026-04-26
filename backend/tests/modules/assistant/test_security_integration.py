from __future__ import annotations

from dataclasses import dataclass

from app.errors import ApiException
from app.modules.assistant.provider import AssistantProviderTimeoutError, MockAssistantProvider
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_conversation_persistence import (
    InMemoryAssistantRepository,
)
from tests.modules.assistant.test_shift_visibility_diagnostic import (
    _DiagnosticRepository,
    _conversation as diagnostic_conversation,
    _service as diagnostic_service,
)


def _internal_context(
    *,
    permission_keys: tuple[str, ...],
    user_id: str = "assistant-user-1",
    tenant_id: str = "tenant-1",
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id=user_id,
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permission_keys),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )


def _portal_context(
    *,
    role_key: str,
    permission_keys: tuple[str, ...],
    user_id: str = "portal-user-1",
    tenant_id: str = "tenant-1",
) -> RequestAuthorizationContext:
    scope_type = "customer" if role_key == "customer_user" else "subcontractor"
    return RequestAuthorizationContext(
        session_id="assistant-session-portal-1",
        user_id=user_id,
        tenant_id=tenant_id,
        role_keys=frozenset({role_key}),
        permission_keys=frozenset(permission_keys),
        scopes=(AuthenticatedRoleScope(role_key=role_key, scope_type=scope_type),),
        request_id="assistant-req-portal-1",
    )


def _basic_service(
    repository: InMemoryAssistantRepository,
    *,
    provider=None,
    tool_registry=None,
) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="mock",
            max_input_chars=400,
            max_tool_calls=8,
            max_context_chunks=4,
        ),
        repository=repository,
        provider=provider or MockAssistantProvider(),
        tool_registry=tool_registry,
    )


@dataclass
class _CountingToolRegistry:
    execute_calls: int = 0
    list_calls: int = 0

    def execute_tool(self, **kwargs):  # noqa: ANN003, ANN201
        self.execute_calls += 1
        raise AssertionError("Out-of-scope requests must not execute tools.")

    def list_available_tools(self, **kwargs):  # noqa: ANN003, ANN201
        self.list_calls += 1
        return [{"function": {"name": "unused.tool", "description": "unused"}}]


class _TimeoutProvider:
    def generate(self, request):  # noqa: ANN001, ANN201
        raise AssistantProviderTimeoutError(
            "timeout while calling provider with Authorization=Bearer secret-jwt sk-test-key"
        )


def test_continue_conversation_after_route_change_updates_route_context_and_history() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    service = _basic_service(repository)
    actor = _internal_context(permission_keys=("assistant.chat.access",))

    first = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="How do I inspect staffing coverage?",
            route_context={
                "path": "/admin/planning-staffing",
                "route_name": "SicherPlanPlanningStaffing",
                "page_id": "P-04",
            },
        ),
        actor,
    )
    second = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="And what should I check next?",
            route_context={
                "path": "/admin/employees",
                "route_name": "SicherPlanEmployees",
                "page_id": "E-01",
            },
        ),
        actor,
    )

    stored = repository.get_conversation_for_user(
        conversation_id=conversation.id,
        tenant_id="tenant-1",
        user_id="assistant-user-1",
    )
    assert first.conversation_id == conversation.id
    assert second.conversation_id == conversation.id
    assert stored is not None
    assert stored.last_route_name == "SicherPlanEmployees"
    assert stored.last_route_path == "/admin/employees"
    assert [item.role for item in stored.messages] == ["user", "assistant", "user", "assistant"]


def test_portal_user_cannot_load_internal_user_conversation() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title="internal",
        locale="de",
        last_route_name="SicherPlanEmployees",
        last_route_path="/admin/employees",
    )
    service = _basic_service(repository)

    try:
        service.get_conversation(
            conversation.id,
            _portal_context(
                role_key="customer_user",
                permission_keys=("assistant.chat.access", "portal.customer.access"),
            ),
        )
    except ApiException as exc:
        assert exc.status_code == 404
        assert exc.code == "assistant.conversation.not_found"
    else:
        raise AssertionError("Expected safe not-found for portal access to an internal conversation.")


def test_missing_permission_message_uses_user_language_for_german_and_persian_diagnostics() -> None:
    repository = _DiagnosticRepository()
    service = diagnostic_service(repository)
    conversation = diagnostic_conversation(repository, locale="de")

    german = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="Ich habe Markus einer Schicht zugewiesen, aber sie ist in der App nicht sichtbar. Woran liegt das?"
        ),
        _internal_context(
            permission_keys=(
                "assistant.chat.access",
                "employees.employee.read",
                "employees.employee.write",
                "planning.shift.read",
                "planning.staffing.read",
            ),
            user_id="dispatcher-1",
        ),
    )
    persian = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="من Markus را به یک شیفت Assign کردم اما در اپ دیده نمی‌شود. مشکل چیست؟"
        ),
        _internal_context(
            permission_keys=(
                "assistant.chat.access",
                "employees.employee.read",
                "employees.employee.write",
                "planning.shift.read",
                "planning.staffing.read",
            ),
            user_id="dispatcher-1",
        ),
    )

    assert german.response_language == "de"
    assert german.answer.startswith("Ich")
    assert any(item.permission == "assistant.diagnostics.read" for item in german.missing_permissions)

    assert persian.response_language == "fa"
    assert persian.answer.startswith("من")
    assert any(item.permission == "assistant.diagnostics.read" for item in persian.missing_permissions)


def test_out_of_scope_question_does_not_list_or_execute_tools() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )
    tool_registry = _CountingToolRegistry()
    service = _basic_service(repository, tool_registry=tool_registry)

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="What is the best medical treatment for migraines?"),
        _internal_context(permission_keys=("assistant.chat.access",)),
    )

    assert response.out_of_scope is True
    assert tool_registry.list_calls == 0
    assert tool_registry.execute_calls == 0


def test_provider_timeout_returns_safe_api_exception_without_secret_leakage() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )
    service = _basic_service(repository, provider=_TimeoutProvider())

    try:
        service.add_message(
            conversation.id,
            AssistantMessageCreate(message="How do I reset employee access in SicherPlan?"),
            _internal_context(permission_keys=("assistant.chat.access",)),
        )
    except ApiException as exc:
        assert exc.status_code == 504
        assert exc.code == "assistant.provider.timeout"
        assert exc.message_key == "errors.assistant.provider.timeout"
        assert exc.details == {}
        rendered = f"{exc.code} {exc.message_key} {exc.details}"
        assert "secret-jwt" not in rendered
        assert "sk-test-key" not in rendered
        assert "Authorization" not in rendered
    else:
        raise AssertionError("Expected provider timeout to become a safe ApiException.")
