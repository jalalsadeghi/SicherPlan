from __future__ import annotations

import json
from pathlib import Path

from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal, export_field_lookup_corpus


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _artifact_path() -> Path:
    return _repo_root() / "backend/app/modules/assistant/generated/field_lookup_corpus.json"


def test_committed_artifact_matches_regenerated_output(tmp_path: Path) -> None:
    regenerated = tmp_path / "field_lookup_corpus.json"
    export_field_lookup_corpus(repo_root=_repo_root(), output_path=regenerated)

    assert _artifact_path().read_bytes() == regenerated.read_bytes()


def test_field_lookup_smoke_terms_remain_stable() -> None:
    assert detect_field_or_lookup_signal("was bedeutet Vertragsreferenz") is not None
    assert detect_field_or_lookup_signal("was bedeutet Rechtlicher Name") is not None
    assert detect_field_or_lookup_signal("was bedeutet Apfelkuchen") is None

    payload = json.loads(_artifact_path().read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
