"""Runtime retrieval for indexed assistant knowledge chunks."""

from __future__ import annotations

from collections import Counter
import re
from typing import Protocol

from app.modules.assistant.knowledge.embeddings import (
    AssistantEmbeddingRetriever,
    NoopAssistantEmbeddingRetriever,
)
from app.modules.assistant.knowledge.types import (
    DEFAULT_MAX_CHUNK_CHARS,
    KnowledgeChunkCandidate,
)
from app.modules.assistant.schemas import AssistantKnowledgeChunkResult


TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
WHITESPACE_RE = re.compile(r"\s+")


class AssistantKnowledgeRetrieverRepository(Protocol):
    def list_active_chunk_candidates(
        self,
        *,
        source_type: str | None = None,
        candidate_limit: int = 200,
    ) -> list[KnowledgeChunkCandidate]: ...


class AssistantKnowledgeRetriever:
    def __init__(
        self,
        *,
        repository: AssistantKnowledgeRetrieverRepository,
        embedding_retriever: AssistantEmbeddingRetriever | None = None,
        max_context_chunks: int = 8,
        max_input_chars: int = 12000,
    ) -> None:
        self.repository = repository
        self.embedding_retriever = embedding_retriever or NoopAssistantEmbeddingRetriever()
        self.max_context_chunks = max(int(max_context_chunks), 1)
        self.max_input_chars = max(int(max_input_chars), 60)

    def retrieve_knowledge_chunks(
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
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        capped_limit = min(max(int(limit), 1), self.max_context_chunks)
        candidate_limit = max(capped_limit * 12, 50)
        candidates = self.repository.list_active_chunk_candidates(
            source_type=source_type,
            candidate_limit=candidate_limit,
        )
        lexical_results = self._score_lexical_candidates(
            candidates,
            query=cleaned_query,
            language_code=language_code,
            module_key=module_key,
            page_id=page_id,
            role_keys=role_keys or [],
            permission_keys=permission_keys or [],
            source_type=source_type,
            limit=capped_limit,
        )
        vector_results = self.embedding_retriever.retrieve(
            query=cleaned_query,
            language_code=language_code,
            module_key=module_key,
            page_id=page_id,
            role_keys=role_keys or [],
            permission_keys=permission_keys or [],
            source_type=source_type,
            limit=capped_limit,
        )
        return self._merge_results(lexical_results, vector_results, limit=capped_limit)

    def _score_lexical_candidates(
        self,
        candidates: list[KnowledgeChunkCandidate],
        *,
        query: str,
        language_code: str | None,
        module_key: str | None,
        page_id: str | None,
        role_keys: list[str],
        permission_keys: list[str],
        source_type: str | None,
        limit: int,
    ) -> list[AssistantKnowledgeChunkResult]:
        normalized_query = _normalize_text(query)
        query_tokens = Counter(_tokenize(normalized_query))
        if not query_tokens and not page_id and not module_key:
            return []

        scored: list[tuple[float, KnowledgeChunkCandidate, str]] = []
        for candidate in candidates:
            score, matched_by = _score_candidate(
                candidate,
                normalized_query=normalized_query,
                query_tokens=query_tokens,
                language_code=language_code,
                module_key=module_key,
                page_id=page_id,
                role_keys=role_keys,
                permission_keys=permission_keys,
                source_type=source_type,
            )
            if score <= 0:
                continue
            scored.append((score, candidate, matched_by))

        scored.sort(
            key=lambda item: (
                -item[0],
                item[1].source_name.casefold(),
                item[1].source_path.casefold(),
                item[1].chunk_index,
                item[1].chunk_id,
            )
        )
        max_chunk_chars = max(60, min(DEFAULT_MAX_CHUNK_CHARS, self.max_input_chars // max(limit, 1)))
        results: list[AssistantKnowledgeChunkResult] = []
        for rank, (score, candidate, matched_by) in enumerate(scored[:limit], start=1):
            results.append(
                AssistantKnowledgeChunkResult(
                    chunk_id=candidate.chunk_id,
                    source_id=candidate.source_id,
                    source_name=candidate.source_name,
                    source_type=candidate.source_type,
                    title=candidate.title,
                    content=_truncate_text(candidate.content, max_chunk_chars),
                    language_code=candidate.language_code,
                    module_key=candidate.module_key,
                    page_id=candidate.page_id,
                    role_keys=list(candidate.role_keys),
                    permission_keys=list(candidate.permission_keys),
                    score=round(score, 4),
                    rank=rank,
                    matched_by=matched_by,
                )
            )
        return results

    @staticmethod
    def _merge_results(
        lexical_results: list[AssistantKnowledgeChunkResult],
        vector_results: list[AssistantKnowledgeChunkResult],
        *,
        limit: int,
    ) -> list[AssistantKnowledgeChunkResult]:
        merged: dict[str, AssistantKnowledgeChunkResult] = {
            item.chunk_id: item for item in lexical_results
        }
        for vector_item in vector_results:
            existing = merged.get(vector_item.chunk_id)
            if existing is None:
                merged[vector_item.chunk_id] = vector_item
                continue
            merged[vector_item.chunk_id] = existing.model_copy(
                update={
                    "score": round(existing.score + vector_item.score, 4),
                    "matched_by": "hybrid",
                }
            )

        ordered = sorted(
            merged.values(),
            key=lambda item: (
                -item.score,
                item.source_name.casefold(),
                item.chunk_id,
            ),
        )[:limit]
        return [
            item.model_copy(update={"rank": index})
            for index, item in enumerate(ordered, start=1)
        ]


def _score_candidate(
    candidate: KnowledgeChunkCandidate,
    *,
    normalized_query: str,
    query_tokens: Counter[str],
    language_code: str | None,
    module_key: str | None,
    page_id: str | None,
    role_keys: list[str],
    permission_keys: list[str],
    source_type: str | None,
) -> tuple[float, str]:
    title_text = _normalize_text(candidate.title or "")
    content_text = _normalize_text(candidate.content)
    combined_text = f"{title_text}\n{content_text}".strip()
    combined_tokens = Counter(_tokenize(combined_text))
    title_tokens = Counter(_tokenize(title_text))

    overlap = sum(min(count, combined_tokens.get(token, 0)) for token, count in query_tokens.items())
    title_overlap = sum(min(count, title_tokens.get(token, 0)) for token, count in query_tokens.items())
    unique_overlap = len(set(query_tokens).intersection(combined_tokens))

    score = 0.0
    matched_by = "metadata"

    if overlap:
        score += overlap * 5.0
        matched_by = "lexical"
    if unique_overlap:
        score += unique_overlap * 2.0
    if title_overlap:
        score += title_overlap * 6.0
        matched_by = "lexical"
    if normalized_query and normalized_query in content_text:
        score += 18.0
        matched_by = "lexical"
    if normalized_query and normalized_query in title_text:
        score += 24.0
        matched_by = "lexical"

    if page_id is not None and candidate.page_id == page_id:
        score += 20.0
    if module_key is not None and candidate.module_key == module_key:
        score += 12.0
    if source_type is not None and candidate.source_type == source_type:
        score += 4.0
    if language_code is not None:
        if candidate.language_code == language_code:
            score += 8.0
        elif candidate.language_code == "en":
            score += 2.0
        elif candidate.language_code is None:
            score += 1.0

    if role_keys and set(role_keys).intersection(candidate.role_keys):
        score += 1.5
    if permission_keys and set(permission_keys).intersection(candidate.permission_keys):
        score += 1.5

    return score, matched_by


def _normalize_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value.casefold()).strip()


def _tokenize(value: str) -> list[str]:
    return TOKEN_RE.findall(value)


def _truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."
