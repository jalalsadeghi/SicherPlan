from __future__ import annotations

from app.modules.assistant.classifier import AssistantIntentCategory, classify_assistant_message
from app.modules.assistant.field_dictionary import detect_platform_term_signal, get_platform_term_definition


def test_demand_groups_term_has_grounded_definition() -> None:
    definition = get_platform_term_definition("planning.staffing.demand_groups")

    assert definition is not None
    assert "minimum" in (definition.definition_en or "").lower()
    assert "target" in (definition.definition_en or "").lower()
    assert "qualification" in (definition.definition_en or "").lower()
    assert any("PlanningStaffingCoverageView.vue" in item.source_name for item in definition.source_basis)


def test_demand_groups_question_is_in_scope_via_platform_term_dictionary() -> None:
    signal = detect_platform_term_signal(
        "was bedeutet Demand groups",
        page_id="P-04",
        route_name="SicherPlanPlanningStaffing",
    )
    assert signal is not None
    assert signal.intent_category == "platform_term_meaning_question"

    result = classify_assistant_message(
        "was bedeutet Demand groups",
        route_context={
            "page_id": "P-04",
            "route_name": "SicherPlanPlanningStaffing",
            "path": "/admin/planning-staffing",
        },
    )

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
    assert result.reason == "platform_term_dictionary_match"
