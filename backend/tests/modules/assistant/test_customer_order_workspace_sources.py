from __future__ import annotations

from app.modules.assistant.page_catalog_seed import ASSISTANT_PAGE_ROUTE_SEEDS
from app.modules.assistant.schemas import AssistantWorkflowHelpInput
from app.modules.assistant.tools.base import AssistantToolExecutionContext
from app.modules.assistant.tools.workflow_help_tools import SearchWorkflowHelpTool
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_page_help_manifest import _context, _repository, _service


def _tool_context() -> AssistantToolExecutionContext:
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


def test_customer_order_workspace_route_seed_matches_frontend_route() -> None:
    by_page_id = {seed.page_id: seed for seed in ASSISTANT_PAGE_ROUTE_SEEDS}
    workspace = by_page_id["C-02"]

    assert workspace.route_name == "SicherPlanCustomerOrderWorkspace"
    assert workspace.path_template == "/admin/customers/order-workspace"
    assert workspace.api_families == ("customers", "planningOrders", "planningShifts", "platformDocuments")


def test_customer_order_workspace_page_help_and_workflow_source_basis_are_present() -> None:
    service = _service(_repository())
    manifest = service.get_page_help_manifest(
        page_id="C-02",
        language_code="en",
        actor=_context("assistant.chat.access", "planning.order.read", "planning.order.write", "planning.shift.write", "planning.staffing.read"),
    )

    assert manifest.page_id == "C-02"
    assert "customer_scoped_order_create" in manifest.workflow_keys
    assert manifest.source_basis
    assert any(action.action_key == "customer.order_workspace.generate_continue" for action in manifest.actions)
    assert any(step.page_id == "P-04" for step in manifest.post_create_steps)

    tool = SearchWorkflowHelpTool()
    result = tool.execute(
        input_data=AssistantWorkflowHelpInput(workflow_key="customer_scoped_order_create", language_code="en"),
        context=_tool_context(),
    )
    workflow = result.data["workflows"][0]

    assert workflow["route_path"] == "/admin/customers/order-workspace"
    assert "/admin/customers/new-plan" in workflow["route_aliases"]
    assert workflow["entry_points"][2] == "Orders tab"
    assert all(step["source_basis"] for step in workflow["steps"])
