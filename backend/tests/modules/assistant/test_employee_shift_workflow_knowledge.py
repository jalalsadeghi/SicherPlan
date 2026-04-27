from __future__ import annotations

from app.modules.assistant.schemas import AssistantWorkflowHelpInput
from app.modules.assistant.tools.base import AssistantToolExecutionContext
from app.modules.assistant.tools.workflow_help_tools import SearchWorkflowHelpTool
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


def test_employee_assignment_workflow_contains_expected_pages_and_steps() -> None:
    result = SearchWorkflowHelpTool().execute(
        input_data=AssistantWorkflowHelpInput(
            query="How do I assign an employee to a shift?",
            language_code="en",
        ),
        context=_context(),
    )

    workflow = result.data["workflows"][0]
    assert workflow["workflow_key"] == "employee_assign_to_shift"
    assert {"E-01", "P-03", "P-04", "P-05"} == set(workflow["linked_page_ids"])
    assert [step["page_id"] for step in workflow["steps"]] == ["E-01", "P-03", "P-04", "P-05"]
    assert all(step["source_basis"] for step in workflow["steps"])


def test_shift_release_workflow_matches_german_employee_app_question() -> None:
    result = SearchWorkflowHelpTool().execute(
        input_data=AssistantWorkflowHelpInput(
            query="Wie gebe ich eine Schicht für die Mitarbeiter-App frei?",
            language_code="de",
        ),
        context=_context(),
    )

    workflow = result.data["workflows"][0]
    assert workflow["workflow_key"] == "shift_release_to_employee_app"
    assert {"P-03", "P-04", "P-05", "ES-01"} == set(workflow["linked_page_ids"])
