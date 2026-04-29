from __future__ import annotations

from pathlib import Path

from app.modules.assistant import field_dictionary as field_dictionary_module
from app.modules.assistant.classifier import AssistantIntentCategory, classify_assistant_message
from app.modules.assistant.field_dictionary import search_platform_terms


def _stage_like_root(tmp_path: Path) -> Path:
    root = tmp_path / "stage-backend-only"
    (root / "backend").mkdir(parents=True)
    return root


def test_platform_term_stage_runtime_uses_generated_artifact(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    stage_root = _stage_like_root(tmp_path)
    field_dictionary_module._load_runtime_field_lookup_corpus.cache_clear()
    field_dictionary_module._build_field_lookup_corpus_from_sources.cache_clear()
    monkeypatch.setattr(field_dictionary_module, "_repo_root", lambda: stage_root)

    matches = search_platform_terms(
        query="was bedeutet Demand groups",
        language_code="de",
        page_id="P-04",
        route_name="SicherPlanPlanningStaffing",
    )

    assert matches
    assert matches[0].term_key == "planning.staffing.demand_groups"
    assert matches[0].source_basis


def test_platform_term_stage_runtime_classifier_stays_in_scope(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    stage_root = _stage_like_root(tmp_path)
    field_dictionary_module._load_runtime_field_lookup_corpus.cache_clear()
    field_dictionary_module._build_field_lookup_corpus_from_sources.cache_clear()
    monkeypatch.setattr(field_dictionary_module, "_repo_root", lambda: stage_root)

    result = classify_assistant_message(
        "was bedeutet Demand groups",
        route_context={
            "page_id": "P-04",
            "route_name": "SicherPlanPlanningStaffing",
            "path": "/admin/planning-staffing",
        },
    )

    assert result.category == AssistantIntentCategory.PLATFORM_RELATED
    assert result.reason == "platform_term_dictionary_match"
    assert result.intent == "platform_term_meaning_question"


def test_platform_term_stage_runtime_ai_74_matrix(tmp_path, monkeypatch) -> None:  # noqa: ANN001
    stage_root = _stage_like_root(tmp_path)
    field_dictionary_module._load_runtime_field_lookup_corpus.cache_clear()
    field_dictionary_module._build_field_lookup_corpus_from_sources.cache_clear()
    monkeypatch.setattr(field_dictionary_module, "_repo_root", lambda: stage_root)

    route_context = {
        "page_id": "P-04",
        "route_name": "SicherPlanPlanningStaffing",
        "path": "/admin/planning-staffing",
    }
    positive_queries = (
        "was bedeutet Staffing-Aktionen",
        "was bedeutet Release-Gates",
        "was bedeutet Override-Nachweise",
        "was bedeutet Partnerfreigaben",
        "was bedeutet Dispatch-Nachrichten",
        "was bedeutet Mindestbesetzung",
        "was bedeutet Pflichtnachweise",
        "what are Staffing actions",
        "what are Release gates",
        "what is Override evidence",
        "what are Partner releases",
        "what are Dispatch messages",
        "what does minimum staffing mean",
        "what are mandatory proofs",
    )
    for query in positive_queries:
        result = classify_assistant_message(query, route_context=route_context)
        assert result.category == AssistantIntentCategory.PLATFORM_RELATED, query
        assert result.reason == "platform_term_dictionary_match", query

    negative_queries = (
        "was bedeutet Banana groups",
        "was bedeutet random marketing funnel",
        "what does unicorn mode mean",
    )
    for query in negative_queries:
        result = classify_assistant_message(query, route_context=route_context)
        assert result.category == AssistantIntentCategory.OUT_OF_SCOPE, query
