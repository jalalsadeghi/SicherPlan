from __future__ import annotations

from tests.modules.assistant.test_page_help_manifest import _context, _repository, _service


def test_core_workspace_page_help_contains_richer_metadata() -> None:
    service = _service(_repository())

    customers = service.get_page_help_manifest(
        page_id="C-01",
        language_code="en",
        actor=_context("assistant.chat.access", "customers.customer.read", "customers.customer.write"),
    )
    assert customers.page_purpose
    assert customers.workflow_keys == ["customer_create", "customer_order_create", "customer_plan_create"]
    assert customers.api_families == ["customers"]
    assert customers.source_basis
    assert any(action.label_status == "verified" for action in customers.actions)

    planning_orders = service.get_page_help_manifest(
        page_id="P-02",
        language_code="en",
        actor=_context("assistant.chat.access", "planning.order.read", "planning.record.read", "planning.order.write", "planning.record.write"),
    )
    assert planning_orders.page_purpose
    assert "customer_order_create" in planning_orders.workflow_keys
    assert "planning" in planning_orders.api_families
    assert planning_orders.source_basis
    assert any(action.label_status == "unverified" for action in planning_orders.actions)

    shift_planning = service.get_page_help_manifest(
        page_id="P-03",
        language_code="en",
        actor=_context("assistant.chat.access", "planning.shift.read", "planning.shift.write"),
    )
    assert shift_planning.page_purpose
    assert "shift_release_to_employee_app" in shift_planning.workflow_keys
    assert any(action.action_key == "planning.shift.release" for action in shift_planning.actions)

    staffing = service.get_page_help_manifest(
        page_id="P-04",
        language_code="de",
        actor=_context("assistant.chat.access", "planning.staffing.read", "planning.staffing.write"),
    )
    assert staffing.page_purpose
    assert any(action.action_key == "planning.staffing.assign" for action in staffing.actions)
    assert any(action.test_id == "planning-staffing-assign-action" for action in staffing.actions)

    dispatch = service.get_page_help_manifest(
        page_id="P-05",
        language_code="en",
        actor=_context("assistant.chat.access", "planning.staffing.read", "planning.staffing.write"),
    )
    assert dispatch.page_purpose
    assert any(action.action_key == "planning.dispatch.preview" for action in dispatch.actions)
    assert any(action.label == "Generate internal deployment plan" for action in dispatch.actions)

    platform_services = service.get_page_help_manifest(
        page_id="PS-01",
        language_code="en",
        actor=_context("assistant.chat.access", "platform_services.document.write"),
    )
    assert platform_services.page_purpose
    assert platform_services.workflow_keys == ["contract_or_document_register"]
    assert platform_services.source_basis
    assert any(action.label_status == "unverified" for action in platform_services.actions)
