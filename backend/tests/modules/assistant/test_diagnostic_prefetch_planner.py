from __future__ import annotations

from app.modules.assistant.diagnostic_prefetch import detect_diagnostic_prefetch_intent, plan_diagnostic_prefetch
from app.modules.assistant.retrieval_planner import build_retrieval_plan


def test_german_mobile_app_visibility_question_is_planned_for_proactive_prefetch() -> None:
    message = "Ich habe einem Mitarbeiter eine Schicht zugewiesen, aber sie wird in der mobilen App nicht angezeigt. Woran könnte das liegen?"

    intent = detect_diagnostic_prefetch_intent(message)
    assert intent == "employee_shift_not_visible_in_mobile_app"

    prefetch = plan_diagnostic_prefetch(
        message=message,
        detected_language="de",
        route_context=None,
    )
    assert prefetch is not None
    assert prefetch.intent == "employee_shift_not_visible_in_mobile_app"
    assert prefetch.missing_inputs == ("employee_name", "date", "shift_or_assignment_ref")

    retrieval_plan = build_retrieval_plan(message=message, route_context=None)
    assert retrieval_plan.intent_category == "operational_diagnostic"
    assert retrieval_plan.diagnostic_intent == "employee_shift_not_visible_in_mobile_app"
    assert retrieval_plan.diagnostic_missing_inputs == ("employee_name", "date", "shift_or_assignment_ref")


def test_english_mobile_app_visibility_question_keeps_specific_employee_and_date_inputs() -> None:
    message = "Markus cannot see his assigned shift in the mobile app on May 1, 2026. Why is it not showing?"

    prefetch = plan_diagnostic_prefetch(
        message=message,
        detected_language="en",
        route_context={"page_id": "P-04"},
    )
    assert prefetch is not None
    assert prefetch.intent in {
        "employee_shift_not_visible_in_mobile_app",
        "employee_assignment_visibility",
        "employee_app_schedule_visibility",
    }
    assert prefetch.employee_name == "Markus"
    assert prefetch.date_iso == "2026-05-01"
    assert "employee_name" not in prefetch.missing_inputs
    assert "date" not in prefetch.missing_inputs
