from __future__ import annotations

from app.modules.assistant.tool_name_adapter import (
    build_provider_tool_name_map,
    is_valid_provider_tool_name,
    to_provider_tool_name,
)


def test_dotted_names_are_converted_to_provider_safe_names() -> None:
    assert to_provider_tool_name("assistant.get_current_user_capabilities") == "assistant_get_current_user_capabilities"
    assert to_provider_tool_name("navigation.build_allowed_link") == "navigation_build_allowed_link"
    assert to_provider_tool_name("planning.find_shifts") == "planning_find_shifts"


def test_provider_tool_name_map_is_unique_and_stable() -> None:
    names = [
        "assistant.find.ui.action",
        "assistant.find_ui_action",
        "employees.search_employee_by_name",
    ]
    first = build_provider_tool_name_map(names)
    second = build_provider_tool_name_map(names)

    assert first == second
    assert len(first) == 3
    assert first["assistant_find_ui_action"] == "assistant.find.ui.action"
    assert first["assistant_find_ui_action_2"] == "assistant.find_ui_action"
    assert first["employees_search_employee_by_name"] == "employees.search_employee_by_name"
    assert all(is_valid_provider_tool_name(name) for name in first)

