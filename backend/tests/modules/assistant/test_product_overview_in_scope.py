from __future__ import annotations

from dataclasses import dataclass

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantKnowledgeChunkResult, AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _context, _repository


class _OverviewKnowledgeRetriever:
    def retrieve_knowledge_chunks(self, *args, **kwargs):  # noqa: ANN002, ANN003
        query = str(kwargs.get("query") or (args[0] if args else ""))
        if "software" not in query.casefold() and "sicherplan" not in query.casefold():
            return []
        return [
            AssistantKnowledgeChunkResult(
                chunk_id="overview-1",
                source_id="source-overview-1",
                source_name="Operational Handbook",
                source_type="operational_handbook",
                source_path="docs/support/hypercare-runbook.md",
                source_language="de",
                title="SicherPlan overview",
                content="SicherPlan ist eine mandantenfähige Plattform für Sicherheitsunternehmen mit Kunden, Mitarbeitern, Subunternehmern, Planung, Feldeinsatz, Wachbuch, Zeiterfassung, Actuals, Abrechnung, Payroll, Reporting und Portalen.",
                content_preview="SicherPlan ist eine mandantenfähige Plattform für Sicherheitsunternehmen.",
                language_code="de",
                module_key="platform",
                page_id=None,
                score=42.0,
                rank=1,
                matched_by="lexical",
            )
        ]


@dataclass
class _OverviewProvider:
    requests: list[AssistantProviderRequest]

    def __init__(self) -> None:
        self.requests = []

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": "SicherPlan ist eine mandantenfähige Plattform für Sicherheitsunternehmen mit Kunden, Mitarbeitenden, Subunternehmern, Planung, Feldeinsatz, Wachbuch, Zeiterfassung, Actuals, Abrechnung, Payroll, Reporting und Portalen.",
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text="overview",
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
        )


def test_product_overview_question_is_in_scope_and_grounded() -> None:
    repository = _repository()
    provider = _OverviewProvider()
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-test",
        ),
        repository=repository,
        provider=provider,
        knowledge_retriever=_OverviewKnowledgeRetriever(),
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            page_help_repository=repository,
        ),
    )
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="Bitte erklären Sie mir kurz und bündig, was diese Software genau macht."),
        _context("assistant.chat.access"),
    )

    assert response.out_of_scope is False
    assert response.rag_trace is not None
    assert response.rag_trace.retrieval_plan["intent_category"] == "product_overview"
    assert response.rag_trace.content_bearing_source_count > 0
    assert response.source_basis
    assert provider.requests
