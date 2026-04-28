from __future__ import annotations

from pathlib import Path

from app.modules.assistant import field_dictionary as field_dictionary_module


def test_source_hashes_exclude_generated_artifact_and_volatile_dirs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    backend_modules = repo_root / "backend/app/modules"
    frontend_root = repo_root / "web/apps/web-antd/src"
    generated_dir = backend_modules / "assistant/generated"
    pytest_cache_dir = backend_modules / ".pytest_cache"
    node_modules_dir = frontend_root / "node_modules"

    generated_dir.mkdir(parents=True)
    pytest_cache_dir.mkdir(parents=True)
    node_modules_dir.mkdir(parents=True)
    (repo_root / "web/apps/web-antd/src/sicherplan-legacy/i18n").mkdir(parents=True)
    (repo_root / "web/apps/web-antd/src/locales/langs/de-DE").mkdir(parents=True)
    (repo_root / "web/apps/web-antd/src/locales/langs/en-US").mkdir(parents=True)

    legacy_messages = repo_root / "web/apps/web-antd/src/sicherplan-legacy/i18n/messages.ts"
    de_locale = repo_root / "web/apps/web-antd/src/locales/langs/de-DE/sicherplan.json"
    en_locale = repo_root / "web/apps/web-antd/src/locales/langs/en-US/sicherplan.json"
    assistant_code = backend_modules / "assistant/field_dictionary.py"

    legacy_messages.write_text('export const messages = { de: {}, en: {} };\n', encoding="utf-8")
    de_locale.write_text('{"admin":{"customers":"Kunden"}}\n', encoding="utf-8")
    en_locale.write_text('{"admin":{"customers":"Customers"}}\n', encoding="utf-8")
    assistant_code.parent.mkdir(parents=True, exist_ok=True)
    assistant_code.write_text("FIELD = 1\n", encoding="utf-8")
    (generated_dir / "field_lookup_corpus.json").write_text('{"stale": true}\n', encoding="utf-8")
    (pytest_cache_dir / "ignored.txt").write_text("ignored\n", encoding="utf-8")
    (node_modules_dir / "ignored.js").write_text("ignored\n", encoding="utf-8")

    hashes_before = field_dictionary_module._collect_source_hashes(repo_root)

    (generated_dir / "field_lookup_corpus.json").write_text('{"stale": false}\n', encoding="utf-8")
    (pytest_cache_dir / "ignored.txt").write_text("changed\n", encoding="utf-8")
    (node_modules_dir / "ignored.js").write_text("changed\n", encoding="utf-8")

    hashes_after = field_dictionary_module._collect_source_hashes(repo_root)

    assert hashes_before == hashes_after
