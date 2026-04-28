from __future__ import annotations

from app.modules.assistant.field_dictionary import (
    detect_field_or_lookup_signal,
    get_field_lookup_corpus_status,
    search_field_dictionary,
)


def main() -> int:
    status = get_field_lookup_corpus_status()
    errors: list[str] = []
    vertragsreferenz_matches = search_field_dictionary(
        query="was bedeutet Vertragsreferenz",
        language_code="de",
        page_id="C-01",
        route_name="SicherPlanCustomers",
    )
    rechtlicher_name_matches = search_field_dictionary(
        query="was bedeutet Rechtlicher Name",
        language_code="de",
        page_id="C-01",
        route_name="SicherPlanCustomers",
    )
    apfelkuchen_signal = detect_field_or_lookup_signal("was bedeutet Apfelkuchen")
    vertragsreferenz_signal = detect_field_or_lookup_signal(
        "was bedeutet Vertragsreferenz",
        page_id="C-01",
        route_name="SicherPlanCustomers",
    )
    rechtlicher_name_signal = detect_field_or_lookup_signal(
        "was bedeutet Rechtlicher Name",
        page_id="C-01",
        route_name="SicherPlanCustomers",
    )

    print(f"artifact_loaded={str(status.artifact_loaded).lower()}")
    print(f"artifact_version={status.artifact_version or 'none'}")
    print(f"field_count={status.field_count}")
    print(f"lookup_count={status.lookup_count}")
    print(f"counts_by_module={status.counts_by_module}")
    print(
        "Vertragsreferenz signal="
        f"{str(vertragsreferenz_signal is not None).lower()} "
        f"matches={len(vertragsreferenz_matches)}"
    )
    print(
        "Rechtlicher Name signal="
        f"{str(rechtlicher_name_signal is not None).lower()} "
        f"matches={len(rechtlicher_name_matches)}"
    )
    print(f"Apfelkuchen signal={str(apfelkuchen_signal is not None).lower()}")

    if not status.artifact_loaded:
        errors.append("artifact_not_loaded")
    if not vertragsreferenz_signal or not vertragsreferenz_matches:
        errors.append("vertragsreferenz_not_detected")
    if not rechtlicher_name_signal or not rechtlicher_name_matches:
        errors.append("rechtlicher_name_not_detected")
    if apfelkuchen_signal is not None:
        errors.append("apfelkuchen_false_positive")

    if errors:
        for error in errors:
            print(f"error={error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
