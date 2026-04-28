from __future__ import annotations

import scripts.verify_assistant_field_dictionary as verify_module
from scripts.verify_assistant_field_dictionary import main


def test_verify_assistant_field_dictionary_script_output(capsys) -> None:  # noqa: ANN001
    exit_code = main()
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "artifact_loaded=true" in captured
    assert "field_count=" in captured
    assert "lookup_count=" in captured
    assert "counts_by_module=" in captured
    assert "Vertragsreferenz signal=true" in captured
    assert "Rechtlicher Name signal=true" in captured
    assert "Apfelkuchen signal=false" in captured


def test_verify_assistant_field_dictionary_script_fails_when_artifact_not_loaded(
    monkeypatch,
    capsys,
) -> None:  # noqa: ANN001
    class _Status:
        artifact_loaded = False
        artifact_version = None
        field_count = 0
        lookup_count = 0
        counts_by_module = {}

    monkeypatch.setattr(verify_module, "get_field_lookup_corpus_status", lambda: _Status())
    monkeypatch.setattr(verify_module, "search_field_dictionary", lambda **_: [])
    monkeypatch.setattr(verify_module, "detect_field_or_lookup_signal", lambda *_, **__: None)

    exit_code = verify_module.main()
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "error=artifact_not_loaded" in captured
    assert "error=vertragsreferenz_not_detected" in captured
    assert "error=rechtlicher_name_not_detected" in captured


def test_verify_assistant_field_dictionary_script_fails_on_false_positive(
    monkeypatch,
    capsys,
) -> None:  # noqa: ANN001
    class _Status:
        artifact_loaded = True
        artifact_version = "1"
        field_count = 219
        lookup_count = 10
        counts_by_module = {"customers": 106}

    def _fake_detect(query: str, **_: object) -> object | None:
        if query == "was bedeutet Apfelkuchen":
            return object()
        return object()

    monkeypatch.setattr(verify_module, "get_field_lookup_corpus_status", lambda: _Status())
    monkeypatch.setattr(
        verify_module,
        "search_field_dictionary",
        lambda **_: [object()],
    )
    monkeypatch.setattr(verify_module, "detect_field_or_lookup_signal", _fake_detect)

    exit_code = verify_module.main()
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "error=apfelkuchen_false_positive" in captured
