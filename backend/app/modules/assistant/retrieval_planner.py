"""Deterministic retrieval planning for assistant grounding."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.assistant.classifier import is_product_overview_question
from app.modules.assistant.diagnostic_prefetch import plan_diagnostic_prefetch
from app.modules.assistant.diagnostics import is_shift_visibility_question
from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal, detect_platform_term_signal
from app.modules.assistant.lexicon import expand_assistant_query
from app.modules.assistant.page_help import detect_ui_howto_intent
from app.modules.assistant.workflow_help import WORKFLOW_HELP_SEEDS, detect_workflow_intent

FIELD_HELP_INTENT_CATEGORIES = {
    "field_meaning_question",
    "lookup_meaning_question",
    "status_meaning_question",
    "form_help_question",
    "column_meaning_question",
    "tab_action_label_question",
    "platform_term_meaning_question",
    "ui_label_meaning_question",
    "domain_concept_question",
    "section_title_question",
    "action_label_question",
    "validation_rule_meaning_question",
    "status_or_option_meaning_question",
}


@dataclass(frozen=True)
class AssistantRetrievalPlan:
    intent_category: str
    workflow_intent: str | None = None
    workflow_variant: str | None = None
    ui_intent: str | None = None
    diagnostic_intent: str | None = None
    expanded_query: str | None = None
    detected_terms: tuple[str, ...] = ()
    expanded_terms_en: tuple[str, ...] = ()
    expanded_terms_de: tuple[str, ...] = ()
    concept_keys: tuple[str, ...] = ()
    likely_page_ids: tuple[str, ...] = ()
    likely_module_keys: tuple[str, ...] = ()
    required_sources: tuple[str, ...] = ()
    needs_diagnostics: bool = False
    diagnostic_missing_inputs: tuple[str, ...] = ()
    diagnostic_checks_missing_input: tuple[str, ...] = ()
    route_context_signals: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_category": self.intent_category,
            "workflow_intent": self.workflow_intent,
            "workflow_variant": self.workflow_variant,
            "ui_intent": self.ui_intent,
            "diagnostic_intent": self.diagnostic_intent,
            "expanded_query": self.expanded_query,
            "detected_terms": list(self.detected_terms),
            "expanded_terms_en": list(self.expanded_terms_en),
            "expanded_terms_de": list(self.expanded_terms_de),
            "concept_keys": list(self.concept_keys),
            "likely_page_ids": list(self.likely_page_ids),
            "likely_module_keys": list(self.likely_module_keys),
            "required_sources": list(self.required_sources),
            "needs_diagnostics": self.needs_diagnostics,
            "diagnostic_missing_inputs": list(self.diagnostic_missing_inputs),
            "diagnostic_checks_missing_input": list(self.diagnostic_checks_missing_input),
            "route_context_signals": dict(self.route_context_signals),
        }


def extract_route_context_signals(route_context: dict[str, Any] | None) -> dict[str, Any]:
    query = route_context.get("query") if isinstance(route_context, dict) else None
    if not isinstance(query, dict):
        query = {}
    path = str((route_context or {}).get("path") or "").strip()
    route_name = str((route_context or {}).get("route_name") or "").strip()
    page_id = str((route_context or {}).get("page_id") or "").strip()

    customer_id = _route_query_string(query.get("customer_id"))
    order_id = _route_query_string(query.get("order_id"))
    planning_record_id = _route_query_string(query.get("planning_record_id"))
    shift_plan_id = _route_query_string(query.get("shift_plan_id"))
    date_value = _route_query_string(query.get("date"))
    tab = _route_query_string(query.get("tab"))

    customer_orders_tab = page_id == "C-01" and tab == "orders"
    customer_workspace_selected = page_id == "C-01" and customer_id is not None
    customer_order_workspace = page_id == "C-02" or path == "/admin/customers/order-workspace" or route_name == "SicherPlanCustomerOrderWorkspace"

    return {
        "page_id": page_id or None,
        "path": path or None,
        "route_name": route_name or None,
        "customer_id": customer_id,
        "order_id": order_id,
        "planning_record_id": planning_record_id,
        "shift_plan_id": shift_plan_id,
        "date": date_value,
        "tab": tab,
        "customer_orders_tab": customer_orders_tab,
        "customer_workspace_selected": customer_workspace_selected,
        "customer_order_workspace": customer_order_workspace,
        "customer_context_active": bool(customer_id and (page_id in {"C-01", "C-02"} or customer_order_workspace)),
    }


def build_retrieval_plan(
    *,
    message: str,
    route_context: dict[str, Any] | None,
) -> AssistantRetrievalPlan:
    lowered = message.strip().casefold()
    route_signals = extract_route_context_signals(route_context)
    workflow_intent = detect_workflow_intent(message)
    workflow_variant = _detect_customer_scoped_order_variant(lowered, route_signals)
    if _should_promote_to_customer_scoped_order(
        lowered=lowered,
        route_signals=route_signals,
        workflow_intent=workflow_intent.intent if workflow_intent is not None else None,
    ):
        workflow_intent = detect_workflow_intent("create order from customer page")
        workflow_variant = workflow_variant or "customer_order_from_customer_page"
    ui_intent = detect_ui_howto_intent(message)
    product_overview = is_product_overview_question(message)
    diagnostic_prefetch = plan_diagnostic_prefetch(
        message=message,
        detected_language="unknown",
        route_context=route_context,
    )
    field_lookup_signal = detect_field_or_lookup_signal(
        message,
        page_id=route_signals.get("page_id"),
        route_name=route_signals.get("route_name"),
    )
    platform_term_signal = detect_platform_term_signal(
        message,
        page_id=route_signals.get("page_id"),
        route_name=route_signals.get("route_name"),
    )
    use_field_lookup_signal = field_lookup_signal is not None
    if field_lookup_signal is not None and platform_term_signal is not None:
        if field_lookup_signal.intent_category not in {"lookup_meaning_question", "status_meaning_question"}:
            field_top_score = field_lookup_signal.field_matches[0].score if field_lookup_signal.field_matches else -1.0
            term_top_score = platform_term_signal.term_matches[0].score if platform_term_signal.term_matches else -1.0
            if not (
                field_lookup_signal.intent_category == "field_meaning_question"
                and term_top_score - field_top_score <= 10.0
            ) and term_top_score > field_top_score:
                use_field_lookup_signal = False
    needs_diagnostics = diagnostic_prefetch is not None or is_shift_visibility_question(message, route_context)
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

    if product_overview:
        required_sources.extend(["knowledge_chunks"])

    if use_field_lookup_signal and field_lookup_signal is not None:
        required_sources.extend(["field_dictionary", "lookup_dictionary", "page_help_manifest", "knowledge_chunks"])
        for match in field_lookup_signal.field_matches[:3]:
            if match.page_id:
                likely_page_ids.append(match.page_id)
            if match.module_key:
                likely_module_keys.append(match.module_key)
        for match in field_lookup_signal.lookup_matches[:3]:
            if match.page_id:
                likely_page_ids.append(match.page_id)
            if match.module_key:
                likely_module_keys.append(match.module_key)
        if route_signals.get("page_id"):
            likely_page_ids.insert(0, str(route_signals["page_id"]))
            likely_module_keys.insert(0, _module_key_for_page_id(str(route_signals["page_id"])))
        if field_lookup_signal.intent_category == "form_help_question":
            required_sources.extend(["page_route_catalog"])

    if platform_term_signal is not None:
        required_sources.extend(
            [
                "platform_term_dictionary",
                "page_help_manifest",
                "workflow_help",
                "page_route_catalog",
                "field_dictionary",
                "lookup_dictionary",
                "knowledge_chunks",
            ]
        )
        for match in platform_term_signal.term_matches[:3]:
            if match.page_id:
                likely_page_ids.append(match.page_id)
            if match.module_key:
                likely_module_keys.append(match.module_key)
        if route_signals.get("page_id"):
            likely_page_ids.insert(0, str(route_signals["page_id"]))
            likely_module_keys.insert(0, _module_key_for_page_id(str(route_signals["page_id"])))

    if route_signals.get("customer_context_active") and workflow_intent is not None and workflow_intent.intent == "customer_scoped_order_create":
        likely_page_ids[:0] = ["C-01", "C-02", "P-04"]
        likely_module_keys[:0] = ["customers", "planning"]
        required_sources.extend(["page_route_catalog", "page_help_manifest", "knowledge_chunks"])

    if _is_global_order_management_question(lowered):
        likely_page_ids[:0] = ["P-02", "C-01"]
        likely_module_keys[:0] = ["planning", "customers"]
        required_sources.extend(["page_route_catalog", "knowledge_chunks"])

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
    elif product_overview:
        intent_category = "product_overview"
    elif use_field_lookup_signal and field_lookup_signal is not None:
        intent_category = field_lookup_signal.intent_category
    elif platform_term_signal is not None:
        intent_category = platform_term_signal.intent_category
    elif route_page_id is not None:
        intent_category = "navigation_question"
        required_sources.extend(["page_route_catalog", "knowledge_chunks"])
    else:
        required_sources.append("knowledge_chunks")

    return AssistantRetrievalPlan(
        intent_category=intent_category,
        workflow_intent=workflow_intent.intent if workflow_intent is not None else None,
        workflow_variant=workflow_variant,
        ui_intent=ui_intent.intent if ui_intent is not None else None,
        diagnostic_intent=diagnostic_prefetch.intent if diagnostic_prefetch is not None else None,
        expanded_query=expanded_query.expanded_query,
        detected_terms=expanded_query.detected_terms,
        expanded_terms_en=expanded_query.expanded_terms_en,
        expanded_terms_de=expanded_query.expanded_terms_de,
        concept_keys=expanded_query.concept_keys,
        likely_page_ids=tuple(_dedupe_preserve_order(likely_page_ids)),
        likely_module_keys=tuple(_dedupe_preserve_order([key for key in likely_module_keys if key])),
        required_sources=tuple(_dedupe_preserve_order(required_sources)),
        needs_diagnostics=needs_diagnostics,
        diagnostic_missing_inputs=diagnostic_prefetch.missing_inputs if diagnostic_prefetch is not None else (),
        diagnostic_checks_missing_input=diagnostic_prefetch.checks_missing_input if diagnostic_prefetch is not None else (),
        route_context_signals=route_signals,
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
    if page_id.startswith("F"):
        return "dashboard"
    if page_id.startswith("E"):
        return "employees"
    if page_id.startswith("FD"):
        return "field_execution"
    if page_id.startswith("P"):
        return "planning"
    if page_id.startswith("C"):
        return "customers"
    if page_id.startswith("FI"):
        return "finance"
    if page_id.startswith("S"):
        return "subcontractors"
    return "platform"


def _route_query_string(value: Any) -> str | None:
    if isinstance(value, list):
        value = value[0] if value else None
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _detect_customer_scoped_order_variant(
    lowered: str,
    route_signals: dict[str, Any],
) -> str | None:
    customer_context = bool(route_signals.get("customer_context_active")) or bool(route_signals.get("customer_order_workspace")) or any(
        token in lowered
        for token in (
            "from customer page",
            "from the customer",
            "inside customer",
            "customer tab",
            "customer orders",
            "customer contract",
            "create order for this customer",
            "beim kunden",
            "im kundenbereich",
            "kunden-workspace",
            "kundenseite",
            "orders-tab",
            "orders tab",
            "kundenauftrag",
            "vertrag beim kunden",
            "auftrag direkt beim kunden",
            "از صفحه مشتری",
            "در بخش مشتری",
            "تب orders",
            "قرارداد مشتری",
            "order برای مشتری",
            "ثبت قرارداد از صفحه مشتری",
        )
    )
    if not customer_context:
        return None
    if any(term in lowered for term in ("staffing coverage", "staffing handoff", "generate series", "series", "ausnahmen", "serien", "handoff", "übergabe")):
        return "staffing_handoff_from_customer_order" if "staffing" in lowered or "handoff" in lowered or "übergabe" in lowered else "series_generation_from_customer_order"
    if any(term in lowered for term in ("shift plan", "schichtplan", "shift template", "shift series")):
        return "shift_plan_from_customer_order"
    if any(term in lowered for term in ("planning record", "planungsdatensatz", "planungspaket")):
        return "planning_record_from_customer_order"
    if any(term in lowered for term in ("document", "documents", "attachment", "attachments", "dokument", "dokumente", "anhang", "anhänge", "سند", "مدرک")):
        return "customer_order_documents"
    if any(term in lowered for term in ("edit", "bearbeiten", "existing order", "bestehenden auftrag", "auftrag bearbeiten")):
        return "customer_order_edit"
    if any(term in lowered for term in ("contract", "vertrag", "قرارداد")):
        return "customer_contract_register_from_customer"
    if route_signals.get("customer_order_workspace"):
        return "customer_order_workspace_flow"
    if any(term in lowered for term in ("order", "auftrag", "orders", "customers order", "kundenauftrag", "سفارش")):
        return "customer_order_from_customer_page"
    return None


def _should_promote_to_customer_scoped_order(
    *,
    lowered: str,
    route_signals: dict[str, Any],
    workflow_intent: str | None,
) -> bool:
    if _is_global_order_management_question(lowered):
        return False
    if not route_signals.get("customer_context_active") and not route_signals.get("customer_order_workspace"):
        return False
    if _detect_customer_scoped_order_variant(lowered, route_signals) is None:
        return False
    if workflow_intent in {
        None,
        "customer_order_create",
        "contract_or_document_register",
        "customer_plan_create",
        "planning_record_create",
        "customer_scoped_order_create",
    }:
        return True
    return False


def _is_global_order_management_question(lowered: str) -> bool:
    return any(
        term in lowered
        for term in (
            "manage all orders",
            "where are orders & planning records",
            "where are orders and planning records",
            "all orders",
            "alle aufträge",
            "wo sind orders",
            "orders & planning records",
            "orders and planning records",
            "wie verwalte ich alle aufträge",
        )
    )
