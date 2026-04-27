from __future__ import annotations

from app.modules.assistant.knowledge.chunker import chunk_text


def test_chunk_metadata_contains_content_preview_and_domain_metadata() -> None:
    chunks = chunk_text(
        source_type="user_manual",
        source_name="User Manual",
        source_path="/tmp/user-manual.md",
        language_code="mixed",
        content=(
            "# C-01 - Customers Workspace\n\n"
            "Customer / Kunde / Kunden workspace handles customer master, billing profile, history, and attachments. "
            "API family customers is used here. Workflow customer_create starts in C-01.\n"
        ),
    )

    assert chunks
    metadata = chunks[0].metadata
    assert metadata.page_id == "C-01"
    assert metadata.module_key == "customers"
    assert metadata.content_preview
    assert "customer_create" in metadata.workflow_keys
    assert "customers" in metadata.api_families
    assert any(term in metadata.domain_terms for term in ("customer", "customers"))
    assert any(alias in metadata.language_aliases for alias in ("customer", "kunde", "kunden"))
