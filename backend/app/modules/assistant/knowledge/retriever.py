"""Runtime retrieval for indexed assistant knowledge chunks."""

from __future__ import annotations

from collections import Counter
import re
from typing import Protocol

from app.modules.assistant.knowledge.embeddings import (
    AssistantEmbeddingRetriever,
    NoopAssistantEmbeddingRetriever,
)
from app.modules.assistant.lexicon import expand_query_for_retrieval
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
        expanded_query = expand_query_for_retrieval(
            cleaned_query,
            language_code,
            workflow_intent=workflow_intent,
            ui_page_id=page_id,
        )

        capped_limit = min(max(int(limit), 1), self.max_context_chunks)
        candidate_limit = max(capped_limit * 40, 200)
        candidates = self.repository.list_active_chunk_candidates(
            source_type=source_type,
            candidate_limit=candidate_limit,
        )
        lexical_results = self._score_lexical_candidates(
            candidates,
            query=cleaned_query,
            expanded_query=expanded_query.expanded_query,
            workflow_intent=workflow_intent,
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
        workflow_intent: str | None,
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
                workflow_intent=workflow_intent,
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
                    source_path=candidate.source_path,
                    source_language=candidate.source_language,
                    title=candidate.title,
                    content=_truncate_text(candidate.content, max_chunk_chars),
                    content_preview=candidate.content_preview or _truncate_text(candidate.content, 180),
                    language_code=candidate.language_code,
                    module_key=candidate.module_key,
                    page_id=candidate.page_id,
                    workflow_keys=list(candidate.workflow_keys or []),
                    role_keys=list(candidate.role_keys),
                    permission_keys=list(candidate.permission_keys),
                    api_families=list(candidate.api_families or []),
                    domain_terms=list(candidate.domain_terms or []),
                    language_aliases=list(candidate.language_aliases or []),
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
    workflow_intent: str | None,
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
    alias_text = _normalize_text(" ".join(candidate.language_aliases or []))
    domain_text = _normalize_text(" ".join(candidate.domain_terms or []))
    combined_text = f"{title_text}\n{content_text}\n{alias_text}\n{domain_text}".strip()
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
    if workflow_intent:
        if workflow_intent in set(candidate.workflow_keys or []):
            score += 35.0
        elif candidate.workflow_keys:
            score -= 18.0
    if alias_text:
        alias_tokens = Counter(_tokenize(alias_text))
        alias_overlap = sum(min(count, alias_tokens.get(token, 0)) for token, count in expanded_query_tokens.items())
        score += alias_overlap * 3.5
    if domain_text:
        domain_tokens = Counter(_tokenize(domain_text))
        domain_overlap = sum(min(count, domain_tokens.get(token, 0)) for token, count in expanded_query_tokens.items())
        score += domain_overlap * 2.5

    if page_id is not None and candidate.page_id == page_id:
        score += 20.0
    if page_ids and candidate.page_id in page_ids:
        score += 18.0
    elif page_ids and candidate.page_id is not None:
        score -= 16.0
    if module_key is not None and candidate.module_key == module_key:
        score += 12.0
    if module_keys and candidate.module_key in module_keys:
        score += 10.0
    elif module_keys and candidate.module_key is not None:
        score -= 14.0
    if source_type is not None and candidate.source_type == source_type:
        score += 4.0
    score += _source_type_boost(candidate.source_type)
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

    score += _workflow_specific_source_adjustments(
        candidate=candidate,
        normalized_query=normalized_query,
        workflow_intent=workflow_intent,
    )
    score += _intent_page_demotions(
        candidate=candidate,
        normalized_query=normalized_query,
        workflow_intent=workflow_intent,
        page_ids=page_ids,
        module_keys=module_keys,
    )

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


def _source_type_boost(source_type: str) -> float:
    boosts = {
        "platform_term_dictionary": 9.75,
        "field_dictionary": 9.5,
        "lookup_dictionary": 9.0,
        "status_dictionary": 8.5,
        "form_field_catalog": 8.5,
        "api_schema_field": 7.0,
        "frontend_i18n_label": 6.5,
        "expert_knowledge_pack": 9.5,
        "ui_action_catalog": 9.0,
        "page_help_manifest": 9.0,
        "workflow_help": 8.0,
        "operational_handbook": 7.0,
        "user_manual": 7.0,
        "implementation_data_model": 5.0,
        "engineering_doc": 4.0,
        "security_doc": 3.5,
        "runbook": 3.0,
        "api_export": 2.0,
        "repository_docs": 3.0,
        "manual": 3.0,
        "sprint_doc": 2.0,
        "role_page_coverage": 2.0,
        "api_endpoint_map": 1.5,
        "page_route_catalog": 1.0,
    }
    return boosts.get(source_type, 0.0)


def _intent_page_demotions(
    *,
    candidate: KnowledgeChunkCandidate,
    normalized_query: str,
    workflow_intent: str | None,
    page_ids: list[str],
    module_keys: list[str],
) -> float:
    if candidate.page_id == "F-02" and "dashboard" not in normalized_query and "kpi" not in normalized_query:
        if "F-02" not in page_ids and "dashboard" not in module_keys:
            return -14.0
    if candidate.page_id == "E-01":
        employee_terms = ("employee", "mitarbeiter", "کارمند", "guard", "hr", "personal")
        if workflow_intent not in {"employee_create", "employee_assign_to_shift", "employee_assign_to_shift_workflow"} and not any(
            term in normalized_query for term in employee_terms
        ):
            if "E-01" not in page_ids and "employees" not in module_keys:
                return -12.0
    if candidate.page_id == "P-02" and workflow_intent == "customer_scoped_order_create":
        canonical_terms = (
            "manage all orders",
            "all orders",
            "orders & planning records",
            "orders and planning records",
            "alle aufträge",
            "wie verwalte ich alle aufträge",
        )
        if not any(term in normalized_query for term in canonical_terms):
            return -10.0
    return 0.0


def _workflow_specific_source_adjustments(
    *,
    candidate: KnowledgeChunkCandidate,
    normalized_query: str,
    workflow_intent: str | None,
) -> float:
    if workflow_intent != "customer_scoped_order_create":
        return 0.0

    boost = 0.0
    source_haystack = " ".join(
        item.casefold()
        for item in (
            candidate.source_name,
            candidate.source_path or "",
            candidate.title or "",
        )
        if item
    )
    preferred_markers = (
        "customerorderstab.vue",
        "customerorderstab",
        "new-plan.vue",
        "new-plan-step-content.vue",
        "new-plan-wizard.steps.ts",
        "planningorders.ts",
        "planningshifts.ts",
        "spr-cust-newplan-v1",
        "customer orders tab",
        "customer order workspace",
    )
    if candidate.page_id in {"C-01", "C-02", "P-04"}:
        boost += 9.0
    if any(marker in source_haystack for marker in preferred_markers):
        boost += 16.0
    if candidate.source_type in {"workflow_help", "page_help_manifest", "expert_knowledge_pack"}:
        boost += 4.0
    if candidate.page_id == "P-02" and not any(
        term in normalized_query
        for term in ("manage all orders", "all orders", "orders & planning records", "alle aufträge")
    ):
        boost -= 8.0
    return boost
