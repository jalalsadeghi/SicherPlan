from __future__ import annotations

from app.modules.assistant.knowledge.chunker import chunk_text


def test_chunker_splits_markdown_by_heading() -> None:
    content = "# Intro\n\nAlpha\n\n## Details\n\nBeta\n"
    chunks = chunk_text(
        source_name="Guide",
        source_path="/docs/sprint/guide.md",
        content=content,
    )
    assert len(chunks) == 2
    assert chunks[0].title == "Intro"
    assert chunks[1].title == "Details"


def test_chunker_splits_large_sections_with_overlap() -> None:
    paragraph = "Paragraph " + ("x" * 900)
    content = "# Intro\n\n" + "\n\n".join([paragraph, paragraph, paragraph])
    chunks = chunk_text(
        source_name="Guide",
        source_path="/docs/sprint/guide.md",
        content=content,
        max_chunk_chars=1200,
        min_chunk_chars=200,
        chunk_overlap_chars=120,
    )
    assert len(chunks) >= 2
    assert chunks[0].content[-50:] in chunks[1].content


def test_chunker_preserves_page_ids_and_routes() -> None:
    content = "# Planning\n\nUse page P-04 and route /api/assistant/capabilities on SicherPlanPlanningStaffing.\n"
    chunks = chunk_text(
        source_name="Planning",
        source_path="/docs/sprint/planning.md",
        content=content,
    )
    assert "P-04" in chunks[0].content
    assert "/api/assistant/capabilities" in chunks[0].content
    assert "SicherPlanPlanningStaffing" in chunks[0].content


def test_chunker_does_not_create_empty_chunks() -> None:
    content = "# Intro\n\n\n\nAlpha\n\n## Next\n\n\nBeta\n"
    chunks = chunk_text(
        source_name="Guide",
        source_path="/docs/sprint/guide.md",
        content=content,
    )
    assert chunks
    assert all(chunk.content.strip() for chunk in chunks)


def test_metadata_extracts_page_id_and_module_key() -> None:
    content = "# Planning\n\nThe relevant page is P-04 for staffing.\n"
    chunks = chunk_text(
        source_name="Planning",
        source_path="/docs/sprint/planning.md",
        content=content,
    )
    assert chunks[0].metadata.page_id == "P-04"
    assert chunks[0].metadata.module_key == "planning"
