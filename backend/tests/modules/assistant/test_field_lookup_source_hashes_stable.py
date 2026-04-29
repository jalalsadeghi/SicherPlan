from __future__ import annotations

import json
from pathlib import Path

from app.modules.assistant import field_dictionary as field_dictionary_module


def _write_minimal_generation_sources(repo_root: Path, *, vue_model: str = "customerDraft.legal_name") -> None:
    backend_modules = repo_root / "backend/app/modules"
    frontend_root = repo_root / "web/apps/web-antd/src"
    (frontend_root / "sicherplan-legacy/i18n").mkdir(parents=True)
    (frontend_root / "locales/langs/de-DE").mkdir(parents=True)
    (frontend_root / "locales/langs/en-US").mkdir(parents=True)
    (frontend_root / "components").mkdir(parents=True)
    (frontend_root / "api").mkdir(parents=True)
    (backend_modules / "customers").mkdir(parents=True)
    (backend_modules / "assistant").mkdir(parents=True, exist_ok=True)

    (repo_root / "web/apps/web-antd/src/sicherplan-legacy/i18n/messages.ts").write_text(
        'export const messages = {\n'
        '  de: {\n'
        '    "customerAdmin.fields.legalName": "Rechtlicher Name",\n'
        '  },\n'
        '  en: {\n'
        '    "customerAdmin.fields.legalName": "Legal name",\n'
        '  },\n'
        '};\n',
        encoding="utf-8",
    )
    (repo_root / "web/apps/web-antd/src/locales/langs/de-DE/sicherplan.json").write_text(
        json.dumps({"customerAdmin": {"fields": {"legalName": "Rechtlicher Name"}}}),
        encoding="utf-8",
    )
    (repo_root / "web/apps/web-antd/src/locales/langs/en-US/sicherplan.json").write_text(
        json.dumps({"customerAdmin": {"fields": {"legalName": "Legal name"}}}),
        encoding="utf-8",
    )
    (repo_root / "web/apps/web-antd/src/components/CustomerForm.vue").write_text(
        "<template>\n"
        f'  <a-input :placeholder=\'t(\"customerAdmin.fields.legalName\")\' v-model=\"{vue_model}\" />\n'
        "</template>\n",
        encoding="utf-8",
    )
    (repo_root / "web/apps/web-antd/src/api/customers.ts").write_text(
        "export interface CustomerRead {\n"
        "  legal_name: string;\n"
        "}\n",
        encoding="utf-8",
    )
    (backend_modules / "customers/schemas.py").write_text(
        "class CustomerRead:\n"
        "    legal_name: str\n",
        encoding="utf-8",
    )
    (backend_modules / "assistant/field_dictionary.py").write_text("FIELD = 1\n", encoding="utf-8")


def _export_bytes(repo_root: Path, target: Path) -> bytes:
    field_dictionary_module.export_field_lookup_corpus(repo_root=repo_root, output_path=target)
    return target.read_bytes()


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
    _write_minimal_generation_sources(repo_root)
    (generated_dir / "field_lookup_corpus.json").write_text('{"stale": true}\n', encoding="utf-8")
    (pytest_cache_dir / "ignored.txt").write_text("ignored\n", encoding="utf-8")
    (node_modules_dir / "ignored.js").write_text("ignored\n", encoding="utf-8")

    hashes_before = field_dictionary_module._collect_source_hashes(repo_root)

    (generated_dir / "field_lookup_corpus.json").write_text('{"stale": false}\n', encoding="utf-8")
    (pytest_cache_dir / "ignored.txt").write_text("changed\n", encoding="utf-8")
    (node_modules_dir / "ignored.js").write_text("changed\n", encoding="utf-8")

    hashes_after = field_dictionary_module._collect_source_hashes(repo_root)

    assert hashes_before == hashes_after


def test_source_hashes_ignore_unrelated_frontend_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_minimal_generation_sources(repo_root)
    unrelated = repo_root / "web/apps/web-antd/src/components/UnrelatedBadge.vue"
    unrelated.write_text("<template><span>alpha</span></template>\n", encoding="utf-8")
    artifact_before = _export_bytes(repo_root, tmp_path / "before.json")

    hashes_before = field_dictionary_module._collect_source_hashes(repo_root)

    unrelated.write_text("<template><span>beta</span></template>\n", encoding="utf-8")
    artifact_after = _export_bytes(repo_root, tmp_path / "after.json")

    hashes_after = field_dictionary_module._collect_source_hashes(repo_root)

    assert hashes_before == hashes_after
    assert artifact_before == artifact_after


def test_source_hashes_change_when_locale_labels_change(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_minimal_generation_sources(repo_root)
    de_locale = repo_root / "web/apps/web-antd/src/locales/langs/de-DE/sicherplan.json"
    artifact_before = _export_bytes(repo_root, tmp_path / "before.json")

    hashes_before = field_dictionary_module._collect_source_hashes(repo_root)

    de_locale.write_text(
        json.dumps({"customerAdmin": {"fields": {"legalName": "Rechtlicher Firmenname"}}}),
        encoding="utf-8",
    )
    artifact_after = _export_bytes(repo_root, tmp_path / "after.json")

    hashes_after = field_dictionary_module._collect_source_hashes(repo_root)

    assert hashes_before != hashes_after
    assert hashes_before["locale_labels"] != hashes_after["locale_labels"]
    assert artifact_before != artifact_after


def test_source_hashes_change_when_extracted_vue_binding_changes(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_minimal_generation_sources(repo_root)
    component = repo_root / "web/apps/web-antd/src/components/CustomerForm.vue"
    artifact_before = _export_bytes(repo_root, tmp_path / "before.json")

    hashes_before = field_dictionary_module._collect_source_hashes(repo_root)

    component.write_text(
        "<template>\n"
        '  <a-input :placeholder=\'t(\"customerAdmin.fields.legalName\")\' v-model=\"customerDraft.name\" />\n'
        "</template>\n",
        encoding="utf-8",
    )
    artifact_after = _export_bytes(repo_root, tmp_path / "after.json")

    hashes_after = field_dictionary_module._collect_source_hashes(repo_root)

    assert hashes_before != hashes_after
    assert hashes_before["vue_field_bindings"] != hashes_after["vue_field_bindings"]
    assert artifact_before != artifact_after
