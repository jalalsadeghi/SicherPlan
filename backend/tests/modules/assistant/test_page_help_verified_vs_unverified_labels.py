from __future__ import annotations

from tests.modules.assistant.test_page_help_manifest import _context, _repository, _service


def test_get_page_help_manifest_surfaces_unverified_labels_but_not_as_verified_actions() -> None:
    service = _service(_repository())

    result = service.get_page_help_manifest(
        page_id="P-02",
        language_code="en",
        actor=_context("assistant.chat.access", "planning.order.read", "planning.record.read", "planning.order.write", "planning.record.write"),
    )

    assert result.actions
    assert all(action.verified is False for action in result.actions)
    assert all(action.label_status == "unverified" for action in result.actions)


def test_verified_workspace_keeps_exact_labels_when_source_is_strong() -> None:
    service = _service(_repository())

    result = service.get_page_help_manifest(
        page_id="P-04",
        language_code="en",
        actor=_context("assistant.chat.access", "planning.staffing.read", "planning.staffing.write"),
    )

    assert any(action.label == "Assign" and action.verified is True for action in result.actions)
    assert any(action.label == "New demand group" and action.verified is True for action in result.actions)


def test_find_ui_action_stays_strict_and_does_not_promote_unverified_manifest_actions() -> None:
    service = _service(_repository())

    result = service.execute_registered_tool(
        tool_name="assistant.find_ui_action",
        input_data={"intent": "create_order", "page_id": "P-02", "language_code": "en"},
        actor=_context("assistant.chat.access", "planning.order.read", "planning.record.read", "planning.order.write", "planning.record.write"),
    )

    assert result.ok is True
    assert result.data["action"] is None
    assert result.data["safe_note"] == "Exact current UI action is not verified for this intent."
