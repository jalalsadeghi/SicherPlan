from __future__ import annotations

from pathlib import Path

from app.modules.assistant.knowledge.ingest import (
    AssistantKnowledgeIngestionService,
    build_default_knowledge_registrations,
)
from app.modules.assistant.knowledge.source_loader import KnowledgeSourceLoader
from tests.modules.assistant.test_knowledge_ingestion import InMemoryKnowledgeRepository


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_default_registrations_include_field_and_lookup_corpus() -> None:
    registrations = build_default_knowledge_registrations(_repo_root())
    source_types = {item.source_type for item in registrations}

    assert {
        "field_dictionary",
        "lookup_dictionary",
        "status_dictionary",
        "form_field_catalog",
        "frontend_i18n_label",
        "api_schema_field",
    }.issubset(source_types)


def test_field_dictionary_ingestion_creates_content_bearing_chunks() -> None:
    repo_root = _repo_root()
    registrations = [
        item
        for item in build_default_knowledge_registrations(repo_root)
        if item.source_type in {"field_dictionary", "lookup_dictionary"}
    ]
    repository = InMemoryKnowledgeRepository()
    service = AssistantKnowledgeIngestionService(
        loader=KnowledgeSourceLoader(allowed_roots=[repo_root]),
        repository=repository,
    )

    result = service.ingest(registrations)

    assert result.sources_failed == 0
    field_path = next(item.source_path for item in registrations if item.source_type == "field_dictionary")
    field_chunks = repository.chunks_by_path[str(Path(field_path).resolve())]
    assert field_chunks
    assert any("Rechtlicher Name" in str(chunk["content"]) for chunk in field_chunks)
