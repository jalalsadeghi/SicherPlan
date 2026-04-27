from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _repository as page_help_repository
from tests.modules.assistant.test_shift_visibility_diagnostic import _DiagnosticRepository
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


@dataclass
class _ToolLoopProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)
    call_count: int = 0

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        self.call_count += 1
        if self.call_count == 1:
            return AssistantProviderResult(
                final_response={
                    "answer": "",
                    "confidence": "medium",
                    "out_of_scope": False,
                    "diagnosis": [],
                    "links": [],
                    "missing_permissions": [],
                    "next_steps": [],
                    "tool_trace_id": None,
                },
                raw_text="",
                requested_tool_calls=[
                    {
                        "id": "tool-1",
                        "name": "assistant.search_workflow_help",
                        "arguments": '{"workflow_key":"customer_order_create","language_code":"en"}',
                        "call_id": "call-1",
                    }
                ],
                provider_name="openai",
                provider_mode="openai",
                model_name="gpt-test",
            )
        assert any(item["tool_name"] == "assistant.search_workflow_help" for item in request.tool_results)
        return AssistantProviderResult(
            final_response={
                "answer": "Use Orders & Planning Records first, then continue into Shift Planning and Staffing Board.",
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": "assistant.search_workflow_help",
            },
            raw_text="Use Orders & Planning Records first, then continue into Shift Planning and Staffing Board.",
            provider_name="openai",
            provider_mode="openai",
            model_name="gpt-test",
        )


class _CapturingProvider:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.requests: list[AssistantProviderRequest] = []
        self.call_count = 0

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        self.call_count += 1
        return AssistantProviderResult(
            final_response={
                "answer": self.answer,
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text=self.answer,
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
        )


def _context(*permissions: str, role_key: str = "tenant_admin") -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({role_key}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key=role_key, scope_type="tenant"),),
        request_id="assistant-req-1",
    )


def test_persian_employee_assign_to_shift_not_routed_as_employee_create() -> None:
    repository = page_help_repository()
    provider = _CapturingProvider("راهنمای تخصیص کارمند به شیفت")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="fa",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
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
        AssistantMessageCreate(message="برای اینکه یک کارمند جدید بتونم در یک شیفت Assgin بدم چکار باید بکنم؟"),
        _context("assistant.chat.access", "employees.employee.read", "planning.order.read", "planning.record.read", "planning.shift.read", "planning.staffing.read"),
    )

    assert response.out_of_scope is False
    assert response.answer == "راهنمای تخصیص کارمند به شیفت"
    assert provider.call_count == 1
    tool_names = [item["tool_name"] for item in provider.requests[0].tool_results]
    assert "assistant.search_workflow_help" in tool_names
    assert "assistant.find_ui_action" not in tool_names
    assert provider.requests[0].grounding_context is not None
    assert provider.requests[0].grounding_context["retrieval_plan"]["workflow_intent"] == "employee_assign_to_shift"
    assert {"E-01", "P-03", "P-04"}.issubset(
        set(provider.requests[0].grounding_context["retrieval_plan"]["likely_page_ids"])
    )


def test_persian_order_create_is_in_scope() -> None:
    repository = page_help_repository()
    provider = _CapturingProvider("راهنمای ساخت سفارش جدید")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="fa",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
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
        AssistantMessageCreate(message="الان میخوام یک order جدید درست کنم، دقیقا باید چکار کنم؟"),
        _context("assistant.chat.access", "planning.order.read", "planning.record.read"),
    )

    assert response.out_of_scope is False
    assert response.answer == "راهنمای ساخت سفارش جدید"
    assert provider.call_count == 1
    assert any(item["tool_name"] == "assistant.search_workflow_help" for item in provider.requests[0].tool_results)
    assert provider.requests[0].grounding_context is not None
    assert "P-02" in provider.requests[0].grounding_context["retrieval_plan"]["likely_page_ids"]


def test_shift_visibility_diagnostic_facts_go_to_provider() -> None:
    repository = _DiagnosticRepository()
    provider = _CapturingProvider("I checked the grounded visibility facts.")
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
        ),
        repository=repository,
        provider=provider,
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            employee_repository=repository,
            planning_repository=repository,
        ),
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="Why is Markus not visible in the employee app?"),
        _context(
            "assistant.chat.access",
            "assistant.diagnostics.read",
            "employees.employee.read",
            "employees.employee.write",
            "employees.private.read",
            "planning.shift.read",
            "planning.staffing.read",
        ),
    )

    assert response.out_of_scope is False
    assert response.answer == "I checked the grounded visibility facts."
    assert provider.call_count == 1
    diagnostic_summary = next(item for item in provider.requests[0].tool_results if item["tool_name"] == "assistant.diagnose_employee_shift_visibility")
    assert diagnostic_summary["summary"]["data"]["diagnostic_key"] == "employee_shift_visibility"
    assert "summary" in diagnostic_summary["summary"]["data"]
    assert provider.requests[0].grounding_context is not None
    assert any(
        source["source_type"] == "diagnostic"
        for source in provider.requests[0].grounding_context["sources"]
    )


def test_persian_customer_plan_create_uses_provider_with_customer_and_planning_candidates() -> None:
    repository = page_help_repository()
    provider = _CapturingProvider("پاسخ مدل برای ثبت پلن مشتری")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="fa",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
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
        AssistantMessageCreate(message="چطور میتونم یک پلن جدید برای مشتری ثبت کنم؟"),
        _context("assistant.chat.access", "customers.customer.read", "planning.order.read", "planning.record.read", "planning.shift.read"),
    )

    assert response.out_of_scope is False
    assert response.answer == "پاسخ مدل برای ثبت پلن مشتری"
    assert provider.call_count == 1
    assert response.answer != "[MOCK RAG]"
    assert provider.requests[0].grounding_context is not None
    assert {"C-01", "P-02"}.issubset(set(provider.requests[0].grounding_context["retrieval_plan"]["likely_page_ids"]))
    assert "P-03" in provider.requests[0].grounding_context["retrieval_plan"]["likely_page_ids"]
    assert any(item["tool_name"] == "assistant.search_workflow_help" for item in provider.requests[0].tool_results)


def test_persian_customer_create_uses_provider_with_customer_workspace_candidate() -> None:
    repository = page_help_repository()
    provider = _CapturingProvider("پاسخ مدل برای ثبت مشتری")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="fa",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
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
        AssistantMessageCreate(message="چطور باید مشتری ثبت کنم؟"),
        _context("assistant.chat.access", "customers.customer.read"),
    )

    assert response.out_of_scope is False
    assert response.answer == "پاسخ مدل برای ثبت مشتری"
    assert provider.call_count == 1
    assert provider.requests[0].grounding_context is not None
    assert provider.requests[0].grounding_context["retrieval_plan"]["workflow_intent"] == "customer_create"
    assert "C-01" in provider.requests[0].grounding_context["retrieval_plan"]["likely_page_ids"]
    assert any(item["tool_name"] == "assistant.search_workflow_help" for item in provider.requests[0].tool_results)


def test_contract_registration_stays_in_scope_and_can_ask_for_clarification() -> None:
    repository = page_help_repository()
    provider = _CapturingProvider("I need to know whether this is a customer, employee, subcontractor, or platform contract before I can give exact steps.")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="fa",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
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
        AssistantMessageCreate(message="چطوری یک قرارداد جدید ثبت کنم؟"),
        _context("assistant.chat.access"),
    )

    assert response.out_of_scope is False
    assert response.answer.startswith("I need to know whether this is")
    assert provider.call_count == 1
    assert response.answer != "[MOCK RAG]"
    assert provider.requests[0].grounding_context is not None
    assert "PS-01" in provider.requests[0].grounding_context["retrieval_plan"]["likely_page_ids"]
    assert any(item["tool_name"] == "assistant.search_workflow_help" for item in provider.requests[0].tool_results)


def test_german_order_create_uses_provider_with_order_candidates() -> None:
    repository = page_help_repository()
    provider = _CapturingProvider("Beginnen Sie in Auftraege & Planungsdatensaetze.")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
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
        AssistantMessageCreate(message="Wie kann ich einen neuen Auftrag erstellen?"),
        _context("assistant.chat.access", "planning.order.read", "planning.record.read"),
    )

    assert response.out_of_scope is False
    assert response.answer.startswith("Beginnen Sie")
    assert provider.call_count == 1
    assert provider.requests[0].grounding_context is not None
    assert "P-02" in provider.requests[0].grounding_context["retrieval_plan"]["likely_page_ids"]
    assert any(item["tool_name"] == "assistant.search_workflow_help" for item in provider.requests[0].tool_results)


def test_provider_links_are_revalidated_and_invented_path_is_removed() -> None:
    repository = page_help_repository()
    provider = _CapturingProvider("Open the staffing workspace.")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )

    def generate_with_invented_link(request: AssistantProviderRequest) -> AssistantProviderResult:
        provider.requests.append(request)
        provider.call_count += 1
        return AssistantProviderResult(
            final_response={
                "answer": provider.answer,
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [
                    {
                        "label": "Invented staffing link",
                        "path": "/totally-invented",
                        "route_name": "FakeRoute",
                        "page_id": "P-04",
                    },
                    {
                        "label": "Bad link without page id",
                        "path": "/not-allowed",
                    },
                ],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text=provider.answer,
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
        )

    provider.generate = generate_with_invented_link  # type: ignore[method-assign]
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
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
        AssistantMessageCreate(message="How can I assign a new employee to a shift?"),
        _context("assistant.chat.access", "employees.employee.read", "planning.order.read", "planning.record.read", "planning.shift.read", "planning.staffing.read"),
    )

    assert response.out_of_scope is False
    assert len(response.links) == 1
    assert response.links[0].page_id == "P-04"
    assert response.links[0].path == "/admin/planning-staffing"


def test_openai_tool_call_loop_executes_registered_tools_only() -> None:
    repository = page_help_repository()
    provider = _ToolLoopProvider()
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
            max_tool_calls=4,
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
        AssistantMessageCreate(message="I want to create a new order. how can I do?"),
        _context("assistant.chat.access", "planning.order.read", "planning.record.read"),
    )

    assert response.out_of_scope is False
    assert response.answer.startswith("Use Orders & Planning Records first")
    assert provider.call_count == 2
    assert any(item["tool_name"] == "assistant.search_workflow_help" for item in provider.requests[1].tool_results)
    assert provider.requests[0].grounding_context is not None
