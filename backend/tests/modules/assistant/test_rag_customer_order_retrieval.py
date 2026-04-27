from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from app.modules.assistant.knowledge.types import KnowledgeChunkCandidate


@dataclass
class _Repo:
    candidates: list[KnowledgeChunkCandidate] = field(default_factory=list)

    def list_active_chunk_candidates(
        self,
        *,
        source_type: str | None = None,
        candidate_limit: int = 200,
    ) -> list[KnowledgeChunkCandidate]:
        items = [item for item in self.candidates if source_type is None or item.source_type == source_type]
        return items[:candidate_limit]


def _candidate(
    *,
    chunk_id: str,
    source_type: str,
    title: str,
    content: str,
    page_id: str,
    module_key: str,
    language_code: str,
) -> KnowledgeChunkCandidate:
    return KnowledgeChunkCandidate(
        chunk_id=chunk_id,
        source_id=f"source-{chunk_id}",
        source_name=f"source-{chunk_id}",
        source_type=source_type,
        source_path=f"/generated/{chunk_id}.md",
        chunk_index=0,
        source_language=language_code,
        title=title,
        content=content,
        language_code=language_code,
        module_key=module_key,
        page_id=page_id,
        role_keys=[],
        permission_keys=[],
        token_count=max(len(content) // 4, 1),
    )


def _retriever() -> AssistantKnowledgeRetriever:
    return AssistantKnowledgeRetriever(
        repository=_Repo(
            [
                _candidate(
                    chunk_id="customers-fa",
                    source_type="user_manual",
                    title="ثبت مشتری در C-01",
                    content="برای ثبت مشتری از workspace C-01 استفاده کنید و اطلاعات پایه مشتری را آنجا ثبت کنید.",
                    page_id="C-01",
                    module_key="customers",
                    language_code="fa",
                ),
                _candidate(
                    chunk_id="planning-fa",
                    source_type="workflow_help",
                    title="ثبت planning record در P-02",
                    content="بعد از customer context، ثبت order یا planning record در P-02 ادامه پیدا می‌کند.",
                    page_id="P-02",
                    module_key="planning",
                    language_code="fa",
                ),
                _candidate(
                    chunk_id="shift-fa",
                    source_type="workflow_help",
                    title="ادامه برنامه‌ریزی در P-03",
                    content="برای ساختار دقیق شیفت‌ها بعد از planning record از P-03 استفاده کنید.",
                    page_id="P-03",
                    module_key="planning",
                    language_code="fa",
                ),
                _candidate(
                    chunk_id="dashboard-fa",
                    source_type="page_route_catalog",
                    title="F-02 Dashboard",
                    content="داشبورد فقط نمای کلی است.",
                    page_id="F-02",
                    module_key="dashboard",
                    language_code="fa",
                ),
                _candidate(
                    chunk_id="employees-fa",
                    source_type="page_route_catalog",
                    title="E-01 Employees",
                    content="E-01 برای پرونده پرسنلی است.",
                    page_id="E-01",
                    module_key="employees",
                    language_code="fa",
                ),
            ]
        ),
        retrieval_mode="lexical",
        embeddings_enabled=False,
        max_context_chunks=4,
        max_input_chars=1200,
    )


def test_persian_customer_create_retrieval_prefers_c01() -> None:
    results = _retriever().retrieve_knowledge_chunks(
        query="چطور باید مشتری ثبت کنم؟",
        language_code="fa",
        page_ids=["C-01"],
        module_keys=["customers"],
        workflow_intent="customer_create",
        limit=3,
    )

    assert results[0].page_id == "C-01"
    assert all(item.page_id != "F-02" for item in results[:2])
    assert all(item.page_id != "E-01" for item in results[:2])


def test_persian_customer_plan_retrieval_prefers_customer_and_order_sources() -> None:
    results = _retriever().retrieve_knowledge_chunks(
        query="چطور میتونم یک پلن جدید برای مشتری ثبت کنم؟",
        language_code="fa",
        page_ids=["C-01", "P-02", "P-03"],
        module_keys=["customers", "planning"],
        workflow_intent="customer_plan_create",
        limit=4,
    )

    top_pages = [item.page_id for item in results[:3]]
    assert "C-01" in top_pages
    assert "P-02" in top_pages
    assert "F-02" not in top_pages
    assert "E-01" not in top_pages
