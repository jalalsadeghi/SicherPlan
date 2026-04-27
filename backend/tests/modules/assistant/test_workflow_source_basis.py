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


def test_workflow_steps_include_source_basis_and_no_answer_text() -> None:
    result = SearchWorkflowHelpTool().execute(
        input_data=AssistantWorkflowHelpInput(workflow_key="customer_order_create", language_code="en"),
        context=_context(),
    )

    assert "answer" not in result.data
    workflow = result.data["workflows"][0]
    assert workflow["workflow_key"] == "customer_order_create"
    assert workflow["source_basis"]
    for step in workflow["steps"]:
        assert step["source_basis"]
        for basis in step["source_basis"]:
            assert basis["source_type"]
            assert basis["source_name"]
            assert basis["evidence"]
