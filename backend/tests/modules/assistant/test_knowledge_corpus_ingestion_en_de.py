from __future__ import annotations

from pathlib import Path

from app.modules.assistant.knowledge.ingest import (
    AssistantKnowledgeIngestionService,
    build_default_knowledge_registrations,
)
from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from app.modules.assistant.knowledge.source_loader import KnowledgeSourceLoader
from tests.modules.assistant.test_knowledge_ingestion import InMemoryKnowledgeRepository
from tests.modules.assistant.test_knowledge_retrieval import InMemoryKnowledgeRetrievalRepository


def _prepare_repo(repo_root: Path) -> None:
    docs_root = repo_root / "docs"
    for relative_path, content in (
        ("sprint/AI-Assistant.md", "# Sprint\n\nC-01 P-02 PS-01\n"),
        ("engineering/ai-assistant-architecture.md", "# Architecture\n\nPlatform Services owns centralized documents.\n"),
        ("security/ai-assistant-security.md", "# Security\n\nCustomer and employee scopes stay isolated.\n"),
        ("qa/ai-assistant-test-plan.md", "# QA\n\nOrder and planning record tests.\n"),
        ("support/hypercare-runbook.md", "# Hypercare\n\nContracts are document-centered.\n"),
        ("training/us-35-role-guides.md", "# Role Guides\n\nCustomers workspace and planning workspaces.\n"),
        ("discovery/us-1-t1-scope-review.md", "# Scope Review\n\nPlatform services owns document links and versions.\n"),
    ):
        path = docs_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_generated_corpus_contains_customers_orders_and_platform_services_content(tmp_path: Path) -> None:
    repo_root = tmp_path / "assistant-knowledge-test-en-de"
    repo_root.mkdir(parents=True, exist_ok=True)
    _prepare_repo(repo_root)
    ingest_repository = InMemoryKnowledgeRepository()
    loader = KnowledgeSourceLoader(
        allowed_roots=[repo_root / "docs", repo_root / "tmp" / "assistant-knowledge"]
    )
    service = AssistantKnowledgeIngestionService(loader=loader, repository=ingest_repository)

    result = service.ingest(build_default_knowledge_registrations(repo_root))
    assert result.sources_failed == 0

    candidates = []
    for source_path, source in ingest_repository.sources.items():
        for chunk in ingest_repository.chunks_by_path.get(source_path, []):
            from app.modules.assistant.knowledge.types import KnowledgeChunkCandidate

            candidates.append(
                KnowledgeChunkCandidate(
                    chunk_id=f"{source.id}-{chunk['chunk_index']}",
                    source_id=source.id,
                    source_name=source.source_name,
                    source_type=source.source_type,
                    source_path=source.source_path,
                    chunk_index=int(chunk["chunk_index"]),
                    source_language=source.source_language,
                    title=chunk["title"],
                    content=str(chunk["content"]),
                    language_code=chunk["language_code"],
                    module_key=chunk["module_key"],
                    page_id=chunk["page_id"],
                    content_preview=chunk["content_preview"],
                    workflow_keys=list(chunk["workflow_keys"]),
                    role_keys=list(chunk["role_keys"]),
                    permission_keys=list(chunk["permission_keys"]),
                    api_families=list(chunk["api_families"]),
                    domain_terms=list(chunk["domain_terms"]),
                    language_aliases=list(chunk["language_aliases"]),
                    token_count=chunk["token_count"],
                )
            )

    retriever = AssistantKnowledgeRetriever(
        repository=InMemoryKnowledgeRetrievalRepository(candidates),
        max_context_chunks=4,
        max_input_chars=1200,
    )

    german_results = retriever.retrieve_knowledge_chunks(
        query="Wie registriere ich einen neuen Vertrag?",
        language_code="de",
        page_ids=["PS-01", "C-01", "P-02"],
        module_keys=["platform_services", "customers", "planning"],
        workflow_intent="contract_or_document_register",
        limit=4,
    )
    assert german_results
    assert any(item.page_id == "PS-01" for item in german_results[:3])

    english_results = retriever.retrieve_knowledge_chunks(
        query="How do I create a new customer?",
        language_code="en",
        page_ids=["C-01"],
        module_keys=["customers"],
        workflow_intent="customer_create",
        limit=4,
    )
    assert english_results
    assert english_results[0].page_id == "C-01"
    assert english_results[0].content_preview
    assert any(alias.lower() in {"customer", "kunde", "kunden"} for alias in english_results[0].language_aliases)
