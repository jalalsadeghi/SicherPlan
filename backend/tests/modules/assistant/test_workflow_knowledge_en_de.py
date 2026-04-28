from __future__ import annotations

from app.modules.assistant.schemas import AssistantWorkflowHelpInput
from app.modules.assistant.tools.base import AssistantToolExecutionContext
from app.modules.assistant.tools.workflow_help_tools import SearchWorkflowHelpTool
from app.modules.assistant.workflow_help import detect_workflow_intent
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


def _context() -> AssistantToolExecutionContext:
    auth_context = RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"assistant.chat.access"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )
    return AssistantToolExecutionContext(
        auth_context=auth_context,
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"assistant.chat.access"}),
        scope_kind="tenant",
        request_id="assistant-req-1",
    )


def test_german_and_english_workflow_queries_resolve_to_verified_workflows() -> None:
    tool = SearchWorkflowHelpTool()

    english_result = tool.execute(
        input_data=AssistantWorkflowHelpInput(query="How do I create a new customer?", language_code="en"),
        context=_context(),
    )
    english_workflow = english_result.data["workflows"][0]
    assert detect_workflow_intent("How do I create a new customer?").intent == "customer_create"
    assert english_workflow["workflow_key"] == "customer_create"
    assert english_workflow["title"] == english_workflow["title_en"]
    assert english_workflow["linked_page_ids"] == ["C-01"]

    german_result = tool.execute(
        input_data=AssistantWorkflowHelpInput(
            query="Wie erstelle ich einen neuen Auftrag für einen Kunden?",
            language_code="de",
        ),
        context=_context(),
    )
    german_workflow = german_result.data["workflows"][0]
    assert german_workflow["workflow_key"] == "customer_order_create"
    assert german_workflow["title"] == german_workflow["title_de"]
    assert {"C-01", "P-02"}.issubset(set(german_workflow["linked_page_ids"]))

    customer_scoped_result = tool.execute(
        input_data=AssistantWorkflowHelpInput(
            query="Wie erstelle ich einen Auftrag direkt beim Kunden?",
            language_code="de",
        ),
        context=_context(),
    )
    customer_scoped_workflow = customer_scoped_result.data["workflows"][0]
    assert customer_scoped_workflow["workflow_key"] == "customer_scoped_order_create"
    assert {"C-01", "C-02", "P-04"}.issubset(set(customer_scoped_workflow["linked_page_ids"]))


def test_contract_query_matches_contract_workflow_in_german_and_english() -> None:
    tool = SearchWorkflowHelpTool()

    german_result = tool.execute(
        input_data=AssistantWorkflowHelpInput(
            query="Wie registriere ich einen neuen Vertrag?",
            language_code="de",
        ),
        context=_context(),
    )
    english_result = tool.execute(
        input_data=AssistantWorkflowHelpInput(
            query="How do I register a new contract?",
            language_code="en",
        ),
        context=_context(),
    )

    assert german_result.data["workflows"][0]["workflow_key"] == "contract_or_document_register"
    assert english_result.data["workflows"][0]["workflow_key"] == "contract_or_document_register"
