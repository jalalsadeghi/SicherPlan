from __future__ import annotations

import json
from pathlib import Path

from app.modules.assistant.field_dictionary import load_generated_field_lookup_corpus


def _artifact_path() -> Path:
    return Path(__file__).resolve().parents[3] / "app/modules/assistant/generated/field_lookup_corpus.json"


def test_generated_field_lookup_corpus_artifact_exists() -> None:
    artifact_path = _artifact_path()
    assert artifact_path.exists()

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert "frontend_i18n" in payload["generated_from"]
    assert payload["fields"]
    assert payload["lookups"]
    assert payload["terms"]


def test_generated_field_lookup_corpus_contains_known_terms() -> None:
    corpus = load_generated_field_lookup_corpus()
    assert corpus is not None

    fields = {item.field_key: item for item in corpus.field_definitions}
    lookups = {item.lookup_key: item for item in corpus.lookup_definitions}
    terms = {item.term_key: item for item in corpus.term_definitions}

    assert "customer.contract_reference" in fields
    assert "Vertragsreferenz" in fields["customer.contract_reference"].labels["de"]
    assert fields["customer.contract_reference"].source_basis

    assert "customer.legal_name" in fields
    assert "Rechtlicher Name" in fields["customer.legal_name"].labels["de"]

    assert "planning.release_state" in lookups
    assert "planning.staffing.demand_groups" in terms
