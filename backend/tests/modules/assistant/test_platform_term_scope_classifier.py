from __future__ import annotations

from app.modules.assistant.classifier import AssistantIntentCategory, classify_assistant_message


def _staffing_route() -> dict[str, str]:
    return {
        "page_id": "P-04",
        "route_name": "SicherPlanPlanningStaffing",
        "path": "/admin/planning-staffing",
    }


def test_platform_term_scope_classifier_accepts_demand_groups_without_platform_prefix() -> None:
    result = classify_assistant_message("was bedeutet Demand groups", route_context=_staffing_route())

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
    assert result.reason == "platform_term_dictionary_match"
    assert result.intent == "platform_term_meaning_question"


def test_platform_term_scope_classifier_accepts_demand_groups_with_shift_coverage_context() -> None:
    result = classify_assistant_message("was bedeutet Demand groups im Shift coverage", route_context=_staffing_route())

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
    assert result.intent == "platform_term_meaning_question"


def test_platform_term_scope_classifier_accepts_english_and_mixed_persian_queries() -> None:
    english = classify_assistant_message("what does Demand groups mean", route_context=_staffing_route())
    mixed = classify_assistant_message("Demand group چیست", route_context=_staffing_route())

    assert english.category == AssistantIntentCategory.PLATFORM_RELATED
    assert english.intent == "platform_term_meaning_question"
    assert mixed.category == AssistantIntentCategory.PLATFORM_RELATED
    assert mixed.intent == "platform_term_meaning_question"


def test_platform_term_scope_classifier_refuses_unknown_or_too_generic_terms() -> None:
    banana = classify_assistant_message("was bedeutet Banana groups", route_context=_staffing_route())
    generic = classify_assistant_message("was bedeutet groups", route_context=_staffing_route())

    assert banana.category == AssistantIntentCategory.OUT_OF_SCOPE
    assert generic.category == AssistantIntentCategory.OUT_OF_SCOPE


def test_platform_term_scope_classifier_accepts_ai_74_term_set() -> None:
    queries = [
        "was bedeutet Staffing-Aktionen",
        "was bedeutet Release-Gates",
        "was bedeutet Override-Nachweise",
        "was bedeutet Partnerfreigaben",
        "was bedeutet Dispatch-Nachrichten",
        "was bedeutet Mindestbesetzung",
        "was bedeutet Pflichtnachweise",
        "what are Staffing actions",
        "what are Release gates",
        "what is Override evidence",
        "what are Partner releases",
        "what are Dispatch messages",
        "what does minimum staffing mean",
        "what are mandatory proofs",
        "Staffing actions یعنی چی",
        "Release Gates یعنی چه",
        "Override evidence یعنی چه",
    ]

    for query in queries:
        result = classify_assistant_message(query, route_context=_staffing_route())
        assert result.category == AssistantIntentCategory.PLATFORM_RELATED, query
        assert result.reason == "platform_term_dictionary_match", query
        assert result.intent == "platform_term_meaning_question", query


def test_platform_term_scope_classifier_refuses_unrelated_ai_74_negative_examples() -> None:
    for query in (
        "was bedeutet Banana groups",
        "was bedeutet random marketing funnel",
        "what does unicorn mode mean",
    ):
        result = classify_assistant_message(query, route_context=_staffing_route())
        assert result.category == AssistantIntentCategory.OUT_OF_SCOPE, query
