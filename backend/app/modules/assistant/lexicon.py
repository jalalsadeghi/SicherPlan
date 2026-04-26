"""Multilingual domain lexicon and query expansion for assistant retrieval."""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.modules.assistant.workflow_help import WORKFLOW_HELP_SEEDS


TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


DOMAIN_LEXICON: dict[str, tuple[str, ...]] = {
    "customer": ("مشتری", "customer", "kunde", "klient", "auftraggeber"),
    "employee": ("کارمند", "پرسنل", "نگهبان", "employee", "mitarbeiter", "guard"),
    "order": ("order", "customer order", "سفارش", "auftrag", "einsatzauftrag", "projekt"),
    "planning_record": ("پلن", "برنامه", "planning record", "plan", "planung", "einsatzplanung"),
    "shift": ("شیفت", "شفت", "صیفت", "shift", "schicht", "dienst"),
    "assignment": ("assign", "assgin", "اختصاص", "تخصیص", "نسبت", "نصبت", "zuweisen", "zuordnung"),
    "contract_document": ("قرارداد", "contract", "vertrag", "document", "dokument", "attachment", "سند"),
    "invoice_billing": ("invoice", "billing", "فاکتور", "صورت‌حساب", "rechnung", "abrechnung"),
    "subcontractor": ("پیمانکار", "subcontractor", "subunternehmer", "partner"),
    "watchbook": ("watchbook", "wachbuch", "دفتر وقایع"),
}

CONCEPT_PAGE_HINTS: dict[str, tuple[str, ...]] = {
    "customer": ("C-01",),
    "employee": ("E-01",),
    "order": ("P-02", "C-01"),
    "planning_record": ("P-02", "P-03", "C-01"),
    "shift": ("P-03", "P-04", "P-05"),
    "assignment": ("P-04", "P-05", "E-01"),
    "contract_document": ("PS-01", "C-01", "P-02"),
    "invoice_billing": ("FI-01", "FI-03"),
    "subcontractor": ("S-01", "P-05"),
    "watchbook": ("FD-01",),
}

CONCEPT_MODULE_HINTS: dict[str, tuple[str, ...]] = {
    "customer": ("customers",),
    "employee": ("employees",),
    "order": ("planning", "customers"),
    "planning_record": ("planning", "customers"),
    "shift": ("planning",),
    "assignment": ("planning", "employees"),
    "contract_document": ("platform_services", "customers", "planning"),
    "invoice_billing": ("finance",),
    "subcontractor": ("subcontractors", "planning"),
    "watchbook": ("field_execution",),
}

CONCEPT_EXPANSION_TERMS: dict[str, tuple[str, ...]] = {
    "customer": ("customer", "customers", "workspace", "C-01", "kunden", "workspace"),
    "employee": ("employee", "employees", "workspace", "E-01", "mitarbeiter"),
    "order": ("order", "orders", "planning", "records", "P-02"),
    "planning_record": ("planning", "record", "plan", "project", "P-02", "P-03"),
    "shift": ("shift", "planning", "staffing", "P-03", "P-04"),
    "assignment": ("assignment", "staffing", "coverage", "P-04", "P-05"),
    "contract_document": ("contract", "document", "attachment", "platform", "services", "PS-01", "C-01", "P-02"),
    "invoice_billing": ("invoice", "billing", "finance"),
    "subcontractor": ("subcontractor", "partner", "workspace", "S-01"),
    "watchbook": ("watchbook", "field", "operations", "FD-01"),
}


@dataclass(frozen=True)
class ExpandedAssistantQuery:
    original_query: str
    expanded_query: str
    concept_keys: tuple[str, ...]
    extra_terms: tuple[str, ...]
    page_hints: tuple[str, ...]
    module_hints: tuple[str, ...]


def detect_domain_concepts(message: str) -> tuple[str, ...]:
    lowered = message.casefold()
    concepts: list[str] = []
    for concept, terms in DOMAIN_LEXICON.items():
        if any(term.casefold() in lowered for term in terms):
            concepts.append(concept)
    return tuple(concepts)


def expand_assistant_query(
    message: str,
    *,
    workflow_intent: str | None = None,
    ui_page_id: str | None = None,
) -> ExpandedAssistantQuery:
    concept_keys = list(detect_domain_concepts(message))
    page_hints: list[str] = []
    module_hints: list[str] = []
    extra_terms: list[str] = []

    for concept in concept_keys:
        page_hints.extend(CONCEPT_PAGE_HINTS.get(concept, ()))
        module_hints.extend(CONCEPT_MODULE_HINTS.get(concept, ()))
        extra_terms.extend(CONCEPT_EXPANSION_TERMS.get(concept, ()))
        extra_terms.extend(DOMAIN_LEXICON.get(concept, ()))

    if workflow_intent and workflow_intent in WORKFLOW_HELP_SEEDS:
        seed = WORKFLOW_HELP_SEEDS[workflow_intent]
        page_hints.extend(seed.linked_page_ids)
        module_hints.extend(_module_hints_from_pages(seed.linked_page_ids))
        extra_terms.append(workflow_intent)
        extra_terms.extend(seed.linked_page_ids)
        extra_terms.append(seed.title)

    if ui_page_id:
        page_hints.append(ui_page_id)
        module_hints.extend(_module_hints_from_pages((ui_page_id,)))
        extra_terms.append(ui_page_id)

    tokens = _tokenize(message)
    expanded_tokens = _dedupe_preserve_order(
        [*tokens, *extra_terms, *page_hints, *module_hints]
    )
    return ExpandedAssistantQuery(
        original_query=message,
        expanded_query=" ".join(expanded_tokens),
        concept_keys=tuple(_dedupe_preserve_order(concept_keys)),
        extra_terms=tuple(_dedupe_preserve_order(extra_terms)),
        page_hints=tuple(_dedupe_preserve_order(page_hints)),
        module_hints=tuple(_dedupe_preserve_order(module_hints)),
    )


def _module_hints_from_pages(page_ids: tuple[str, ...] | list[str]) -> list[str]:
    module_hints: list[str] = []
    for page_id in page_ids:
        if page_id.startswith("PS"):
            module_hints.append("platform_services")
        elif page_id.startswith("C"):
            module_hints.append("customers")
        elif page_id.startswith("E"):
            module_hints.append("employees")
        elif page_id.startswith("P") or page_id.startswith("FD"):
            module_hints.append("planning")
        elif page_id.startswith("FI"):
            module_hints.append("finance")
    return module_hints


def _tokenize(value: str) -> list[str]:
    return TOKEN_RE.findall(value.casefold())


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result
