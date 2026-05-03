from __future__ import annotations

from pathlib import Path

from app.modules.assistant import field_lookup_corpus_artifact as helper


def test_check_deterministic_returns_zero_for_stable_export(monkeypatch: object, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    def fake_export(*, repo_root: Path, output_path: Path) -> dict[str, object]:
        output_path.write_text('{"stable": true}\n', encoding="utf-8")
        return {
            "field_count": 1,
            "lookup_count": 1,
            "term_count": 1,
            "field_counts_by_module": {},
            "lookup_counts_by_module": {},
            "term_counts_by_module": {},
            "warnings": [],
        }

    monkeypatch.setattr(helper, "export_field_lookup_corpus", fake_export)

    assert helper.check_deterministic(repo_root=repo_root) == 0


def test_check_deterministic_returns_one_for_nondeterministic_export(monkeypatch: object, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    counter = {"value": 0}

    def fake_export(*, repo_root: Path, output_path: Path) -> dict[str, object]:
        counter["value"] += 1
        output_path.write_text(f'{{"run": {counter["value"]}}}\n', encoding="utf-8")
        return {
            "field_count": 1,
            "lookup_count": 1,
            "term_count": 1,
            "field_counts_by_module": {},
            "lookup_counts_by_module": {},
            "term_counts_by_module": {},
            "warnings": [],
        }

    monkeypatch.setattr(helper, "export_field_lookup_corpus", fake_export)

    assert helper.check_deterministic(repo_root=repo_root) == 1


def test_check_committed_returns_one_for_stale_artifact(monkeypatch: object, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifact_path = repo_root / "backend/app/modules/assistant/generated/field_lookup_corpus.json"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text('{"committed": false}\n', encoding="utf-8")

    def fake_export(*, repo_root: Path, output_path: Path) -> dict[str, object]:
        output_path.write_text('{"committed": true}\n', encoding="utf-8")
        return {
            "field_count": 1,
            "lookup_count": 1,
            "term_count": 1,
            "field_counts_by_module": {},
            "lookup_counts_by_module": {},
            "term_counts_by_module": {},
            "warnings": [],
        }

    monkeypatch.setattr(helper, "export_field_lookup_corpus", fake_export)

    assert helper.check_committed(repo_root=repo_root) == 1


def test_ensure_current_updates_committed_artifact(monkeypatch: object, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifact_path = repo_root / "backend/app/modules/assistant/generated/field_lookup_corpus.json"
    artifact_path.parent.mkdir(parents=True)

    def fake_export(*, repo_root: Path, output_path: Path) -> dict[str, object]:
        output_path.write_text('{"current": true}\n', encoding="utf-8")
        return {
            "field_count": 1,
            "lookup_count": 2,
            "term_count": 3,
            "field_counts_by_module": {"planning": 1},
            "lookup_counts_by_module": {"planning": 1},
            "term_counts_by_module": {"planning": 1},
            "warnings": [],
        }

    monkeypatch.setattr(helper, "export_field_lookup_corpus", fake_export)

    assert helper.ensure_current(repo_root=repo_root) == 0
    assert artifact_path.read_text(encoding="utf-8") == '{"current": true}\n'
