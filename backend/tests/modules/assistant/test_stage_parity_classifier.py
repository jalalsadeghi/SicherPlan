from __future__ import annotations

from pathlib import Path

import pytest

from app.modules.assistant import field_dictionary as field_dictionary_module
from app.modules.assistant.classifier import AssistantIntentCategory, classify_assistant_message


def _stage_like_root(tmp_path: Path) -> Path:
    root = tmp_path / "stage-backend-only"
    (root / "backend").mkdir(parents=True)
    return root


@pytest.fixture
def artifact_only_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage_root = _stage_like_root(tmp_path)
    field_dictionary_module._load_runtime_field_lookup_corpus.cache_clear()
    field_dictionary_module._build_field_lookup_corpus_from_sources.cache_clear()
    monkeypatch.setattr(field_dictionary_module, "_repo_root", lambda: stage_root)


@pytest.mark.parametrize(
    ("question", "route_context", "expected_out_of_scope", "allowed_intents"),
    [
        (
            "was bedeutet Vertragsreferenz",
            {"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
            False,
            {"field_meaning_question"},
        ),
        (
            "was bedeutet Rechtlicher Name",
            {"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
            False,
            {"field_meaning_question"},
        ),
        (
            "was bedeutet Kundennummer",
            {"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
            False,
            {"field_meaning_question"},
        ),
        (
            "was bedeutet Externe Referenz",
            {"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
            False,
            {"field_meaning_question"},
        ),
        (
            "was bedeutet Freigabestatus",
            {"page_id": "P-03", "route_name": "SicherPlanPlanningShifts", "path": "/admin/planning-shifts"},
            False,
            {"lookup_meaning_question", "status_meaning_question"},
        ),
        (
            "was bedeutet release_ready",
            {"page_id": "P-03", "route_name": "SicherPlanPlanningShifts", "path": "/admin/planning-shifts"},
            False,
            {"lookup_meaning_question", "status_meaning_question"},
        ),
        (
            "was bedeutet Schichttyp",
            {"page_id": "P-03", "route_name": "SicherPlanPlanningShifts", "path": "/admin/planning-shifts"},
            False,
            {"field_meaning_question"},
        ),
        (
            "was bedeutet Apfelkuchen",
            None,
            True,
            set(),
        ),
    ],
)
def test_stage_parity_classifier_matrix(
    artifact_only_runtime: None,
    question: str,
    route_context: dict[str, str] | None,
    expected_out_of_scope: bool,
    allowed_intents: set[str],
) -> None:
    result = classify_assistant_message(question, route_context=route_context)

    assert result.is_out_of_scope is expected_out_of_scope
    if expected_out_of_scope:
        assert result.category == AssistantIntentCategory.OUT_OF_SCOPE
    else:
        assert result.category == AssistantIntentCategory.PLATFORM_RELATED
        assert result.is_platform_related is True
        assert result.intent in allowed_intents
