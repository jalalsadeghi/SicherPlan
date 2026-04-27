from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
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


FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "assistant" / "golden_qa_en_de.json"


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
        intent_category = str(retrieval_plan.get("intent_category") or "").strip()
        answer = _compose_answer(
            response_language=request.response_language,
            intent_category=intent_category,
            workflow_intent=workflow_intent,
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
        AssistantMessageCreate(message=case.question),
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

    if response.links:
        failures.append("unexpected_links_present")

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


def _compose_answer(*, response_language: str, intent_category: str, workflow_intent: str) -> str:
    key = workflow_intent or intent_category
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
    return mapping.get(key, mapping["product_overview"])


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
