"""Knowledge ingestion orchestration for assistant documentation sources."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from app.modules.assistant.page_catalog_seed import ASSISTANT_PAGE_ROUTE_SEEDS
from app.modules.assistant.page_help_seed import ASSISTANT_PAGE_HELP_SEEDS
from app.modules.assistant.knowledge.chunker import chunk_text
from app.modules.assistant.knowledge.repository import AssistantKnowledgeRepository
from app.modules.assistant.knowledge.source_loader import KnowledgeSourceLoader
from app.modules.assistant.knowledge.types import (
    ChunkedKnowledgeDocument,
    KnowledgeSourceRegistration,
    UnsupportedKnowledgeSourceError,
)
from app.modules.assistant.models import AssistantKnowledgeSource


@dataclass(frozen=True)
class KnowledgeIngestionFailure:
    source_path: str
    error: str


@dataclass(frozen=True)
class KnowledgeIngestionResult:
    sources_seen: int
    sources_indexed: int
    sources_skipped: int
    sources_failed: int
    chunks_created: int
    failures: list[KnowledgeIngestionFailure]


class AssistantKnowledgeIngestionService:
    def __init__(
        self,
        *,
        loader: KnowledgeSourceLoader,
        repository: AssistantKnowledgeRepository | None = None,
    ) -> None:
        self.loader = loader
        self.repository = repository

    def ingest(self, registrations: list[KnowledgeSourceRegistration]) -> KnowledgeIngestionResult:
        if self.repository is None:
            raise RuntimeError("Knowledge repository is required for ingestion.")

        sources_indexed = 0
        sources_skipped = 0
        sources_failed = 0
        chunks_created = 0
        failures: list[KnowledgeIngestionFailure] = []

        for registration in registrations:
            try:
                loaded = self.loader.load(registration)
                unchanged = self.repository.find_active_source_by_path_hash(
                    source_path=loaded.source_path,
                    source_hash=loaded.source_hash,
                )
                if unchanged is not None:
                    sources_skipped += 1
                    continue

                existing = self.repository.find_latest_source_by_path(source_path=loaded.source_path)
                source = self.repository.upsert_source(
                    existing_source=existing,
                    source_type=loaded.source_type,
                    source_name=loaded.source_name,
                    source_path=loaded.source_path,
                    source_hash=loaded.source_hash,
                    source_version=loaded.source_version,
                    status="active",
                )
                chunk_rows = self._build_chunk_rows(
                    source_name=loaded.source_name,
                    source_path=loaded.source_path,
                    content=loaded.content,
                    language_code=loaded.language_code,
                )
                self.repository.replace_chunks(source=source, chunks=chunk_rows)
                sources_indexed += 1
                chunks_created += len(chunk_rows)
            except Exception as exc:
                sources_failed += 1
                failures.append(
                    KnowledgeIngestionFailure(
                        source_path=registration.source_path,
                        error=str(exc),
                    )
                )
                self._mark_failed_source(registration=registration, error=exc)

        return KnowledgeIngestionResult(
            sources_seen=len(registrations),
            sources_indexed=sources_indexed,
            sources_skipped=sources_skipped,
            sources_failed=sources_failed,
            chunks_created=chunks_created,
            failures=failures,
        )

    def _mark_failed_source(self, *, registration: KnowledgeSourceRegistration, error: Exception) -> None:
        if self.repository is None:
            return
        if isinstance(error, UnsupportedKnowledgeSourceError):
            status = "failed"
        else:
            status = "failed"
        existing = self.repository.find_latest_source_by_path(source_path=str(Path(registration.source_path).resolve()))
        self.repository.upsert_source(
            existing_source=existing,
            source_type=registration.source_type,
            source_name=registration.source_name,
            source_path=str(Path(registration.source_path).resolve()),
            source_hash=hashlib.sha256(
                f"failed:{registration.source_type}:{registration.source_path}".encode("utf-8")
            ).hexdigest(),
            source_version=None,
            status=status,
        )

    @staticmethod
    def _build_chunk_rows(
        *,
        source_name: str,
        source_path: str,
        content: str,
        language_code: str | None,
    ) -> list[dict[str, object]]:
        chunks = chunk_text(
            source_name=source_name,
            source_path=source_path,
            content=content,
            language_code=language_code,
        )
        return [_chunk_to_row(chunk) for chunk in chunks]


def _chunk_to_row(chunk: ChunkedKnowledgeDocument) -> dict[str, object]:
    return {
        "chunk_index": chunk.chunk_index,
        "title": chunk.title,
        "content": chunk.content,
        "language_code": chunk.metadata.language_code,
        "module_key": chunk.metadata.module_key,
        "page_id": chunk.metadata.page_id,
        "role_keys": chunk.metadata.role_keys,
        "permission_keys": chunk.metadata.permission_keys,
        "token_count": chunk.metadata.token_count,
    }


def build_default_knowledge_registrations(repo_root: Path) -> list[KnowledgeSourceRegistration]:
    docs_root = repo_root / "docs"
    registrations: list[KnowledgeSourceRegistration] = [
        KnowledgeSourceRegistration(
            source_type="sprint_doc",
            source_name="AI Assistant Sprint Plan",
            source_path=str(docs_root / "sprint" / "AI-Assistant.md"),
        ),
        KnowledgeSourceRegistration(
            source_type="repository_docs",
            source_name="AI Assistant Architecture",
            source_path=str(docs_root / "engineering" / "ai-assistant-architecture.md"),
        ),
        KnowledgeSourceRegistration(
            source_type="repository_docs",
            source_name="AI Assistant Security",
            source_path=str(docs_root / "security" / "ai-assistant-security.md"),
        ),
        KnowledgeSourceRegistration(
            source_type="manual",
            source_name="AI Assistant QA Plan",
            source_path=str(docs_root / "qa" / "ai-assistant-test-plan.md"),
        ),
    ]

    generated_root = repo_root / "tmp" / "assistant-knowledge"
    generated_root.mkdir(parents=True, exist_ok=True)
    page_catalog_path = generated_root / "page-route-catalog.md"
    page_help_path = generated_root / "page-help-manifest.md"
    workflow_path = generated_root / "workflow-help.md"

    page_catalog_lines = ["# Assistant Page Route Catalog", ""]
    for seed in ASSISTANT_PAGE_ROUTE_SEEDS:
        page_catalog_lines.append(
            f"## {seed.page_id} {seed.label}\n\n"
            f"- route_name: {seed.route_name}\n"
            f"- path_template: {seed.path_template}\n"
            f"- module_key: {seed.module_key}\n"
            f"- required_permissions: {', '.join(seed.required_permissions) or 'none'}\n"
        )
    page_catalog_path.write_text("\n".join(page_catalog_lines), encoding="utf-8")

    page_help_lines = ["# Assistant Page Help Manifest", ""]
    for seed in ASSISTANT_PAGE_HELP_SEEDS:
        page_help_lines.append(
            f"## {seed.page_id} {seed.language_code or 'und'}\n\n"
            f"- route_name: {seed.route_name}\n"
            f"- path_template: {seed.path_template}\n"
            f"- module_key: {seed.module_key}\n"
            f"- status: {seed.status}\n"
        )
    page_help_path.write_text("\n".join(page_help_lines), encoding="utf-8")

    workflow_lines = ["# Assistant Workflow Help", ""]
    workflow_lines.append("This generated source summarizes verified workflow seeds used by the assistant.")
    workflow_path.write_text("\n".join(workflow_lines), encoding="utf-8")

    registrations.extend(
        [
            KnowledgeSourceRegistration(
                source_type="repository_docs",
                source_name="Assistant Page Route Catalog",
                source_path=str(page_catalog_path),
            ),
            KnowledgeSourceRegistration(
                source_type="repository_docs",
                source_name="Assistant Page Help Manifest",
                source_path=str(page_help_path),
            ),
            KnowledgeSourceRegistration(
                source_type="repository_docs",
                source_name="Assistant Workflow Help",
                source_path=str(workflow_path),
            ),
        ]
    )
    return registrations
