from __future__ import annotations

import scripts.verify_assistant_platform_terms as verify_module
from scripts.verify_assistant_platform_terms import main


def test_verify_assistant_platform_terms_script_output(capsys) -> None:  # noqa: ANN001
    exit_code = main()
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "artifact_loaded=true" in captured
    assert "term_count=" in captured
    assert "Demand groups signal=true" in captured
    assert "Staffing-Aktionen signal=true" in captured
    assert "Release-Gates signal=true" in captured
    assert "Banana groups signal=false" in captured


def test_verify_assistant_platform_terms_script_fails_when_artifact_not_loaded(
    monkeypatch,
    capsys,
) -> None:  # noqa: ANN001
    class _Status:
        artifact_loaded = False
        artifact_version = None
        term_count = 0
        counts_by_module = {}

    monkeypatch.setattr(verify_module, "get_field_lookup_corpus_status", lambda: _Status())
    monkeypatch.setattr(verify_module, "search_platform_terms", lambda **_: [])
    monkeypatch.setattr(verify_module, "detect_platform_term_signal", lambda *_, **__: None)

    exit_code = verify_module.main()
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "error=artifact_not_loaded" in captured
    assert "error=demand_groups_not_detected" in captured
    assert "error=staffing_actions_not_detected" in captured
    assert "error=release_gates_not_detected" in captured


def test_verify_assistant_platform_terms_script_fails_on_false_positive(
    monkeypatch,
    capsys,
) -> None:  # noqa: ANN001
    class _Status:
        artifact_loaded = True
        artifact_version = "1"
        term_count = 523
        counts_by_module = {"planning": 293}

    def _fake_detect(query: str, **_: object) -> object | None:
        if query == "was bedeutet Banana groups":
            return object()
        return object()

    def _fake_search(*, query: str, **_: object) -> list[object]:
        if query == "was bedeutet Banana groups":
            return [object()]
        return [object()]

    monkeypatch.setattr(verify_module, "get_field_lookup_corpus_status", lambda: _Status())
    monkeypatch.setattr(verify_module, "search_platform_terms", _fake_search)
    monkeypatch.setattr(verify_module, "detect_platform_term_signal", _fake_detect)

    exit_code = verify_module.main()
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "error=banana_groups_false_positive" in captured
