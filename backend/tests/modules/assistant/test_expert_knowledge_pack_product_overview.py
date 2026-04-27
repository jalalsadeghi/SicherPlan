from __future__ import annotations

from app.modules.assistant.expert_knowledge_pack import (
    EXPERT_KNOWLEDGE_PACK_BY_KEY,
    render_expert_knowledge_pack_markdown,
)
from app.modules.assistant.knowledge.chunker import chunk_text


def test_product_overview_pack_is_bilingual_and_source_grounded() -> None:
    pack = EXPERT_KNOWLEDGE_PACK_BY_KEY["product_overview"]

    assert "what does this software do" in pack.aliases_en
    assert "was macht diese software" in pack.aliases_de
    assert {"C-01", "P-02", "FI-01"}.issubset(set(pack.linked_page_ids))
    assert len(pack.facts) >= 4
    assert all(fact.source_basis for fact in pack.facts)


def test_product_overview_pack_renders_content_bearing_knowledge_without_answer_templates() -> None:
    markdown = render_expert_knowledge_pack_markdown()

    assert "SicherPlan product overview (product_overview)" in markdown
    assert "multi-tenant security operations platform" in markdown
    assert "If user asks" not in markdown
    assert "return Y" not in markdown

    chunks = chunk_text(
        source_type="expert_knowledge_pack",
        source_name="SicherPlan Expert Knowledge Pack",
        source_path="/tmp/expert-knowledge-pack.md",
        content=markdown,
        language_code="en",
    )
    overview_chunk = next(chunk for chunk in chunks if "product_overview" in chunk.content)
    assert overview_chunk.content
    assert overview_chunk.metadata.content_preview
    assert overview_chunk.metadata.domain_terms
