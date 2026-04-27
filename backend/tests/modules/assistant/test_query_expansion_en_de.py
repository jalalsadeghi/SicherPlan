from __future__ import annotations

from app.modules.assistant.lexicon import expand_query_for_retrieval


def test_german_contract_query_expands_to_contract_and_document_context() -> None:
    expanded = expand_query_for_retrieval(
        "Wie registriere ich einen neuen Vertrag?",
        "de",
        workflow_intent="contract_or_document_register",
    )

    assert "contract" in expanded.detected_terms
    assert "vertrag" in {item.casefold() for item in expanded.expanded_terms_de}
    assert "contract" in expanded.expanded_terms_en
    assert {"PS-01", "C-01", "P-02"}.issubset(set(expanded.likely_page_ids))
    assert {"platform_services", "customers", "planning"}.issubset(set(expanded.likely_module_keys))


def test_english_customer_order_query_expands_to_customer_and_planning_context() -> None:
    expanded = expand_query_for_retrieval(
        "How do I create a new customer order?",
        "en",
        workflow_intent="customer_order_create",
    )

    assert "order" in expanded.detected_terms
    assert "customer" in expanded.detected_terms
    assert "customer order" in expanded.expanded_terms_en
    assert {"C-01", "P-02"}.issubset(set(expanded.likely_page_ids))
    assert {"customers", "planning"}.issubset(set(expanded.likely_module_keys))
