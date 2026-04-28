from __future__ import annotations

from pathlib import Path

from app.modules.assistant.field_dictionary import export_field_lookup_corpus


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_field_lookup_export_is_byte_identical_for_repeated_runs(tmp_path: Path) -> None:
    first_output = tmp_path / "first.json"
    second_output = tmp_path / "second.json"

    export_field_lookup_corpus(repo_root=_repo_root(), output_path=first_output)
    export_field_lookup_corpus(repo_root=_repo_root(), output_path=second_output)

    assert first_output.read_bytes() == second_output.read_bytes()
