from __future__ import annotations

from app.modules.assistant.field_dictionary import get_field_lookup_corpus_status


def test_field_dictionary_status_reports_packaged_artifact() -> None:
    status = get_field_lookup_corpus_status()

    assert status.artifact_loaded is True
    assert status.artifact_version == "1"
    assert status.field_count > 0
    assert status.lookup_count > 0
    assert status.counts_by_module.get("customers", 0) > 0
