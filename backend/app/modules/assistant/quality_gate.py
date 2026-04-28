"""Internal RAG quality gate evaluation."""

from __future__ import annotations

from typing import Any

from app.modules.assistant.classifier import is_product_overview_question
from app.modules.assistant.retrieval_planner import FIELD_HELP_INTENT_CATEGORIES
from app.modules.assistant.schemas import (
    AssistantConfidence,
    AssistantRagQualityGateRead,
    AssistantRagTraceRead,
    AssistantStructuredResponse,
)


def evaluate_rag_answer_quality(
    *,
    question: str,
    classification: dict[str, Any] | None,
    response: AssistantStructuredResponse,
    rag_trace: AssistantRagTraceRead | None,
) -> AssistantRagQualityGateRead:
    failures: list[str] = []
    classification_reason = str((classification or {}).get("reason") or "")
    intent_category = str((rag_trace.retrieval_plan if rag_trace is not None else {}).get("intent_category") or "")

    if rag_trace is None or not rag_trace.provider_called:
        failures.append("PROVIDER_NOT_CALLED")
    if rag_trace is None or not rag_trace.retrieval_executed:
        failures.append("RETRIEVAL_NOT_EXECUTED")
    if rag_trace is None or not rag_trace.grounding_attached:
        failures.append("GROUNDING_NOT_ATTACHED")

    if intent_category in {"workflow_how_to", "ui_action_question"} | FIELD_HELP_INTENT_CATEGORIES and (
        rag_trace is None or rag_trace.content_bearing_source_count <= 0
    ):
        failures.append("NO_CONTENT_BEARING_SOURCES")

    if not response.out_of_scope and _needs_source_basis(response.answer) and not response.source_basis:
        failures.append("NO_SOURCE_BASIS")

    if is_product_overview_question(question) and response.out_of_scope:
        failures.append("OVERVIEW_OUT_OF_SCOPE")
    if classification_reason == "product_overview" and response.out_of_scope:
        failures.append("OVERVIEW_OUT_OF_SCOPE")

    if _mentions_precise_ui_claim(response.answer) and not any(
        item.source_type == "page_help_manifest" for item in response.source_basis
    ):
        failures.append("UNVERIFIED_EXACT_UI_CLAIM")

    if (
        rag_trace is not None
        and "content_bearing_sources" in rag_trace.missing_context
        and response.confidence != AssistantConfidence.LOW
    ):
        failures.append("MISSING_CONTEXT_NOT_LOW_CONFIDENCE")

    if (
        rag_trace is not None
        and "content_bearing_sources" in rag_trace.missing_context
        and not _states_missing_context(response.answer)
    ):
        failures.append("MISSING_CONTEXT_NOT_DISCLOSED")

    return AssistantRagQualityGateRead(
        passed=not failures,
        failures=failures,
    )


def _needs_source_basis(answer: str) -> bool:
    return len(answer.strip()) >= 40


def _mentions_precise_ui_claim(answer: str) -> bool:
    lowered = answer.casefold()
    tokens = (
        "exact button",
        "button label",
        "exact label",
        "exact current ui label",
        "schaltfläche",
        "genaue bezeichnung",
        "exakte bezeichnung",
    )
    return any(token in lowered for token in tokens)


def _states_missing_context(answer: str) -> bool:
    lowered = answer.casefold()
    tokens = (
        "not verified",
        "cannot confirm",
        "missing",
        "need more context",
        "nicht verifiziert",
        "nicht bestätigt",
        "kann ich nicht bestätigen",
        "mehr kontext",
    )
    return any(token in lowered for token in tokens)
