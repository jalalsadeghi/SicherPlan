from __future__ import annotations

from app.modules.assistant.field_dictionary import build_field_lookup_corpus


def test_platform_term_corpus_contains_demand_groups() -> None:
    corpus = build_field_lookup_corpus()
    terms = {item.term_key: item for item in corpus.term_definitions}

    assert "planning.staffing.demand_groups" in terms
    definition = terms["planning.staffing.demand_groups"]
    assert definition.page_id == "P-04"
    assert definition.module_key == "planning"
    assert "Demand groups" in definition.labels.get("en", [])
    assert "Demand Groups" in definition.labels.get("de", [])
    assert definition.definition_en
    assert definition.definition_de
    assert definition.source_basis


def test_platform_term_corpus_contains_ai_74_term_set() -> None:
    corpus = build_field_lookup_corpus()
    terms = {item.term_key: item for item in corpus.term_definitions}

    expected = {
        "planning.staffing.staffing_actions",
        "planning.staffing.release_gates",
        "planning.staffing.override_evidence",
        "planning.staffing.partner_releases",
        "planning.staffing.dispatch_messages",
        "planning.staffing.minimum_staffing",
        "planning.staffing.mandatory_proofs",
    }
    assert expected.issubset(set(terms))
