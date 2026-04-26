"""Repository layer for assistant knowledge source and chunk persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.assistant.knowledge.types import KnowledgeChunkCandidate
from app.modules.assistant.models import AssistantKnowledgeChunk, AssistantKnowledgeSource


class AssistantKnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_active_source_by_path_hash(self, *, source_path: str, source_hash: str) -> AssistantKnowledgeSource | None:
        statement = (
            select(AssistantKnowledgeSource)
            .where(
                AssistantKnowledgeSource.source_path == source_path,
                AssistantKnowledgeSource.source_hash == source_hash,
                AssistantKnowledgeSource.status == "active",
            )
            .order_by(AssistantKnowledgeSource.updated_at.desc())
        )
        return self.session.scalars(statement).first()

    def find_latest_source_by_path(self, *, source_path: str) -> AssistantKnowledgeSource | None:
        statement = (
            select(AssistantKnowledgeSource)
            .where(AssistantKnowledgeSource.source_path == source_path)
            .order_by(AssistantKnowledgeSource.updated_at.desc())
        )
        return self.session.scalars(statement).first()

    def upsert_source(
        self,
        *,
        existing_source: AssistantKnowledgeSource | None,
        source_type: str,
        source_name: str,
        source_path: str,
        source_hash: str,
        source_version: str | None,
        status: str,
    ) -> AssistantKnowledgeSource:
        now = datetime.now(UTC)
        source = existing_source or AssistantKnowledgeSource(
            source_type=source_type,
            source_name=source_name,
            source_path=source_path,
            source_hash=source_hash,
            source_version=source_version,
            status=status,
            last_ingested_at=now,
        )
        source.source_type = source_type
        source.source_name = source_name
        source.source_path = source_path
        source.source_hash = source_hash
        source.source_version = source_version
        source.status = status
        source.last_ingested_at = now
        self.session.add(source)
        self.session.flush()
        return source

    def replace_chunks(
        self,
        *,
        source: AssistantKnowledgeSource,
        chunks: list[dict[str, object]],
    ) -> None:
        self.session.execute(
            delete(AssistantKnowledgeChunk).where(AssistantKnowledgeChunk.source_id == source.id)
        )
        for chunk in chunks:
            row = AssistantKnowledgeChunk(
                source_id=source.id,
                chunk_index=int(chunk["chunk_index"]),
                title=chunk["title"],
                content=str(chunk["content"]),
                language_code=chunk["language_code"],
                module_key=chunk["module_key"],
                page_id=chunk["page_id"],
                role_keys=chunk["role_keys"],
                permission_keys=chunk["permission_keys"],
                embedding=None,
                token_count=chunk["token_count"],
            )
            self.session.add(row)
        self.session.flush()

    def list_active_chunk_candidates(
        self,
        *,
        source_type: str | None = None,
        candidate_limit: int = 200,
    ) -> list[KnowledgeChunkCandidate]:
        statement = (
            select(AssistantKnowledgeChunk, AssistantKnowledgeSource)
            .join(
                AssistantKnowledgeSource,
                AssistantKnowledgeChunk.source_id == AssistantKnowledgeSource.id,
            )
            .where(AssistantKnowledgeSource.status == "active")
            .order_by(
                AssistantKnowledgeSource.source_name.asc(),
                AssistantKnowledgeSource.source_path.asc(),
                AssistantKnowledgeChunk.chunk_index.asc(),
            )
            .limit(max(int(candidate_limit), 1))
        )
        if source_type is not None:
            statement = statement.where(AssistantKnowledgeSource.source_type == source_type)

        rows: Iterable[tuple[AssistantKnowledgeChunk, AssistantKnowledgeSource]] = self.session.execute(statement).all()
        return [self._to_candidate(chunk, source) for chunk, source in rows]

    @staticmethod
    def _to_candidate(
        chunk: AssistantKnowledgeChunk,
        source: AssistantKnowledgeSource,
    ) -> KnowledgeChunkCandidate:
        return KnowledgeChunkCandidate(
            chunk_id=chunk.id,
            source_id=source.id,
            source_name=source.source_name,
            source_type=source.source_type,
            source_path=source.source_path,
            chunk_index=chunk.chunk_index,
            title=chunk.title,
            content=chunk.content,
            language_code=chunk.language_code,
            module_key=chunk.module_key,
            page_id=chunk.page_id,
            role_keys=list(chunk.role_keys or []),
            permission_keys=list(chunk.permission_keys or []),
            token_count=chunk.token_count,
        )
