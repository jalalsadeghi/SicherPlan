from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.modules.assistant.knowledge.ingest import (
    AssistantKnowledgeIngestionService,
    build_default_knowledge_registrations,
)
from app.modules.assistant.knowledge.repository import AssistantKnowledgeRepository
from app.modules.assistant.knowledge.source_loader import KnowledgeSourceLoader
from app.modules.assistant.knowledge.types import KnowledgeSourceRegistration
from app.modules.assistant.models import AssistantKnowledgeSource


@dataclass
class InMemoryKnowledgeRepository:
    sources: dict[str, AssistantKnowledgeSource] = field(default_factory=dict)
    chunks_by_path: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    counter: int = 0

    def find_active_source_by_path_hash(self, *, source_path: str, source_hash: str) -> AssistantKnowledgeSource | None:
        source = self.sources.get(source_path)
        if source is None:
            return None
        if source.source_hash == source_hash and source.status == "active":
            return source
        return None

    def find_latest_source_by_path(self, *, source_path: str) -> AssistantKnowledgeSource | None:
        return self.sources.get(source_path)

    def upsert_source(
        self,
        *,
        existing_source: AssistantKnowledgeSource | None,
        source_type: str,
        source_name: str,
        source_path: str,
        source_hash: str,
        source_version: str | None,
        source_language: str | None,
        status: str,
    ) -> AssistantKnowledgeSource:
        source = existing_source or AssistantKnowledgeSource(
            id=f"src-{self.counter}",
            source_type=source_type,
            source_name=source_name,
            source_path=source_path,
            source_hash=source_hash,
            source_version=source_version,
            source_language=source_language,
            status=status,
            last_ingested_at=None,
            created_at=None,
            updated_at=None,
        )
        self.counter += 1
        source.source_type = source_type
        source.source_name = source_name
        source.source_path = source_path
        source.source_hash = source_hash
        source.source_version = source_version
        source.source_language = source_language
        source.status = status
        self.sources[source_path] = source
        return source

    def replace_chunks(self, *, source: AssistantKnowledgeSource, chunks: list[dict[str, object]]) -> None:
        self.chunks_by_path[source.source_path] = list(chunks)


def _service(docs_root: Path, repository: InMemoryKnowledgeRepository) -> AssistantKnowledgeIngestionService:
    loader = KnowledgeSourceLoader(allowed_roots=[docs_root])
    return AssistantKnowledgeIngestionService(loader=loader, repository=repository)


def test_ingestion_creates_source_and_chunks(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    source_file = docs_root / "planning.md"
    source_file.write_text("# Planning\n\nUse page P-04.\n", encoding="utf-8")
    repository = InMemoryKnowledgeRepository()

    result = _service(docs_root, repository).ingest(
        [
            KnowledgeSourceRegistration(
                source_type="markdown",
                source_name="Planning",
                source_path=str(source_file),
            )
        ]
    )

    assert result.sources_indexed == 1
    assert result.chunks_created >= 1
    assert str(source_file.resolve()) in repository.sources
    assert repository.chunks_by_path[str(source_file.resolve())][0]["page_id"] == "P-04"


def test_ingestion_skips_unchanged_source(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    source_file = docs_root / "planning.md"
    source_file.write_text("# Planning\n\nUse page P-04.\n", encoding="utf-8")
    repository = InMemoryKnowledgeRepository()
    service = _service(docs_root, repository)
    registration = KnowledgeSourceRegistration(
        source_type="markdown",
        source_name="Planning",
        source_path=str(source_file),
    )

    first = service.ingest([registration])
    second = service.ingest([registration])

    assert first.sources_indexed == 1
    assert second.sources_skipped == 1


def test_ingestion_reindexes_changed_source(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    source_file = docs_root / "planning.md"
    source_file.write_text("# Planning\n\nUse page P-04.\n", encoding="utf-8")
    repository = InMemoryKnowledgeRepository()
    service = _service(docs_root, repository)
    registration = KnowledgeSourceRegistration(
        source_type="markdown",
        source_name="Planning",
        source_path=str(source_file),
    )

    first = service.ingest([registration])
    original_hash = repository.sources[str(source_file.resolve())].source_hash
    source_file.write_text("# Planning\n\nUse page P-05.\n", encoding="utf-8")
    second = service.ingest([registration])

    assert first.sources_indexed == 1
    assert second.sources_indexed == 1
    assert repository.sources[str(source_file.resolve())].source_hash != original_hash
    assert repository.chunks_by_path[str(source_file.resolve())][0]["page_id"] == "P-05"


def test_unsupported_pdf_fails_safely_if_not_implemented(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    source_file = docs_root / "manual.pdf"
    source_file.write_bytes(b"%PDF-1.4")
    repository = InMemoryKnowledgeRepository()

    result = _service(docs_root, repository).ingest(
        [
            KnowledgeSourceRegistration(
                source_type="pdf",
                source_name="Manual",
                source_path=str(source_file),
            )
        ]
    )

    assert result.sources_failed == 1
    assert "PDF extraction is not implemented" in result.failures[0].error


def test_default_registrations_include_generated_corpus_seed_types(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    (docs_root / "sprint").mkdir(parents=True)
    (docs_root / "engineering").mkdir(parents=True)
    (docs_root / "security").mkdir(parents=True)
    (docs_root / "qa").mkdir(parents=True)
    (docs_root / "support").mkdir(parents=True)
    (docs_root / "training").mkdir(parents=True)
    (docs_root / "discovery").mkdir(parents=True)
    for relative_path in (
        "sprint/AI-Assistant.md",
        "engineering/ai-assistant-architecture.md",
        "security/ai-assistant-security.md",
        "qa/ai-assistant-test-plan.md",
        "support/hypercare-runbook.md",
        "training/us-35-role-guides.md",
        "discovery/us-1-t1-scope-review.md",
    ):
        (docs_root / relative_path).write_text("# Seed\n\nP-02\n", encoding="utf-8")

    registrations = build_default_knowledge_registrations(tmp_path)
    source_types = {item.source_type for item in registrations}

    assert {
        "page_route_catalog",
        "page_help_manifest",
        "workflow_help",
        "expert_knowledge_pack",
        "ui_action_catalog",
        "api_export",
        "role_page_coverage",
        "operational_handbook",
        "user_manual",
        "implementation_data_model",
    }.issubset(source_types)


def test_default_registrations_skip_missing_optional_docs(tmp_path: Path) -> None:
    registrations = build_default_knowledge_registrations(tmp_path)
    assert registrations
    assert all(Path(item.source_path).exists() for item in registrations)
