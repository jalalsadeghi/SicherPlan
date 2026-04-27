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


def test_contract_workflow_carries_ambiguity_and_verified_context_pages() -> None:
    result = SearchWorkflowHelpTool().execute(
        input_data=AssistantWorkflowHelpInput(
            workflow_key="contract_or_document_register",
            language_code="de",
        ),
        context=_context(),
    )

    workflow = result.data["workflows"][0]
    assert workflow["workflow_key"] == "contract_or_document_register"
    assert workflow["ambiguity_notes"]
    assert {"PS-01", "C-01", "P-02", "S-01"} == set(workflow["linked_page_ids"])
    assert all(page_id != "CON-01" for page_id in workflow["linked_page_ids"])
    assert any("ask" in note.casefold() or "klären" in note.casefold() for note in workflow["ambiguity_notes"])
