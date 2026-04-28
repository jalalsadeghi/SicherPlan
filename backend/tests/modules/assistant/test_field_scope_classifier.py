from __future__ import annotations

from app.modules.assistant.classifier import AssistantIntentCategory, classify_assistant_message
from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal


def test_rechtlicher_name_is_in_scope_without_sicherplan_keyword() -> None:
    result = classify_assistant_message("was bedeutet Rechtlicher Name")

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
    assert result.intent == "field_meaning_question"


def test_rechtlicher_name_with_sicherplan_stays_field_meaning_question() -> None:
    result = classify_assistant_message("was bedeutet Rechtlicher Name im sicherplan")

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
    assert result.intent == "field_meaning_question"


def test_english_legal_name_question_is_in_scope() -> None:
    result = classify_assistant_message("what does Legal name mean")

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
    assert result.intent == "field_meaning_question"


def test_status_question_is_in_scope_but_ambiguous() -> None:
    result = classify_assistant_message("was bedeutet Status")
    signal = detect_field_or_lookup_signal("was bedeutet Status")

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
    assert result.intent == "status_meaning_question"
    assert signal is not None
    assert signal.ambiguous is True


def test_apfel_stays_out_of_scope() -> None:
    result = classify_assistant_message("was bedeutet Apfel")

    assert result.category == AssistantIntentCategory.OUT_OF_SCOPE
    assert result.intent is None


def test_vague_this_field_question_uses_route_context() -> None:
    result = classify_assistant_message(
        "was bedeutet dieses Feld",
        route_context={"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
    )

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
    assert result.intent == "form_help_question"
