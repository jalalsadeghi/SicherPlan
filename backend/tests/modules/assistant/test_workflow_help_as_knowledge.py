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
        path.write_text("# Seed\n\nP-02 P-03 P-04\n", encoding="utf-8")


def test_workflow_help_generated_source_contains_real_workflow_content(tmp_path: Path) -> None:
    repo_root = tmp_path / "assistant-knowledge-test-workflow"
    repo_root.mkdir(parents=True, exist_ok=True)
    _prepare_repo(repo_root)
    repository = InMemoryKnowledgeRepository()
    loader = KnowledgeSourceLoader(
        allowed_roots=[repo_root / "docs", repo_root / "tmp" / "assistant-knowledge"]
    )
    service = AssistantKnowledgeIngestionService(loader=loader, repository=repository)

    result = service.ingest(build_default_knowledge_registrations(repo_root))

    assert result.sources_failed == 0
    workflow_path = str((repo_root / "tmp" / "assistant-knowledge" / "workflow-help.md").resolve())
    chunks = repository.chunks_by_path[workflow_path]
    order_chunk = next(chunk for chunk in chunks if "customer_order_create" in chunk["workflow_keys"])
    assert order_chunk["page_id"] == "P-02"
    assert "Orders & Planning Records" in order_chunk["content"]
    assert order_chunk["content_preview"]
