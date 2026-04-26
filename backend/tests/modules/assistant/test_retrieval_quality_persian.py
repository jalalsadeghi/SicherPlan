from __future__ import annotations

from app.modules.assistant.knowledge.embeddings import NoopAssistantEmbeddingRetriever
from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from tests.modules.assistant.test_knowledge_retrieval import (
    InMemoryKnowledgeRetrievalRepository,
    _candidate,
)


def _retriever():
    return AssistantKnowledgeRetriever(
        repository=InMemoryKnowledgeRetrievalRepository(
            [
                _candidate(
                    chunk_id="c-customer",
                    source_id="s-customer",
                    source_name="Customers Workspace Manual",
                    title="Create customer in workspace C-01",
                    content="برای ثبت مشتری جدید از Customers Workspace با page C-01 استفاده کنید.",
                    language_code="fa",
                    module_key="customers",
                    page_id="C-01",
                ),
                _candidate(
                    chunk_id="c-order",
                    source_id="s-order",
                    source_name="Orders Planning Manual",
                    title="Create planning record and order in P-02",
                    content="برای ثبت پلن مشتری و customer order از Orders & Planning Records صفحه P-02 شروع کنید.",
                    language_code="fa",
                    module_key="planning",
                    page_id="P-02",
                ),
                _candidate(
                    chunk_id="c-shift",
                    source_id="s-shift",
                    source_name="Shift Planning Manual",
                    title="Continue to P-03",
                    content="پس از planning record به صفحه P-03 برای shift planning بروید.",
                    language_code="fa",
                    module_key="planning",
                    page_id="P-03",
                ),
                _candidate(
                    chunk_id="c-contract",
                    source_id="s-contract",
                    source_name="Platform Services Contract Guide",
                    title="Contract or document registration in PS-01",
                    content="اگر نوع قرارداد روشن نیست، ابتدا Platform Services با page PS-01 را بررسی کنید.",
                    language_code="fa",
                    module_key="platform_services",
                    page_id="PS-01",
                ),
                _candidate(
                    chunk_id="c-dashboard",
                    source_id="s-dashboard",
                    source_name="Dashboard Overview",
                    title="Dashboard F-02 overview",
                    content="داشبورد F-02 فقط نمای کلی tenant را نشان می‌دهد.",
                    language_code="fa",
                    module_key="platform",
                    page_id="F-02",
                ),
                _candidate(
                    chunk_id="c-employee",
                    source_id="s-employee",
                    source_name="Employee Manual",
                    title="Employees workspace E-01",
                    content="برای ایجاد employee به E-01 بروید.",
                    language_code="fa",
                    module_key="employees",
                    page_id="E-01",
                ),
            ]
        ),
        embedding_retriever=NoopAssistantEmbeddingRetriever(),
        retrieval_mode="lexical",
        embeddings_enabled=False,
        max_context_chunks=4,
        max_input_chars=800,
    )


def test_persian_customer_create_prefers_customer_workspace() -> None:
    results = _retriever().retrieve_knowledge_chunks(
        query="چطور باید مشتری ثبت کنم؟",
        language_code="fa",
        page_ids=["C-01"],
        module_keys=["customers"],
        workflow_intent="customer_create",
        limit=4,
    )

    assert results[0].page_id == "C-01"
    assert results[0].module_key == "customers"
    assert [row.page_id for row in results[:3]].count("F-02") == 0
    assert [row.page_id for row in results[:3]].count("E-01") == 0


def test_persian_customer_plan_prefers_customer_and_order_sources() -> None:
    results = _retriever().retrieve_knowledge_chunks(
        query="چطور میتونم یک پلن جدید برای مشتری ثبت کنم؟",
        language_code="fa",
        page_ids=["C-01", "P-02", "P-03"],
        module_keys=["customers", "planning"],
        workflow_intent="customer_plan_create",
        limit=4,
    )

    top_pages = [row.page_id for row in results[:3]]
    assert "C-01" in top_pages
    assert "P-02" in top_pages
    assert top_pages[0] in {"C-01", "P-02"}
    assert top_pages.count("F-02") == 0
    assert top_pages.count("E-01") == 0


def test_persian_contract_registration_does_not_return_dashboard_only_sources() -> None:
    results = _retriever().retrieve_knowledge_chunks(
        query="چطوری یک قرارداد جدید ثبت کنم؟",
        language_code="fa",
        page_ids=["PS-01", "C-01", "P-02"],
        module_keys=["platform_services", "customers", "planning"],
        workflow_intent="contract_registration",
        limit=4,
    )

    top_pages = [row.page_id for row in results[:3]]
    assert "PS-01" in top_pages
    assert any(page in {"C-01", "P-02"} for page in top_pages)
    assert top_pages != ["F-02", "F-02", "F-02"]
