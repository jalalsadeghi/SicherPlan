"""Multilingual domain lexicon and query expansion for assistant retrieval."""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.modules.assistant.workflow_help import WORKFLOW_HELP_SEEDS


TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


DOMAIN_LEXICON: dict[str, tuple[str, ...]] = {
    "customer": ("مشتری", "customer", "customer master", "customer account", "client", "kunde", "kunden", "kundenstamm", "auftraggeber", "klient"),
    "employee": ("کارمند", "پرسنل", "نگهبان", "employee", "guard", "staff", "workforce", "mitarbeiter", "wachkraft", "personal"),
    "order": ("order", "customer order", "job", "سفارش", "auftrag", "kundenauftrag", "einsatzauftrag", "projekt"),
    "planning_record": ("پلن", "برنامه", "planning", "plan", "planning record", "shift plan", "schedule", "operation plan", "planung", "einsatzplanung", "planungsdatensatz", "dienstplanung"),
    "shift": ("شیفت", "شفت", "صیفت", "shift", "duty", "schedule", "schicht", "dienst", "dienstplan"),
    "assignment": ("assign", "assgin", "assignment", "staffing", "allocate", "اختصاص", "تخصیص", "نسبت", "نصبت", "zuweisen", "zuordnung", "einteilen", "besetzung"),
    "contract": ("قرارداد", "contract", "agreement", "contract document", "vertrag", "verträge", "vereinbarung", "vertragsdokument", "سند قرارداد"),
    "document": ("document", "attachment", "file", "proof", "version", "link", "dokument", "anhang", "datei", "nachweis", "version", "verknüpfen", "سند", "فایل", "مدرک"),
    "customer_order_workspace": (
        "customer orders tab",
        "orders tab",
        "order workspace",
        "customer order workspace",
        "customers workspace order",
        "kundenbereich auftrag",
        "orders-tab",
        "kundenauftrag im kundenbereich",
        "customer order documents",
        "order documents",
        "planning record from customer order",
        "shift plan from customer order",
        "staffing handoff from customer order",
        "تب orders مشتری",
        "order workspace مشتری",
        "ثبت order از صفحه مشتری",
    ),
    "invoice_billing": ("invoice", "billing", "timesheet", "فاکتور", "صورت‌حساب", "rechnung", "abrechnung", "stundennachweis"),
    "subcontractor": ("پیمانکار", "subcontractor", "partner", "external worker", "subunternehmer", "fremdpersonal"),
    "watchbook": ("watchbook", "wachbuch", "دفتر وقایع"),
    "product_overview": (
        "sicherplan",
        "software",
        "platform",
        "plattform",
        "what does this software do",
        "was macht diese software",
        "wofür ist diese plattform",
    ),
    "platform_services": ("platform services", "documents", "dokumente", "ps-01"),
    "customer_workspace": ("customers workspace", "kunden", "مشتریان", "c-01"),
    "orders_planning": ("orders & planning records", "orders and planning records", "p-02"),
}

CONCEPT_PAGE_HINTS: dict[str, tuple[str, ...]] = {
    "customer": ("C-01",),
    "employee": ("E-01",),
    "order": ("P-02", "C-01"),
    "planning_record": ("P-02", "P-03", "C-01"),
    "shift": ("P-03", "P-04", "P-05"),
    "assignment": ("P-04", "P-05", "E-01"),
    "contract": ("PS-01", "C-01", "P-02", "S-01"),
    "document": ("PS-01", "C-01", "P-02"),
    "customer_order_workspace": ("C-01", "C-02", "P-04"),
    "invoice_billing": ("FI-01", "FI-03"),
    "subcontractor": ("S-01", "P-05"),
    "watchbook": ("FD-01",),
    "product_overview": (),
    "platform_services": ("PS-01",),
    "customer_workspace": ("C-01",),
    "orders_planning": ("P-02",),
}

CONCEPT_MODULE_HINTS: dict[str, tuple[str, ...]] = {
    "customer": ("customers",),
    "employee": ("employees",),
    "order": ("planning", "customers"),
    "planning_record": ("planning", "customers"),
    "shift": ("planning",),
    "assignment": ("planning", "employees"),
    "contract": ("platform_services", "customers", "planning", "subcontractors"),
    "document": ("platform_services", "customers", "planning"),
    "customer_order_workspace": ("customers", "planning"),
    "invoice_billing": ("finance",),
    "subcontractor": ("subcontractors", "planning"),
    "watchbook": ("field_execution",),
    "product_overview": ("platform",),
    "platform_services": ("platform_services",),
    "customer_workspace": ("customers",),
    "orders_planning": ("planning",),
}

CONCEPT_EXPANSION_TERMS: dict[str, tuple[str, ...]] = {
    "customer": ("customer", "customers", "workspace", "C-01", "kunden", "workspace"),
    "employee": ("employee", "employees", "workspace", "E-01", "mitarbeiter"),
    "order": ("order", "orders", "planning", "records", "P-02"),
    "planning_record": ("planning", "record", "plan", "project", "P-02", "P-03"),
    "shift": ("shift", "planning", "staffing", "P-03", "P-04"),
    "assignment": ("assignment", "staffing", "coverage", "P-04", "P-05"),
    "contract": ("contract", "agreement", "vertrag", "documents", "attachment", "platform", "services", "PS-01", "C-01", "P-02", "S-01"),
    "document": ("document", "documents", "attachment", "file", "version", "link", "PS-01", "C-01", "P-02"),
    "customer_order_workspace": (
        "customer",
        "orders",
        "tab",
        "order",
        "workspace",
        "documents",
        "planning-record",
        "shift-plan",
        "staffing-handoff",
        "C-01",
        "C-02",
        "planning-staffing",
        "P-04",
    ),
    "invoice_billing": ("invoice", "billing", "finance"),
    "subcontractor": ("subcontractor", "partner", "workspace", "S-01"),
    "watchbook": ("watchbook", "field", "operations", "FD-01"),
    "product_overview": (
        "sicherplan",
        "security",
        "operations",
        "platform",
        "multi-tenant",
        "customers",
        "employees",
        "subcontractors",
        "planning",
        "field",
        "watchbook",
        "patrol",
        "time",
        "actuals",
        "billing",
        "payroll",
        "reporting",
        "portals",
    ),
    "platform_services": ("platform", "services", "documents", "document", "versions", "links", "PS-01"),
    "customer_workspace": ("customers", "workspace", "customer", "history", "attachments", "commercial", "C-01"),
    "orders_planning": ("orders", "planning", "records", "document", "packages", "attachments", "P-02"),
}


@dataclass(frozen=True)
class ExpandedAssistantQuery:
    original_query: str
    expanded_query: str
    detected_terms: tuple[str, ...]
    expanded_terms_en: tuple[str, ...]
    expanded_terms_de: tuple[str, ...]
    likely_page_ids: tuple[str, ...]
    likely_module_keys: tuple[str, ...]
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


def expand_query_for_retrieval(
    query: str,
    language_code: str | None = None,
    *,
    workflow_intent: str | None = None,
    ui_page_id: str | None = None,
) -> ExpandedAssistantQuery:
    concept_keys = list(detect_domain_concepts(query))
    page_hints: list[str] = []
    module_hints: list[str] = []
    extra_terms: list[str] = []
    expanded_terms_en: list[str] = []
    expanded_terms_de: list[str] = []

    for concept in concept_keys:
        page_hints.extend(CONCEPT_PAGE_HINTS.get(concept, ()))
        module_hints.extend(CONCEPT_MODULE_HINTS.get(concept, ()))
        extra_terms.extend(CONCEPT_EXPANSION_TERMS.get(concept, ()))
        extra_terms.extend(DOMAIN_LEXICON.get(concept, ()))
        for term in DOMAIN_LEXICON.get(concept, ()):
            lower_term = term.casefold()
            if any(token in lower_term for token in ("kunde", "kunden", "auftrag", "planung", "schicht", "vertrag", "dokument", "rechnung", "zuweisung", "zuord", "einteilen", "besetzung", "wachkraft", "subunternehmer", "fremd")):
                expanded_terms_de.append(term)
            elif any(token in lower_term for token in ("customer", "client", "order", "planning", "shift", "contract", "document", "invoice", "billing", "assignment", "staffing", "employee", "guard", "subcontractor", "partner", "proof", "link")):
                expanded_terms_en.append(term)

    if workflow_intent and workflow_intent in WORKFLOW_HELP_SEEDS:
        seed = WORKFLOW_HELP_SEEDS[workflow_intent]
        page_hints.extend(seed.linked_page_ids)
        module_hints.extend(_module_hints_from_pages(seed.linked_page_ids))
        extra_terms.append(workflow_intent)
        extra_terms.extend(seed.linked_page_ids)
        extra_terms.extend((seed.title_en, seed.title_de, seed.summary_en, seed.summary_de))
        extra_terms.extend(seed.intent_aliases_en)
        extra_terms.extend(seed.intent_aliases_de)
        expanded_terms_en.extend(seed.intent_aliases_en)
        expanded_terms_en.append(seed.title_en)
        expanded_terms_de.extend(seed.intent_aliases_de)
        expanded_terms_de.append(seed.title_de)

    if ui_page_id:
        page_hints.append(ui_page_id)
        module_hints.extend(_module_hints_from_pages((ui_page_id,)))
        extra_terms.append(ui_page_id)

    tokens = _tokenize(query)
    expanded_tokens = _dedupe_preserve_order(
        [*tokens, *extra_terms, *page_hints, *module_hints]
    )
    return ExpandedAssistantQuery(
        original_query=query,
        expanded_query=" ".join(expanded_tokens),
        detected_terms=tuple(_dedupe_preserve_order(concept_keys)),
        expanded_terms_en=tuple(_dedupe_preserve_order(expanded_terms_en)),
        expanded_terms_de=tuple(_dedupe_preserve_order(expanded_terms_de)),
        likely_page_ids=tuple(_dedupe_preserve_order(page_hints)),
        likely_module_keys=tuple(_dedupe_preserve_order(module_hints)),
        concept_keys=tuple(_dedupe_preserve_order(concept_keys)),
        extra_terms=tuple(_dedupe_preserve_order(extra_terms)),
        page_hints=tuple(_dedupe_preserve_order(page_hints)),
        module_hints=tuple(_dedupe_preserve_order(module_hints)),
    )


def expand_assistant_query(
    message: str,
    *,
    workflow_intent: str | None = None,
    ui_page_id: str | None = None,
) -> ExpandedAssistantQuery:
    return expand_query_for_retrieval(
        message,
        None,
        workflow_intent=workflow_intent,
        ui_page_id=ui_page_id,
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
        elif page_id.startswith("S"):
            module_hints.append("subcontractors")
        elif page_id.startswith("FD"):
            module_hints.append("field_execution")
        elif page_id.startswith("P"):
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
