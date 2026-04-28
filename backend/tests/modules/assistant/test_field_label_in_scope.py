from __future__ import annotations

from app.modules.assistant.classifier import AssistantIntentCategory, classify_assistant_message
from app.modules.assistant.retrieval_planner import build_retrieval_plan


def test_short_field_label_question_is_in_scope_without_sicherplan_keyword() -> None:
    result = classify_assistant_message(
        "was bedeutet Rechtlicher Name",
        route_context={"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
    )

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
    assert result.is_out_of_scope is False
    assert result.reason == "field_or_lookup_dictionary_match"
    assert result.intent == "field_meaning_question"


def test_field_label_question_builds_field_lookup_retrieval_plan() -> None:
    plan = build_retrieval_plan(
        message="was bedeutet Rechtlicher Name",
        route_context={"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
    )

    assert plan.intent_category == "field_meaning_question"
    assert "C-01" in plan.likely_page_ids
    assert "customers" in plan.likely_module_keys
    assert "field_dictionary" in plan.required_sources
