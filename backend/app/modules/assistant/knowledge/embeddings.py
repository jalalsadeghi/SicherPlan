"""Optional embedding retrieval interface for assistant knowledge search."""

from __future__ import annotations

from typing import Protocol

from app.modules.assistant.schemas import AssistantKnowledgeChunkResult


class AssistantEmbeddingRetriever(Protocol):
    def retrieve(
        self,
        *,
        query: str,
        language_code: str | None = None,
        module_key: str | None = None,
        page_id: str | None = None,
        role_keys: list[str] | None = None,
        permission_keys: list[str] | None = None,
        source_type: str | None = None,
        limit: int = 8,
    ) -> list[AssistantKnowledgeChunkResult]: ...


class NoopAssistantEmbeddingRetriever:
    """Non-breaking default while the repo has no pgvector-backed retrieval path."""

    def retrieve(
        self,
        *,
        query: str,
        language_code: str | None = None,
        module_key: str | None = None,
        page_id: str | None = None,
        role_keys: list[str] | None = None,
        permission_keys: list[str] | None = None,
        source_type: str | None = None,
        limit: int = 8,
    ) -> list[AssistantKnowledgeChunkResult]:
        del query, language_code, module_key, page_id, role_keys, permission_keys, source_type, limit
        return []
