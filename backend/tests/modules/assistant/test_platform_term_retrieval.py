from __future__ import annotations

from app.modules.assistant.retrieval_planner import build_retrieval_plan


def _staffing_route() -> dict[str, str]:
    return {
        "page_id": "P-04",
        "route_name": "SicherPlanPlanningStaffing",
        "path": "/admin/planning-staffing",
    }


def test_platform_term_retrieval_plan_for_demand_groups_includes_related_sources() -> None:
    plan = build_retrieval_plan(
        message="was bedeutet Demand groups",
        route_context=_staffing_route(),
    )

    assert plan.intent_category == "platform_term_meaning_question"
    assert "platform_term_dictionary" in plan.required_sources
    assert "page_help_manifest" in plan.required_sources
    assert "workflow_help" in plan.required_sources
    assert "field_dictionary" in plan.required_sources
    assert "lookup_dictionary" in plan.required_sources
    assert "page_route_catalog" in plan.required_sources
    assert "P-04" in plan.likely_page_ids
