from __future__ import annotations

from app.modules.assistant.classifier import AssistantIntentCategory, classify_assistant_message
from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal, search_field_dictionary


def test_vertragsreferenz_is_detected_as_field_signal() -> None:
    signal = detect_field_or_lookup_signal(
        "was bedeutet Vertragsreferenz",
        page_id="C-01",
        route_name="SicherPlanCustomers",
    )

    assert signal is not None
    assert signal.intent_category == "field_meaning_question"


def test_vertragsreferenz_question_is_in_scope() -> None:
    result = classify_assistant_message(
        "was bedeutet Vertragsreferenz",
        route_context={"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
    )

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
    assert result.is_out_of_scope is False
    assert result.reason == "field_or_lookup_dictionary_match"


def test_apfelkuchen_remains_out_of_scope() -> None:
    result = classify_assistant_message("was bedeutet Apfelkuchen")

    assert result.category == AssistantIntentCategory.OUT_OF_SCOPE
    assert result.is_out_of_scope is True


def test_vertragsreferenz_search_returns_source_basis() -> None:
    matches = search_field_dictionary(
        query="was bedeutet Vertragsreferenz",
        language_code="de",
        page_id="C-01",
        route_name="SicherPlanCustomers",
    )

    assert matches
    assert matches[0].field_key == "customer.contract_reference"
    assert matches[0].source_basis
