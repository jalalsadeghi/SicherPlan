from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from app.modules.assistant.knowledge.ingest import (
    AssistantKnowledgeIngestionService,
    build_default_knowledge_registrations,
)
from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from app.modules.assistant.knowledge.source_loader import KnowledgeSourceLoader
from app.modules.assistant.knowledge.types import KnowledgeChunkCandidate
from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate, AssistantStructuredResponse
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _context, _repository
from tests.modules.assistant.test_knowledge_ingestion import InMemoryKnowledgeRepository
from tests.modules.assistant.test_knowledge_retrieval import InMemoryKnowledgeRetrievalRepository


FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "assistant"
FIXTURE_PATH = FIXTURE_DIR / "golden_qa_en_de.json"
CUSTOMER_ORDER_FIXTURE_PATH = FIXTURE_DIR / "golden_qa_customer_orders.json"
FIELDS_LOOKUPS_FIXTURE_PATH = FIXTURE_DIR / "golden_qa_fields_lookups.json"


@dataclass(frozen=True)
class GoldenQaCase:
    id: str
    language: str
    question: str
    expected_intent: str
    expected_pages: list[str]
    required_concepts: list[str]
    forbidden_patterns: list[str]
    requires_source_basis: bool
    min_content_bearing_sources: int
    route_context: dict[str, Any] | None = None
    expected_links: list[str] | None = None


@dataclass
class GoldenQaResult:
    case: GoldenQaCase
    response: AssistantStructuredResponse
    provider_request: AssistantProviderRequest
    failures: list[str]

    @property
    def passed(self) -> bool:
        return not self.failures


class GoldenExpertProvider:
    def __init__(self) -> None:
        self.requests: list[AssistantProviderRequest] = []

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        grounding_context = request.grounding_context or {}
        sources = grounding_context.get("sources")
        if not isinstance(sources, list) or not sources:
            raise AssertionError("Golden expert provider requires non-empty grounding context.")
        content_sources = [
            item for item in sources
            if isinstance(item, dict) and bool(item.get("content_bearing"))
        ]
        if not content_sources:
            raise AssertionError("Golden expert provider requires at least one content-bearing grounding source.")

        retrieval_plan = grounding_context.get("retrieval_plan") or {}
        workflow_intent = str(retrieval_plan.get("workflow_intent") or "").strip()
        workflow_variant = str(retrieval_plan.get("workflow_variant") or "").strip()
        intent_category = str(retrieval_plan.get("intent_category") or "").strip()
        route_signals = retrieval_plan.get("route_context_signals") if isinstance(retrieval_plan.get("route_context_signals"), dict) else {}
        answer = _compose_answer(
            user_message=request.user_message,
            grounding_context=grounding_context,
            response_language=request.response_language,
            intent_category=intent_category,
            workflow_intent=workflow_intent,
            workflow_variant=workflow_variant,
            route_signals=route_signals,
        )
        source_basis = _source_basis_from_sources(content_sources[:4])
        confidence = "medium" if len(content_sources) >= 2 else "low"
        return AssistantProviderResult(
            final_response={
                "answer": answer,
                "confidence": confidence,
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
                "source_basis": source_basis,
            },
            raw_text=answer,
            provider_name="golden-expert",
            provider_mode="openai",
            model_name="golden-expert-test",
        )


def load_golden_cases() -> list[GoldenQaCase]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return [GoldenQaCase(**item) for item in payload]


def load_customer_order_golden_cases() -> list[GoldenQaCase]:
    payload = json.loads(CUSTOMER_ORDER_FIXTURE_PATH.read_text(encoding="utf-8"))
    return [GoldenQaCase(**item) for item in payload]


def load_field_lookup_golden_cases() -> list[GoldenQaCase]:
    payload = json.loads(FIELDS_LOOKUPS_FIXTURE_PATH.read_text(encoding="utf-8"))
    return [GoldenQaCase(**item) for item in payload]


def build_golden_service(tmp_path: Path, provider: GoldenExpertProvider) -> AssistantService:
    repo_root = tmp_path / "golden-qa-repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    _prepare_docs(repo_root)
    candidates = _ingested_candidates(repo_root)
    knowledge_retriever = AssistantKnowledgeRetriever(
        repository=InMemoryKnowledgeRetrievalRepository(candidates),
        max_context_chunks=6,
        max_input_chars=2400,
    )
    repository = _repository()
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
            max_context_chunks=6,
            max_input_chars=2400,
            max_tool_calls=8,
        ),
        repository=repository,
        provider=provider,
        knowledge_retriever=knowledge_retriever,
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            page_help_repository=repository,
            customer_repository=_GoldenLookupRepository(),
        ),
    )


def run_case(tmp_path: Path, case: GoldenQaCase) -> GoldenQaResult:
    provider = GoldenExpertProvider()
    service = build_golden_service(tmp_path, provider)
    conversation = service.repository.create_conversation(  # type: ignore[attr-defined]
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale=case.language,
        last_route_name=None,
        last_route_path=None,
    )
    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message=case.question, route_context=case.route_context),
        _context(
            "assistant.chat.access",
            "customers.customer.read",
            "customers.customer.write",
            "planning.order.read",
            "planning.order.write",
            "planning.record.read",
            "planning.record.write",
            "planning.shift.read",
            "planning.shift.write",
            "planning.staffing.read",
            "employees.employee.read",
            "employees.employee.write",
            "subcontractors.company.read",
            "portal.employee.access",
        ),
    )
    request = provider.requests[-1]
    failures = evaluate_golden_case(case=case, response=response, request=request)
    return GoldenQaResult(case=case, response=response, provider_request=request, failures=failures)


def evaluate_golden_case(
    *,
    case: GoldenQaCase,
    response: AssistantStructuredResponse,
    request: AssistantProviderRequest,
) -> list[str]:
    failures: list[str] = []
    rag_trace = response.rag_trace
    if rag_trace is None:
        failures.append("missing_rag_trace")
        return failures

    if not rag_trace.provider_called:
        failures.append("provider_not_called")
    if not request.grounding_context or not request.grounding_context.get("sources"):
        failures.append("missing_grounding_context")

    actual_intent = str(rag_trace.retrieval_plan.get("workflow_intent") or rag_trace.retrieval_plan.get("intent_category") or "")
    if actual_intent != case.expected_intent:
        failures.append(f"wrong_intent:{actual_intent}")

    if case.expected_pages:
        top_pages = {item.page_id for item in rag_trace.top_sources if item.page_id}
        if not top_pages.intersection(case.expected_pages):
            failures.append("top_sources_not_relevant")

    if rag_trace.content_bearing_source_count < case.min_content_bearing_sources:
        failures.append("insufficient_content_bearing_sources")

    if case.requires_source_basis and not response.source_basis:
        failures.append("missing_source_basis")

    if response.response_language != case.language:
        failures.append("wrong_response_language")

    lowered_answer = response.answer.casefold()
    for concept in case.required_concepts:
        if concept.casefold() not in lowered_answer:
            failures.append(f"missing_concept:{concept}")
    for pattern in case.forbidden_patterns:
        if pattern.casefold() in lowered_answer:
            failures.append(f"forbidden_pattern:{pattern}")

    if response.confidence == "high" and len(response.source_basis) < 2:
        failures.append("high_confidence_without_sufficient_source_basis")

    invented_tokens = ("create employee or new employee",)
    if any(token in lowered_answer for token in invented_tokens):
        failures.append("invented_page_or_action")
    if "contract module" in lowered_answer and "no verified standalone contract module" not in lowered_answer:
        failures.append("invented_page_or_action")
    if "vertragsmodul" in lowered_answer and "nicht verifiziert" not in lowered_answer and "kein eigenständiges vertragsmodul" not in lowered_answer:
        failures.append("invented_page_or_action")

    expected_links = case.expected_links or []
    if expected_links:
        response_link_labels = {str(link.label or "") for link in response.links}
        for expected_label in expected_links:
            if expected_label not in response_link_labels:
                failures.append(f"missing_link:{expected_label}")
    for link in response.links:
        if not str(link.path or "").strip() or str(link.path).strip() == "#":
            failures.append("unsafe_placeholder_link")

    if any(token in lowered_answer for token in ("c-01", "c-02", "p-02", "p-04", "ps-01", "e-01")):
        failures.append("raw_internal_page_code_in_answer")

    if case.expected_intent == "customer_scoped_order_create":
        source_names = {str(item.source_name or "").casefold() for item in response.source_basis}
        if source_names and all(
            name in {"assistant workflow help", "planning orders overview", "orders & planning records"} or "p-02" in name
            for name in source_names
        ):
            failures.append("source_basis_only_old_global_planning")

    return failures


def render_result_row(result: GoldenQaResult) -> str:
    rag_trace = result.response.rag_trace
    top_sources = ",".join(
        item.page_id or item.source_type
        for item in (rag_trace.top_sources if rag_trace is not None else [])
        if (item.page_id or item.source_type)
    )
    source_basis = "yes" if result.response.source_basis else "no"
    status = "PASS" if result.passed else "FAIL"
    actual_intent = str(
        (rag_trace.retrieval_plan.get("workflow_intent") if rag_trace is not None else None)
        or (rag_trace.retrieval_plan.get("intent_category") if rag_trace is not None else None)
        or ""
    )
    return (
        f"{result.case.id} | {actual_intent} | {top_sources} | "
        f"{rag_trace.content_bearing_source_count if rag_trace is not None else 0} | {source_basis} | {status}"
    )


def _prepare_docs(repo_root: Path) -> None:
    docs_root = repo_root / "docs"
    for relative_path, content in (
        (
            "sprint/AI-Assistant.md",
            "# Sprint\n\nSicherPlan connects customers, employees, subcontractors, planning, field execution, billing, reporting, and portals.\n",
        ),
        (
            "engineering/ai-assistant-architecture.md",
            "# Architecture\n\nSicherPlan is a multi-tenant security operations platform with customers, planning, field execution, finance, and reporting.\n",
        ),
        (
            "security/ai-assistant-security.md",
            "# Security\n\nRole-aware, tenant-aware, permission-aware, and audit-oriented platform guidance.\n",
        ),
        (
            "qa/ai-assistant-test-plan.md",
            "# QA\n\nCustomer, employee, contract, planning, and release workflows are source-grounded.\n",
        ),
        (
            "support/hypercare-runbook.md",
            "# Hypercare\n\nContracts are document-centered and platform services own centralized documents.\n",
        ),
        (
            "training/us-35-role-guides.md",
            "# Role Guides\n\nCustomers workspace, employees workspace, orders and planning records, shift planning, staffing board, and employee app release guidance.\n",
        ),
        (
            "discovery/us-1-t1-scope-review.md",
            "# Scope Review\n\nPlatform services own document links and versions, while customers and planning own business meaning.\n",
        ),
    ):
        path = docs_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _ingested_candidates(repo_root: Path) -> list[KnowledgeChunkCandidate]:
    ingest_repository = InMemoryKnowledgeRepository()
    loader = KnowledgeSourceLoader(
        allowed_roots=[repo_root / "docs", repo_root / "tmp" / "assistant-knowledge"]
    )
    service = AssistantKnowledgeIngestionService(loader=loader, repository=ingest_repository)
    result = service.ingest(build_default_knowledge_registrations(repo_root))
    if result.sources_failed:
        raise AssertionError(f"Knowledge ingestion failed: {result.failures}")

    candidates: list[KnowledgeChunkCandidate] = []
    for source_path, source in ingest_repository.sources.items():
        for chunk in ingest_repository.chunks_by_path.get(source_path, []):
            candidates.append(
                KnowledgeChunkCandidate(
                    chunk_id=f"{source.id}-{chunk['chunk_index']}",
                    source_id=source.id,
                    source_name=source.source_name,
                    source_type=source.source_type,
                    source_path=source.source_path,
                    chunk_index=int(chunk["chunk_index"]),
                    source_language=source.source_language,
                    title=chunk["title"],
                    content=str(chunk["content"]),
                    language_code=chunk["language_code"],
                    module_key=chunk["module_key"],
                    page_id=chunk["page_id"],
                    content_preview=chunk["content_preview"],
                    workflow_keys=list(chunk["workflow_keys"]),
                    role_keys=list(chunk["role_keys"]),
                    permission_keys=list(chunk["permission_keys"]),
                    api_families=list(chunk["api_families"]),
                    domain_terms=list(chunk["domain_terms"]),
                    language_aliases=list(chunk["language_aliases"]),
                    token_count=chunk["token_count"],
                )
            )
    return candidates


def _compose_answer(
    *,
    user_message: str = "",
    grounding_context: dict[str, Any] | None = None,
    response_language: str,
    intent_category: str,
    workflow_intent: str,
    workflow_variant: str = "",
    route_signals: dict[str, Any] | None = None,
) -> str:
    key = workflow_intent or intent_category
    route_signals = route_signals or {}
    grounding_context = grounding_context or {}
    customer_selected = bool(route_signals.get("customer_id"))
    if intent_category in {"field_meaning_question", "lookup_meaning_question", "status_meaning_question", "form_help_question", "column_meaning_question", "tab_action_label_question"}:
        return _compose_field_lookup_answer(
            user_message=user_message,
            grounding_context=grounding_context,
            response_language=response_language,
            intent_category=intent_category,
        )
    if response_language == "de":
        mapping = {
            "product_overview": "SicherPlan ist eine mandantenfähige Sicherheitsoperations-Plattform für Sicherheitsunternehmen. Sie verbindet Kunden, Mitarbeiter, Subunternehmer, Planung, Feldausführung, Abrechnung und Reporting in einem rollen-, berechtigungs- und mandantenbezogenen Betriebsmodell.",
            "customer_create": "Nutzen Sie den Kunden-Workspace, um den Kundenstamm anzulegen. Dazu gehören Kundenstamm, Kontakte, Adressen, Abrechnungsprofil, Rechnungsempfänger, Preislisten und Berechtigungen beziehungsweise Sichtbarkeitsregeln.",
            "employee_create": "Nutzen Sie den Mitarbeiter-Workspace für die Mitarbeiterakte. Pflegen Sie Identität, Personalnummer, Qualifikationen, Verfügbarkeit, App-Zugang und die nötigen Berechtigungen vor dem operativen Einsatz.",
            "contract_or_document_register": "Kein eigenständiges Vertragsmodul ist verifiziert. Für Dokumente und Verträge ist Plattformdienste relevant; je nach Typ brauchen Sie zusätzlich Kundenkontext, Auftragskontext oder Subunternehmerkontext. Falls der Vertragstyp unklar ist, ist eine Rückfrage nötig.",
            "customer_order_create": "Legen Sie zuerst den Kundenkontext fest und wechseln Sie dann in Aufträge & Planung. Dort erfassen Sie Auftrag, Anforderungen, Equipment, Anhänge und den Planungsdatensatz als Grundlage für die weitere Planung.",
            "employee_assign_to_shift": "Prüfen Sie zuerst Mitarbeiter, Qualifikation und Verfügbarkeit. Danach arbeiten Sie mit Schichtplanung und Staffing Board, kontrollieren Doppelbuchung oder andere Prüfungen und berücksichtigen anschließend Freigabe und App-Sichtbarkeit.",
            "shift_release_to_employee_app": "Prüfen Sie Schicht, Besetzung, Freigabe und den Self-Service-Zugang. Für die Mitarbeiter-App sind Schichtfreigabe, Staffing-Status, Disposition und der Self-Service-Kontext gemeinsam relevant.",
        }
        if key == "customer_scoped_order_create":
            prefix = "Starten Sie in Kunden, öffnen Sie den ausgewählten Kunden und wechseln Sie in den Orders-Tab. " if customer_selected else "Starten Sie in Kunden, wählen Sie zuerst einen Kunden aus und wechseln Sie dann in den Orders-Tab. "
            if workflow_variant == "customer_contract_register_from_customer":
                return prefix + "Nutzen Sie New order oder Edit im Order Workspace. Dort laufen Auftragsdetails, Auftragsumfang und Dokumente, Planungsdatensatz, Planungsdokumente, Schichtplan sowie Serien und Ausnahmen. Kein eigenständiges Vertragsmodul ist verifiziert; Vertragsdokumente werden in Auftragsdokumente oder Planungsdokumente verknüpft. Mit Generate Series & Continue werden konkrete Schichten erzeugt und nach Staffing Coverage übergeben."
            if workflow_variant == "customer_order_documents":
                return prefix + "Öffnen Sie New order oder Edit im Order Workspace. Dort pflegen Sie Auftragsdetails, Auftragsumfang und Dokumente, danach Planungsdatensatz, Planungsdokumente, Schichtplan sowie Serien und Ausnahmen. Das Vertragsdokument gehört in Auftragsdokumente oder, falls es zum Planungsdatensatz gehört, in Planungsdokumente. Generate Series & Continue führt anschließend nach Staffing Coverage."
            if workflow_variant in {"series_generation_from_customer_order", "staffing_handoff_from_customer_order", "customer_order_workspace_flow"}:
                return prefix + "Im Order Workspace bearbeiten Sie Auftragsdetails, Auftragsumfang und Dokumente, Planungsdatensatz, Planungsdokumente, Schichtplan sowie Serien und Ausnahmen. Nach Generate Series & Continue werden konkrete Schichten erzeugt und Sie landen in Staffing Coverage."
            return prefix + "Nutzen Sie New order für einen neuen Ablauf oder Edit für einen bestehenden Auftrag im Order Workspace. Der Wizard führt durch Auftragsdetails, Auftragsumfang und Dokumente, Planungsdatensatz, Planungsdokumente, Schichtplan sowie Serien und Ausnahmen. Mit Generate Series & Continue werden konkrete Schichten erzeugt und nach Staffing Coverage übergeben."
    elif response_language == "fa":
        mapping = {
            "product_overview": "SicherPlan یک پلتفرم چندمستاجری عملیات امنیتی برای شرکت‌های امنیتی است و مشتریان، کارکنان، پیمانکاران فرعی، برنامه‌ریزی، اجرای میدانی، صورتحساب و گزارش‌گیری را در یک مدل دسترسی‌محور به هم وصل می‌کند.",
            "customer_create": "از Customers Workspace برای ثبت مشتری استفاده کنید. این بخش شامل اطلاعات پایه مشتری، مخاطبین، آدرس‌ها، پروفایل صورتحساب، طرف‌های فاکتور، نرخ‌ها و قوانین دسترسی یا دید است.",
            "employee_create": "از Employees Workspace برای ایجاد پرونده کارمند استفاده کنید و هویت، شماره پرسنلی، صلاحیت‌ها، دسترسی اپ و آمادگی عملیاتی را کامل کنید.",
            "contract_or_document_register": "ماژول مستقل قرارداد به صورت تاییدشده وجود ندارد. برای قرارداد و سند باید از زمینه Platform Services استفاده کنید و بسته به نوع مورد، زمینه مشتری، سفارش یا پیمانکار فرعی را هم مشخص کنید.",
            "customer_order_create": "ابتدا زمینه مشتری را مشخص کنید و سپس به Orders & Planning Records بروید تا سفارش، نیازمندی‌ها، تجهیزات، پیوست‌ها و planning record را ثبت کنید.",
            "employee_assign_to_shift": "ابتدا کارمند، صلاحیت و دسترس‌پذیری را بررسی کنید و بعد با Shift Planning و Staffing Board ادامه دهید.",
            "shift_release_to_employee_app": "برای دیده‌شدن در اپ کارمند باید وضعیت شیفت، تخصیص، انتشار و دسترسی self-service بررسی شود.",
        }
        if key == "customer_scoped_order_create":
            prefix = "از Customers شروع کنید، مشتری انتخاب‌شده را باز کنید و به تب Orders بروید. " if customer_selected else "از Customers شروع کنید، اول یک مشتری را انتخاب کنید و بعد به تب Orders بروید. "
            if workflow_variant == "customer_contract_register_from_customer":
                return prefix + "از New order یا Edit در Order workspace استفاده کنید. در این مسیر Order details، Order scope & documents، Planning record، Planning documents، Shift plan و Series & exceptions تکمیل می‌شود. ماژول مستقل Contract به صورت تاییدشده وجود ندارد و فایل قرارداد در بخش Order documents یا Planning documents وصل می‌شود. بعد از Generate Series & Continue شیفت‌های واقعی ساخته می‌شوند و به Staffing Coverage می‌روید."
            if workflow_variant == "customer_order_documents":
                return prefix + "در Order workspace بخش‌های Order details، Order scope & documents، Planning record، Planning documents، Shift plan و Series & exceptions را طی می‌کنید. فایل قرارداد باید در Order documents یا در صورت تعلق به بسته برنامه‌ریزی، در Planning documents وصل شود. Generate Series & Continue بعد از آن به Staffing Coverage می‌رود."
            return prefix + "برای جریان جدید از New order و برای سفارش موجود از Edit در Order workspace استفاده کنید. مسیر wizard شامل Order details، Order scope & documents، Planning record، Planning documents، Shift plan و Series & exceptions است. Generate Series & Continue شیفت‌های واقعی را می‌سازد و شما را به Staffing Coverage می‌برد."
    else:
        mapping = {
            "product_overview": "SicherPlan is a multi-tenant security operations platform for security companies. It connects customers, employees, subcontractors, planning, field execution, billing, and reporting in a role-aware, permission-aware, tenant-aware operating model.",
            "customer_create": "Use the Customers Workspace to create the customer master. That covers customer master data, contacts, addresses, billing profile, invoice parties, rate cards, and permission or visibility rules.",
            "employee_create": "Use the Employees Workspace to create the employee file. Complete identity, personnel number, qualifications, availability, access link, and the required permissions before operational use.",
            "contract_or_document_register": "There is no verified standalone contract module. Platform Services is the document-centered entry point, and you may also need customer context, order context, or subcontractor context. If the contract type is unclear, clarify the business context before guiding the user.",
            "customer_order_create": "Start with customer context and continue in Orders & Planning Records. Capture the order, requirements, equipment, attachments, and the planning record that will drive later planning.",
            "employee_assign_to_shift": "Verify the employee, qualifications, and availability first. Then use shift planning and the Staffing Board, review double booking or other validations, and handle release follow-up afterward.",
            "shift_release_to_employee_app": "Check the shift, staffing state, release state, and self-service access. Employee app visibility depends on shift release, staffing, dispatch follow-up, and the employee self-service context.",
        }
        if key == "customer_scoped_order_create":
            prefix = "Start in Customers, open the selected customer, and switch to the Orders tab. " if customer_selected else "Start in Customers, select a customer first, and then switch to the Orders tab. "
            if workflow_variant == "customer_contract_register_from_customer":
                return prefix + "Use New order or Edit in the Order workspace. The flow covers Order details, Order scope & documents, Planning record, Planning documents, Shift plan, and Series & exceptions. There is no verified standalone Contract module; contract documents belong under Order documents or Planning documents. After Generate Series & Continue, concrete shifts are created and the flow hands off to Staffing Coverage."
            if workflow_variant == "customer_order_documents":
                return prefix + "Open New order or Edit in the Order workspace. The wizard covers Order details, Order scope & documents, Planning record, Planning documents, Shift plan, and Series & exceptions. Attach the contract file under Order documents or, if it belongs to the planning package, under Planning documents. Generate Series & Continue then leads into Staffing Coverage."
            if workflow_variant in {"series_generation_from_customer_order", "staffing_handoff_from_customer_order", "customer_order_workspace_flow"}:
                return prefix + "Inside the Order workspace, complete Order details, Order scope & documents, Planning record, Planning documents, Shift plan, and Series & exceptions. After Generate Series & Continue, concrete shifts are generated and the user lands in Staffing Coverage."
            return prefix + "Use New order for a new flow or Edit for an existing order in the Order workspace. The wizard covers Order details, Order scope & documents, Planning record, Planning documents, Shift plan, and Series & exceptions. Generate Series & Continue creates concrete shifts and hands off to Staffing Coverage."
    return mapping.get(key, mapping["product_overview"])


def _compose_field_lookup_answer(
    *,
    user_message: str,
    grounding_context: dict[str, Any],
    response_language: str,
    intent_category: str,
) -> str:
    sources = grounding_context.get("sources") if isinstance(grounding_context.get("sources"), list) else []
    field_source = next((item for item in sources if isinstance(item, dict) and item.get("source_type") == "field_dictionary"), None)
    lookup_source = next((item for item in sources if isinstance(item, dict) and item.get("source_type") == "lookup_dictionary"), None)
    target_page_id = str((field_source or lookup_source or {}).get("page_id") or "").strip()
    page_source = next(
        (
            item
            for item in sources
            if isinstance(item, dict)
            and item.get("source_type") == "page_help_manifest"
            and str(item.get("page_id") or "").strip() == target_page_id
        ),
        None,
    ) or next((item for item in sources if isinstance(item, dict) and item.get("source_type") == "page_help_manifest"), None)
    page_title = str((page_source or {}).get("title") or (page_source or {}).get("source_name") or "Workspace").strip()
    module_key = str((field_source or lookup_source or {}).get("module_key") or "platform").strip()
    lowered = user_message.casefold().strip()
    probe_label = _display_probe_label(user_message)
    if lowered in {"was bedeutet status", "what does status mean"}:
        if response_language == "de":
            return (
                f"Status ist hier mehrdeutig. Im aktuellen Kontext ist am wahrscheinlichsten der Status im {page_title}, "
                f"aber es kann je nach Abschnitt auch um Freigabestatus oder andere Statusfelder gehen. "
                "Präzisieren Sie bitte, ob Sie den Datensatzstatus, einen Freigabestatus oder einen Sichtbarkeitsstatus meinen."
            )
        if response_language == "fa":
            return (
                f"Status در اینجا مبهم است. در این زمینه محتمل‌ترین معنی وضعیت در {page_title} است، "
                "اما ممکن است منظور وضعیت رکورد، وضعیت انتشار یا وضعیت دید باشد. لطفاً مشخص کنید کدام مورد مدنظر است."
            )
        return (
            f"Status is ambiguous here. In the current context it most likely refers to the status used in {page_title}, "
            "but it could also mean a release state or another status field. Clarify whether you mean record status, release status, or visibility status."
        )
    if field_source is not None and intent_category == "field_meaning_question":
        facts = field_source.get("facts") if isinstance(field_source.get("facts"), dict) else {}
        label = probe_label or str(facts.get("label") or field_source.get("title") or "Field").strip()
        definition = str(facts.get("definition") or field_source.get("content") or "").strip()
        if response_language == "de":
            return f'"{label}" ist im {page_title} ({module_key}) relevant. {definition} Es erscheint im zugehörigen Formular oder Detailkontext und wird dort für die fachliche Einordnung und Folgeprozesse verwendet.'
        if response_language == "fa":
            return f'"{label}" در {page_title} ({module_key}) استفاده می‌شود. {definition} این فیلد در فرم یا جزئیات همان بخش ظاهر می‌شود و برای هویت رسمی یا فرایندهای بعدی به کار می‌رود.'
        return f'"{label}" is used in the {page_title} ({module_key}). {definition} It appears in the related form or detail context and is used for the business meaning and downstream workflow.'
    if lookup_source is not None:
        facts = lookup_source.get("facts") if isinstance(lookup_source.get("facts"), dict) else {}
        label = probe_label or str(facts.get("label") or lookup_source.get("title") or "Lookup").strip()
        matched_values = facts.get("matched_values") if isinstance(facts.get("matched_values"), list) else []
        values = facts.get("values") if isinstance(facts.get("values"), list) else []
        if not matched_values and values:
            matched_values = [
                value
                for value in values
                if isinstance(value, dict) and bool(value.get("matched"))
            ]
        value_source_kind = str(facts.get("value_source_kind") or "")
        if matched_values:
            value = matched_values[0] if isinstance(matched_values[0], dict) else {}
            meaning = (
                value.get("meaning_de") if response_language == "de"
                else value.get("meaning_en") if response_language == "en"
                else value.get("meaning_de") or value.get("meaning_en")
            ) or ""
            code = str(value.get("value") or "")
            parent_label = _lookup_parent_label(lookup_source=lookup_source, response_language=response_language)
            if response_language == "de":
                return f'"{label}" gehört im {page_title} ({module_key}) zum Feld "{parent_label}". "{code}" bedeutet: {meaning} Der Wert steuert Sichtbarkeit, Freigabe oder operative Weiterverarbeitung je nach Kontext.'
            if response_language == "fa":
                return f'"{label}" در {page_title} ({module_key}) به فیلد "{parent_label}" مربوط است. "{code}" یعنی: {meaning} این مقدار بسته به زمینه روی دید، انتشار یا فرایند عملیاتی اثر می‌گذارد.'
            return f'"{label}" in {page_title} ({module_key}) belongs to the "{parent_label}" field. "{code}" means: {meaning} It affects visibility, release handling, or downstream operational processing depending on the context.'
        if value_source_kind == "tenant_lookup":
            if response_language == "de":
                return f'"{label}" ist im {page_title} ({module_key}) ein mandantenspezifisches Lookup-Feld. Es erklärt die Einordnung oder Segmentierung des Datensatzes. Die exakten auswählbaren Werte können je Mandant variieren.'
            if response_language == "fa":
                return f'"{label}" در {page_title} ({module_key}) یک فیلد lookup وابسته به مستاجر است. این فیلد برای دسته‌بندی یا رتبه‌بندی رکورد استفاده می‌شود و مقادیر دقیق آن ممکن است بین مستاجران متفاوت باشد.'
            return f'"{label}" in {page_title} ({module_key}) is a tenant-specific lookup field. It is used for classification or segmentation of the record, and the exact selectable values may vary by tenant.'
        if values:
            if response_language == "de":
                return f'"{label}" ist im {page_title} ({module_key}) ein Auswahl- oder Statusfeld. Es steuert, wie der Datensatz fachlich verwendet oder sichtbar gemacht wird.'
            if response_language == "fa":
                return f'"{label}" در {page_title} ({module_key}) یک فیلد گزینه‌ای یا وضعیتی است و نحوه استفاده یا دیده‌شدن رکورد را مشخص می‌کند.'
            return f'"{label}" in {page_title} ({module_key}) is a lookup or status field and controls how the record is used or made visible.'
    if response_language == "de":
        return f"Die Frage bezieht sich auf ein Feld oder Label im {page_title}. Im aktuellen Kontext ist eine genauere Einordnung über das zugehörige Formular oder den genauen Abschnitt sinnvoll."
    if response_language == "fa":
        return f"این پرسش به یک فیلد یا برچسب در {page_title} مربوط است. برای توضیح دقیق‌تر بهتر است بخش یا فرم دقیق را مشخص کنید."
    return f"This question refers to a field or label in {page_title}. For a more precise explanation, the exact form or section should be clarified."


def _display_probe_label(user_message: str) -> str:
    stripped = user_message.strip().strip("?؟").strip()
    lowered = stripped.casefold()
    prefixes = (
        "was bedeutet ",
        "what does ",
        "what is ",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            stripped = stripped[len(prefix):].strip(" :?-\"'“”„")
            lowered = stripped.casefold()
            break
    suffix_patterns = (
        r"\b(mean|meaning|bedeuten|bedeutet)\b$",
        r"\bim sicherplan\b$",
        r"\bin sicherplan\b$",
        r"یعنی چه$",
        r"یعنی چی$",
        r"چیست$",
        r"چه است$",
    )
    for pattern in suffix_patterns:
        stripped = re.sub(pattern, "", stripped, flags=re.IGNORECASE).strip(" :?-\"'“”„")
    return stripped


def _lookup_parent_label(*, lookup_source: dict[str, Any], response_language: str) -> str:
    lookup_key = str(lookup_source.get("source_name") or "")
    if lookup_key == "planning.release_state":
        if response_language == "de":
            return "Freigabestatus"
        if response_language == "fa":
            return "وضعیت انتشار"
        return "Release state"
    return str(lookup_source.get("title") or lookup_source.get("source_name") or "Lookup").strip()


class _GoldenLookupRow:
    def __init__(self, row_id: str, code: str, label: str, description: str | None = None) -> None:
        self.id = row_id
        self.code = code
        self.label = label
        self.description = description


class _GoldenLookupRepository:
    def list_lookup_values(self, tenant_id: str | None, domain: str):  # noqa: ANN001
        if tenant_id != "tenant-1":
            return []
        rows = {
            "customer_category": [
                _GoldenLookupRow("cat-1", "vip", "VIP", "Priorisierte Kundenklassifizierung für Schlüsselkunden."),
                _GoldenLookupRow("cat-2", "standard", "Standard", "Normale Kundenklassifizierung ohne Sonderregeln."),
            ],
            "customer_ranking": [
                _GoldenLookupRow("rank-1", "a", "A", "Höchste Priorität im Ranking."),
                _GoldenLookupRow("rank-2", "b", "B", "Mittlere Priorität im Ranking."),
            ],
            "customer_status": [
                _GoldenLookupRow("status-1", "preferred", "Preferred", "Mandantenspezifischer Kundenstatus für bevorzugte Betreuung."),
                _GoldenLookupRow("status-2", "prospect", "Prospect", "Mandantenspezifischer Vorstufenstatus."),
            ],
            "legal_form": [
                _GoldenLookupRow("lf-1", "gmbh", "GmbH", "Juristische Rechtsform des Kunden."),
            ],
        }
        return rows.get(domain, [])


def _source_basis_from_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for source in sources:
        source_type = str(source.get("source_type") or "").strip()
        normalized_type = "workflow_help" if source_type == "workflow" else ("page_help_manifest" if source_type == "ui_action" else source_type)
        result.append(
            {
                "source_type": normalized_type,
                "source_name": source.get("source_name"),
                "page_id": source.get("page_id"),
                "module_key": source.get("module_key"),
                "title": source.get("title"),
                "evidence": str(source.get("content") or source.get("title") or source.get("source_name") or "").strip(),
            }
        )
    return result
