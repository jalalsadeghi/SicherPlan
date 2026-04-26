"""Runtime retrieval for indexed assistant knowledge chunks."""

from __future__ import annotations

from collections import Counter
import re
from typing import Protocol

from app.modules.assistant.knowledge.embeddings import (
    AssistantEmbeddingRetriever,
    NoopAssistantEmbeddingRetriever,
)
from app.modules.assistant.lexicon import expand_assistant_query
from app.modules.assistant.knowledge.types import (
    DEFAULT_MAX_CHUNK_CHARS,
    KnowledgeChunkCandidate,
)
from app.modules.assistant.schemas import AssistantKnowledgeChunkResult


TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
WHITESPACE_RE = re.compile(r"\s+")
STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "for", "of", "in", "on", "how", "do", "i", "it",
    "wie", "ich", "einen", "eine", "einer", "einem", "eines", "fuer", "für", "und", "der", "die", "das", "den", "dem",
    "چطور", "چطوری", "میتونم", "میتوانم", "باید", "یک", "جدید", "را", "برای", "کنم", "شود", "است", "از", "در",
}


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
        retrieval_mode: str = "lexical",
        embeddings_enabled: bool = False,
        max_context_chunks: int = 8,
        max_input_chars: int = 12000,
    ) -> None:
        self.repository = repository
        self.embedding_retriever = embedding_retriever or NoopAssistantEmbeddingRetriever()
        self.retrieval_mode = retrieval_mode
        self.embeddings_enabled = embeddings_enabled
        self.max_context_chunks = max(int(max_context_chunks), 1)
        self.max_input_chars = max(int(max_input_chars), 60)

    @property
    def effective_retrieval_mode(self) -> str:
        if self.retrieval_mode in {"semantic", "hybrid"} and self.embeddings_enabled:
            return self.retrieval_mode
        return "lexical"

    def retrieve_knowledge_chunks(
        self,
        *,
        query: str,
        language_code: str | None = None,
        module_key: str | None = None,
        page_id: str | None = None,
        module_keys: list[str] | None = None,
        page_ids: list[str] | None = None,
        workflow_intent: str | None = None,
        role_keys: list[str] | None = None,
        permission_keys: list[str] | None = None,
        source_type: str | None = None,
        limit: int = 8,
    ) -> list[AssistantKnowledgeChunkResult]:
        cleaned_query = query.strip()
        if not cleaned_query:
            return []
        expanded_query = expand_assistant_query(
            cleaned_query,
            workflow_intent=workflow_intent,
            ui_page_id=page_id,
        )

        capped_limit = min(max(int(limit), 1), self.max_context_chunks)
        candidate_limit = max(capped_limit * 12, 50)
        candidates = self.repository.list_active_chunk_candidates(
            source_type=source_type,
            candidate_limit=candidate_limit,
        )
        lexical_results = self._score_lexical_candidates(
            candidates,
            query=cleaned_query,
            expanded_query=expanded_query.expanded_query,
            language_code=language_code,
            module_key=module_key,
            page_id=page_id,
            module_keys=module_keys or [],
            page_ids=page_ids or [],
            role_keys=role_keys or [],
            permission_keys=permission_keys or [],
            source_type=source_type,
            limit=capped_limit,
        )
        vector_results: list[AssistantKnowledgeChunkResult] = []
        if self.effective_retrieval_mode in {"semantic", "hybrid"}:
            vector_results = self.embedding_retriever.retrieve(
                query=expanded_query.expanded_query,
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
        expanded_query: str,
        language_code: str | None,
        module_key: str | None,
        page_id: str | None,
        module_keys: list[str],
        page_ids: list[str],
        role_keys: list[str],
        permission_keys: list[str],
        source_type: str | None,
        limit: int,
    ) -> list[AssistantKnowledgeChunkResult]:
        normalized_query = _normalize_text(query)
        normalized_expanded_query = _normalize_text(expanded_query)
        query_tokens = Counter(_tokenize(normalized_query))
        expanded_query_tokens = Counter(_tokenize(normalized_expanded_query))
        all_page_ids = _dedupe_list([*(page_ids or []), page_id] if page_id else list(page_ids or []))
        all_module_keys = _dedupe_list([*(module_keys or []), module_key] if module_key else list(module_keys or []))
        if not expanded_query_tokens and not all_page_ids and not all_module_keys:
            return []

        scored: list[tuple[float, KnowledgeChunkCandidate, str]] = []
        for candidate in candidates:
            score, matched_by = _score_candidate(
                candidate,
                normalized_query=normalized_query,
                normalized_expanded_query=normalized_expanded_query,
                query_tokens=query_tokens,
                expanded_query_tokens=expanded_query_tokens,
                language_code=language_code,
                module_key=module_key,
                page_id=page_id,
                module_keys=all_module_keys,
                page_ids=all_page_ids,
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
    normalized_expanded_query: str,
    query_tokens: Counter[str],
    expanded_query_tokens: Counter[str],
    language_code: str | None,
    module_key: str | None,
    page_id: str | None,
    module_keys: list[str],
    page_ids: list[str],
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
    expanded_overlap = sum(min(count, combined_tokens.get(token, 0)) for token, count in expanded_query_tokens.items())
    expanded_title_overlap = sum(min(count, title_tokens.get(token, 0)) for token, count in expanded_query_tokens.items())
    unique_overlap = len(set(expanded_query_tokens).intersection(combined_tokens))

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
    if expanded_overlap:
        score += expanded_overlap * 2.5
        matched_by = "lexical"
    if expanded_title_overlap:
        score += expanded_title_overlap * 3.0
        matched_by = "lexical"
    if normalized_query and normalized_query in content_text:
        score += 18.0
        matched_by = "lexical"
    if normalized_query and normalized_query in title_text:
        score += 24.0
        matched_by = "lexical"
    if normalized_expanded_query and normalized_expanded_query in content_text:
        score += 8.0
    if normalized_expanded_query and normalized_expanded_query in title_text:
        score += 10.0

    if page_id is not None and candidate.page_id == page_id:
        score += 20.0
    if page_ids and candidate.page_id in page_ids:
        score += 18.0
    elif page_ids and candidate.page_id is not None:
        score -= 8.0
    if module_key is not None and candidate.module_key == module_key:
        score += 12.0
    if module_keys and candidate.module_key in module_keys:
        score += 10.0
    elif module_keys and candidate.module_key is not None:
        score -= 8.0
    if source_type is not None and candidate.source_type == source_type:
        score += 4.0
    if candidate.source_type in {"manual", "repository_docs", "sprint_doc"}:
        score += 2.0
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

    preferred_page_match = bool(page_ids and candidate.page_id in page_ids)
    preferred_module_match = bool(module_keys and candidate.module_key in module_keys)
    if (
        (page_ids or module_keys)
        and not preferred_page_match
        and not preferred_module_match
        and score < 15.0
    ):
        return 0.0, matched_by

    return score, matched_by


def _normalize_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value.casefold()).strip()


def _tokenize(value: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(value) if token not in STOPWORDS]


def _truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


def _dedupe_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result
