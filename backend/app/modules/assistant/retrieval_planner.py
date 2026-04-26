"""Deterministic retrieval planning for assistant grounding."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.assistant.diagnostics import is_shift_visibility_question
from app.modules.assistant.lexicon import expand_assistant_query
from app.modules.assistant.page_help import detect_ui_howto_intent
from app.modules.assistant.workflow_help import WORKFLOW_HELP_SEEDS, detect_workflow_intent


@dataclass(frozen=True)
class AssistantRetrievalPlan:
    intent_category: str
    workflow_intent: str | None = None
    ui_intent: str | None = None
    expanded_query: str | None = None
    concept_keys: tuple[str, ...] = ()
    likely_page_ids: tuple[str, ...] = ()
    likely_module_keys: tuple[str, ...] = ()
    required_sources: tuple[str, ...] = ()
    needs_diagnostics: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_category": self.intent_category,
            "workflow_intent": self.workflow_intent,
            "ui_intent": self.ui_intent,
            "expanded_query": self.expanded_query,
            "concept_keys": list(self.concept_keys),
            "likely_page_ids": list(self.likely_page_ids),
            "likely_module_keys": list(self.likely_module_keys),
            "required_sources": list(self.required_sources),
            "needs_diagnostics": self.needs_diagnostics,
        }


def build_retrieval_plan(
    *,
    message: str,
    route_context: dict[str, Any] | None,
) -> AssistantRetrievalPlan:
    workflow_intent = detect_workflow_intent(message)
    ui_intent = detect_ui_howto_intent(message)
    needs_diagnostics = is_shift_visibility_question(message, route_context)
    expanded_query = expand_assistant_query(
        message,
        workflow_intent=workflow_intent.intent if workflow_intent is not None else None,
        ui_page_id=ui_intent.page_id if ui_intent is not None else None,
    )

    likely_page_ids: list[str] = list(expanded_query.page_hints)
    likely_module_keys: list[str] = list(expanded_query.module_hints)
    required_sources: list[str] = ["auth_context", "current_route"]

    if workflow_intent is not None:
        seed = WORKFLOW_HELP_SEEDS.get(workflow_intent.intent)
        if seed is not None:
            likely_page_ids.extend(seed.linked_page_ids)
            for page_id in seed.linked_page_ids:
                likely_module_keys.append(_module_key_for_page_id(page_id))
        required_sources.extend(["workflow_help", "page_route_catalog", "knowledge_chunks"])
        if ui_intent is None:
            required_sources.append("page_help_manifest")

    if ui_intent is not None:
        likely_page_ids.append(ui_intent.page_id)
        likely_module_keys.append(_module_key_for_page_id(ui_intent.page_id))
        required_sources.extend(["ui_action_catalog", "page_help_manifest", "page_route_catalog"])

    if needs_diagnostics:
        required_sources.extend(["operational_diagnostics", "knowledge_chunks"])
        likely_page_ids.extend(["E-01", "P-03", "P-04", "P-05", "ES-01"])
        likely_module_keys.extend(["employees", "planning"])

    route_page_id = None
    if route_context is not None and isinstance(route_context.get("page_id"), str):
        route_page_id = str(route_context["page_id"]).strip() or None
    if (
        route_page_id is not None
        and workflow_intent is None
        and ui_intent is None
        and not needs_diagnostics
    ):
        likely_page_ids.append(route_page_id)
        likely_module_keys.append(_module_key_for_page_id(route_page_id))

    intent_category = "unknown_platform_related"
    if needs_diagnostics:
        intent_category = "operational_diagnostic"
    elif ui_intent is not None:
        intent_category = "ui_action_question"
    elif workflow_intent is not None:
        intent_category = "workflow_how_to"
    elif route_page_id is not None:
        intent_category = "navigation_question"
        required_sources.extend(["page_route_catalog", "knowledge_chunks"])
    else:
        required_sources.append("knowledge_chunks")

    return AssistantRetrievalPlan(
        intent_category=intent_category,
        workflow_intent=workflow_intent.intent if workflow_intent is not None else None,
        ui_intent=ui_intent.intent if ui_intent is not None else None,
        expanded_query=expanded_query.expanded_query,
        concept_keys=expanded_query.concept_keys,
        likely_page_ids=tuple(_dedupe_preserve_order(likely_page_ids)),
        likely_module_keys=tuple(_dedupe_preserve_order([key for key in likely_module_keys if key])),
        required_sources=tuple(_dedupe_preserve_order(required_sources)),
        needs_diagnostics=needs_diagnostics,
    )


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def _module_key_for_page_id(page_id: str) -> str:
    if page_id.startswith("PS"):
        return "platform_services"
    if page_id.startswith("E"):
        return "employees"
    if page_id.startswith("P") or page_id.startswith("FD"):
        return "planning"
    if page_id.startswith("C"):
        return "customers"
    if page_id.startswith("FI"):
        return "finance"
    if page_id.startswith("S"):
        return "subcontractors"
    return "platform"
