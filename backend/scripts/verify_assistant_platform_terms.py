from __future__ import annotations

from app.modules.assistant.field_dictionary import (
    detect_platform_term_signal,
    get_field_lookup_corpus_status,
    search_platform_terms,
)


def main() -> int:
    status = get_field_lookup_corpus_status()
    errors: list[str] = []
    route_kwargs = {"page_id": "P-04", "route_name": "SicherPlanPlanningStaffing"}

    demand_groups_matches = search_platform_terms(
        query="was bedeutet Demand groups",
        language_code="de",
        **route_kwargs,
    )
    staffing_actions_matches = search_platform_terms(
        query="was bedeutet Staffing-Aktionen",
        language_code="de",
        **route_kwargs,
    )
    release_gates_matches = search_platform_terms(
        query="was bedeutet Release-Gates",
        language_code="de",
        **route_kwargs,
    )
    banana_groups_matches = search_platform_terms(
        query="was bedeutet Banana groups",
        language_code="de",
        **route_kwargs,
    )

    demand_groups_signal = detect_platform_term_signal("was bedeutet Demand groups", **route_kwargs)
    staffing_actions_signal = detect_platform_term_signal("was bedeutet Staffing-Aktionen", **route_kwargs)
    release_gates_signal = detect_platform_term_signal("was bedeutet Release-Gates", **route_kwargs)
    banana_groups_signal = detect_platform_term_signal("was bedeutet Banana groups", **route_kwargs)

    print(f"artifact_loaded={str(status.artifact_loaded).lower()}")
    print(f"artifact_version={status.artifact_version or 'none'}")
    print(f"term_count={status.term_count}")
    print(f"counts_by_module={status.counts_by_module}")
    print(
        "Demand groups signal="
        f"{str(demand_groups_signal is not None).lower()} "
        f"matches={len(demand_groups_matches)}"
    )
    print(
        "Staffing-Aktionen signal="
        f"{str(staffing_actions_signal is not None).lower()} "
        f"matches={len(staffing_actions_matches)}"
    )
    print(
        "Release-Gates signal="
        f"{str(release_gates_signal is not None).lower()} "
        f"matches={len(release_gates_matches)}"
    )
    print(
        "Banana groups signal="
        f"{str(banana_groups_signal is not None).lower()} "
        f"matches={len(banana_groups_matches)}"
    )

    if not status.artifact_loaded:
        errors.append("artifact_not_loaded")
    if not demand_groups_signal or not demand_groups_matches:
        errors.append("demand_groups_not_detected")
    if not staffing_actions_signal or not staffing_actions_matches:
        errors.append("staffing_actions_not_detected")
    if not release_gates_signal or not release_gates_matches:
        errors.append("release_gates_not_detected")
    if banana_groups_signal is not None or banana_groups_matches:
        errors.append("banana_groups_false_positive")

    if errors:
        for error in errors:
            print(f"error={error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
