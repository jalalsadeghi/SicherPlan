from __future__ import annotations

from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal
from app.modules.assistant.retrieval_planner import build_retrieval_plan


def test_status_question_without_route_is_marked_ambiguous() -> None:
    signal = detect_field_or_lookup_signal("was bedeutet Status")
    plan = build_retrieval_plan(message="was bedeutet Status", route_context=None)

    assert signal is not None
    assert signal.ambiguous is True
    assert signal.intent_category == "status_meaning_question"
    assert plan.intent_category == "status_meaning_question"


def test_customer_route_boosts_customer_status_candidates() -> None:
    signal = detect_field_or_lookup_signal(
        "was bedeutet Status",
        page_id="C-01",
        route_name="SicherPlanCustomers",
    )
    plan = build_retrieval_plan(
        message="was bedeutet Status",
        route_context={"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
    )

    assert signal is not None
    assert signal.lookup_matches
    assert signal.lookup_matches[0].page_id == "C-01"
    assert plan.likely_page_ids[0] == "C-01"


def test_employee_route_boosts_employee_status_candidates() -> None:
    signal = detect_field_or_lookup_signal(
        "was bedeutet Status",
        page_id="E-01",
        route_name="SicherPlanEmployees",
    )

    assert signal is not None
    assert signal.field_matches
    assert signal.field_matches[0].page_id == "E-01"
