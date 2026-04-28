from __future__ import annotations

from pathlib import Path

from app.modules.assistant import field_dictionary as field_dictionary_module
from app.modules.assistant.classifier import AssistantIntentCategory, classify_assistant_message
from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal, search_field_dictionary


def _stage_like_root(tmp_path: Path) -> Path:
    root = tmp_path / "stage-backend-only"
    (root / "backend").mkdir(parents=True)
    return root


def test_generated_artifact_loads_without_frontend_sources(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    stage_root = _stage_like_root(tmp_path)
    field_dictionary_module._load_runtime_field_lookup_corpus.cache_clear()
    field_dictionary_module._build_field_lookup_corpus_from_sources.cache_clear()
    monkeypatch.setattr(field_dictionary_module, "_repo_root", lambda: stage_root)

    signal = detect_field_or_lookup_signal(
        "was bedeutet Rechtlicher Name",
        page_id="C-01",
        route_name="SicherPlanCustomers",
    )

    assert signal is not None
    assert signal.intent_category == "field_meaning_question"


def test_stage_like_runtime_uses_artifact_for_source_basis(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    stage_root = _stage_like_root(tmp_path)
    field_dictionary_module._load_runtime_field_lookup_corpus.cache_clear()
    field_dictionary_module._build_field_lookup_corpus_from_sources.cache_clear()
    monkeypatch.setattr(field_dictionary_module, "_repo_root", lambda: stage_root)

    matches = search_field_dictionary(
        query="was bedeutet Vertragsreferenz",
        language_code="de",
        page_id="C-01",
        route_name="SicherPlanCustomers",
    )

    assert matches
    assert matches[0].field_key == "customer.contract_reference"
    assert matches[0].source_basis


def test_stage_like_runtime_does_not_require_frontend_sources_for_classifier(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    stage_root = _stage_like_root(tmp_path)
    field_dictionary_module._load_runtime_field_lookup_corpus.cache_clear()
    field_dictionary_module._build_field_lookup_corpus_from_sources.cache_clear()
    monkeypatch.setattr(field_dictionary_module, "_repo_root", lambda: stage_root)

    result = classify_assistant_message(
        "was bedeutet Rechtlicher Name",
        route_context={"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
    )

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
