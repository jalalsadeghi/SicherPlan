from __future__ import annotations

from pathlib import Path

from app.modules.assistant import field_dictionary as field_dictionary_module
from app.modules.assistant.field_dictionary import search_field_dictionary, search_lookup_dictionary


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_generated_artifact_preserves_field_search_behavior(monkeypatch) -> None:
    source_results = search_field_dictionary(
        query="was bedeutet Vertragsreferenz",
        language_code="de",
        page_id="C-01",
        route_name="SicherPlanCustomers",
        repo_root=_repo_root(),
    )
    assert source_results

    temp_root = _repo_root() / "backend/tests"
    field_dictionary_module._load_runtime_field_lookup_corpus.cache_clear()
    field_dictionary_module._build_field_lookup_corpus_from_sources.cache_clear()
    monkeypatch.setattr(field_dictionary_module, "_repo_root", lambda: temp_root)

    artifact_results = search_field_dictionary(
        query="was bedeutet Vertragsreferenz",
        language_code="de",
        page_id="C-01",
        route_name="SicherPlanCustomers",
    )

    assert artifact_results
    assert artifact_results[0].field_key == source_results[0].field_key
    assert artifact_results[0].label == source_results[0].label
    assert artifact_results[0].source_basis


def test_generated_artifact_preserves_lookup_search_behavior(monkeypatch) -> None:
    source_results = search_lookup_dictionary(
        query="was bedeutet Freigabestatus",
        language_code="de",
        page_id="P-03",
        route_name="SicherPlanPlanningShifts",
        repo_root=_repo_root(),
    )
    assert source_results

    temp_root = _repo_root() / "backend/tests"
    field_dictionary_module._load_runtime_field_lookup_corpus.cache_clear()
    field_dictionary_module._build_field_lookup_corpus_from_sources.cache_clear()
    monkeypatch.setattr(field_dictionary_module, "_repo_root", lambda: temp_root)

    artifact_results = search_lookup_dictionary(
        query="was bedeutet Freigabestatus",
        language_code="de",
        page_id="P-03",
        route_name="SicherPlanPlanningShifts",
    )

    assert artifact_results
    assert artifact_results[0].lookup_key == source_results[0].lookup_key
    assert artifact_results[0].label == source_results[0].label
