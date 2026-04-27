from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from app.modules.assistant.knowledge.types import KnowledgeChunkCandidate
from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _repository as page_help_repository


@dataclass
class _KnowledgeRepository:
    candidates: list[KnowledgeChunkCandidate] = field(default_factory=list)

    def list_active_chunk_candidates(
        self,
        *,
        source_type: str | None = None,
        candidate_limit: int = 200,
    ) -> list[KnowledgeChunkCandidate]:
        filtered = [
            item for item in self.candidates if source_type is None or item.source_type == source_type
        ]
        return filtered[:candidate_limit]


class _CapturingProvider:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.requests: list[AssistantProviderRequest] = []

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": self.answer,
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text=self.answer,
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
        )


def _candidate(
    *,
    chunk_id: str,
    source_name: str,
    title: str,
    content: str,
    module_key: str,
    page_id: str,
) -> KnowledgeChunkCandidate:
    return KnowledgeChunkCandidate(
        chunk_id=chunk_id,
        source_id=f"source-{chunk_id}",
        source_name=source_name,
        source_type="repository_docs",
        source_path=f"/docs/{chunk_id}.md",
        chunk_index=0,
        source_language="fa",
        title=title,
        content=content,
        language_code="fa",
        module_key=module_key,
        page_id=page_id,
        role_keys=[],
        permission_keys=[],
        token_count=max(len(content) // 4, 1),
    )


def _context(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )


def test_grounding_for_persian_customer_plan_is_not_dashboard_or_employee_dominated() -> None:
    repository = page_help_repository()
    provider = _CapturingProvider("پاسخ مدل")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="fa",
        last_route_name="SicherPlanDashboard",
        last_route_path="/admin/dashboard",
    )
    knowledge_retriever = AssistantKnowledgeRetriever(
        repository=_KnowledgeRepository(
            [
                _candidate(
                    chunk_id="customer",
                    source_name="Customers Manual",
                    title="ثبت مشتری در C-01",
                    content="برای customer context از صفحه C-01 استفاده کنید.",
                    module_key="customers",
                    page_id="C-01",
                ),
                _candidate(
                    chunk_id="order",
                    source_name="Orders Manual",
                    title="ثبت planning record در P-02",
                    content="برای ثبت پلن مشتری از P-02 شروع کنید.",
                    module_key="planning",
                    page_id="P-02",
                ),
                _candidate(
                    chunk_id="dashboard",
                    source_name="Dashboard Manual",
                    title="داشبورد F-02",
                    content="F-02 فقط overview است.",
                    module_key="platform",
                    page_id="F-02",
                ),
                _candidate(
                    chunk_id="employee",
                    source_name="Employee Manual",
                    title="Employees E-01",
                    content="E-01 برای employee master است.",
                    module_key="employees",
                    page_id="E-01",
                ),
            ]
        ),
        retrieval_mode="lexical",
        embeddings_enabled=False,
        max_context_chunks=4,
        max_input_chars=800,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
        ),
        repository=repository,
        provider=provider,
        knowledge_retriever=knowledge_retriever,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="چطور میتونم یک پلن جدید برای مشتری ثبت کنم؟",
            route_context={"page_id": "F-02", "path": "/admin/dashboard"},
        ),
        _context("assistant.chat.access", "customers.customer.read", "planning.order.read", "planning.record.read"),
    )

    assert response.out_of_scope is False
    grounding = provider.requests[0].grounding_context
    assert grounding is not None
    knowledge_pages = [source["page_id"] for source in grounding["sources"] if source["source_type"] == "knowledge_chunk"]
    assert "C-01" in knowledge_pages
    assert "P-02" in knowledge_pages
    assert knowledge_pages[0] in {"C-01", "P-02"}
    assert knowledge_pages[:2] != ["F-02", "E-01"]
