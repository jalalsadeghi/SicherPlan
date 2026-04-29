from __future__ import annotations

from app.modules.assistant.field_dictionary import search_platform_terms


def test_search_platform_terms_matches_demand_groups() -> None:
    matches = search_platform_terms(
        query="was bedeutet Demand groups",
        language_code="de",
        page_id="P-04",
        route_name="SicherPlanPlanningStaffing",
    )

    assert matches
    assert matches[0].term_key == "planning.staffing.demand_groups"
    assert matches[0].source_basis
    assert matches[0].definition


def test_search_platform_terms_matches_ai_74_english_terms() -> None:
    expected = {
        "what are Staffing actions": "planning.staffing.staffing_actions",
        "what are Release gates": "planning.staffing.release_gates",
        "what is Override evidence": "planning.staffing.override_evidence",
        "what are Partner releases": "planning.staffing.partner_releases",
        "what are Dispatch messages": "planning.staffing.dispatch_messages",
        "what does minimum staffing mean": "planning.staffing.minimum_staffing",
        "what are mandatory proofs": "planning.staffing.mandatory_proofs",
    }
    for query, term_key in expected.items():
        matches = search_platform_terms(
            query=query,
            language_code="en",
            page_id="P-04",
            route_name="SicherPlanPlanningStaffing",
        )
        assert matches, query
        assert matches[0].term_key == term_key, query
