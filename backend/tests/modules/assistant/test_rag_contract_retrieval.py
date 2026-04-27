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
    source_name: str,
    title: str,
    content: str,
    page_id: str,
    module_key: str,
) -> KnowledgeChunkCandidate:
    return KnowledgeChunkCandidate(
        chunk_id=chunk_id,
        source_id=f"source-{chunk_id}",
        source_name=source_name,
        source_type=source_type,
        source_path=f"/generated/{chunk_id}.md",
        chunk_index=0,
        source_language="de",
        title=title,
        content=content,
        language_code="de",
        module_key=module_key,
        page_id=page_id,
        role_keys=[],
        permission_keys=[],
        token_count=max(len(content) // 4, 1),
    )


def test_contract_retrieval_prefers_platform_customer_and_order_context_over_dashboard() -> None:
    retriever = AssistantKnowledgeRetriever(
        repository=_Repo(
            [
                _candidate(
                    chunk_id="ps",
                    source_type="operational_handbook",
                    source_name="Operational Handbook",
                    title="PS-01 Platform Services Workspace",
                    content="Use PS-01 for document create, versioning, and linkage when the exact contract subtype is unclear.",
                    page_id="PS-01",
                    module_key="platform_services",
                ),
                _candidate(
                    chunk_id="customers",
                    source_type="user_manual",
                    source_name="User Manual",
                    title="C-01 Customers Workspace",
                    content="Customer history and customer-scoped attachments belong to C-01.",
                    page_id="C-01",
                    module_key="customers",
                ),
                _candidate(
                    chunk_id="orders",
                    source_type="workflow_help",
                    source_name="Workflow Help",
                    title="P-02 Orders & Planning Records",
                    content="P-02 handles order packages, planning records, and document packages for customer orders.",
                    page_id="P-02",
                    module_key="planning",
                ),
                _candidate(
                    chunk_id="dashboard",
                    source_type="page_route_catalog",
                    source_name="Page Route Catalog",
                    title="F-02 Dashboard",
                    content="F-02 is the landing page overview.",
                    page_id="F-02",
                    module_key="dashboard",
                ),
                _candidate(
                    chunk_id="employees",
                    source_type="page_route_catalog",
                    source_name="Page Route Catalog",
                    title="E-01 Employees Workspace",
                    content="E-01 is for employee master data.",
                    page_id="E-01",
                    module_key="employees",
                ),
            ]
        ),
        retrieval_mode="lexical",
        embeddings_enabled=False,
        max_context_chunks=4,
        max_input_chars=1200,
    )

    results = retriever.retrieve_knowledge_chunks(
        query="Wie registriere ich einen neuen Vertrag?",
        language_code="de",
        page_ids=["PS-01", "C-01", "P-02", "S-01"],
        module_keys=["platform_services", "customers", "planning", "subcontractors"],
        workflow_intent="contract_or_document_register",
        limit=4,
    )

    top_pages = [item.page_id for item in results[:3]]
    assert "PS-01" in top_pages
    assert any(page in {"C-01", "P-02"} for page in top_pages)
    assert "F-02" not in top_pages
    assert "E-01" not in top_pages
    assert any(item.source_type in {"operational_handbook", "user_manual", "workflow_help"} for item in results[:3])
