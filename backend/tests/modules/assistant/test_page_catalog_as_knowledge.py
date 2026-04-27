from __future__ import annotations

from pathlib import Path

from app.modules.assistant.knowledge.ingest import (
    AssistantKnowledgeIngestionService,
    build_default_knowledge_registrations,
)
from app.modules.assistant.knowledge.source_loader import KnowledgeSourceLoader
from tests.modules.assistant.test_knowledge_ingestion import InMemoryKnowledgeRepository


def _prepare_repo(repo_root: Path) -> None:
    docs_root = repo_root / "docs"
    for relative_path in (
        "sprint/AI-Assistant.md",
        "engineering/ai-assistant-architecture.md",
        "security/ai-assistant-security.md",
        "qa/ai-assistant-test-plan.md",
        "support/hypercare-runbook.md",
        "training/us-35-role-guides.md",
        "discovery/us-1-t1-scope-review.md",
    ):
        path = docs_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Seed\n\nC-01 P-02 PS-01\n", encoding="utf-8")


def test_page_catalog_generated_source_contains_real_workspace_content() -> None:
    repo_root = Path(__file__).resolve().parents[4] / "tmp" / "assistant-knowledge-test-page-catalog"
    repo_root.mkdir(parents=True, exist_ok=True)
    _prepare_repo(repo_root)
    repository = InMemoryKnowledgeRepository()
    loader = KnowledgeSourceLoader(
        allowed_roots=[repo_root / "docs", repo_root / "tmp" / "assistant-knowledge"]
    )
    service = AssistantKnowledgeIngestionService(loader=loader, repository=repository)

    result = service.ingest(build_default_knowledge_registrations(repo_root))

    assert result.sources_failed == 0
    catalog_path = str((repo_root / "tmp" / "assistant-knowledge" / "page-route-catalog.md").resolve())
    chunks = repository.chunks_by_path[catalog_path]
    customer_chunk = next(chunk for chunk in chunks if chunk["page_id"] == "C-01")
    assert "Customers Workspace" in (customer_chunk["title"] or "")
    assert "required_permissions" in customer_chunk["content"]
    assert customer_chunk["content_preview"]
