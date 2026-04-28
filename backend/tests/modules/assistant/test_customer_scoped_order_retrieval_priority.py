from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from app.modules.assistant.knowledge.types import KnowledgeChunkCandidate


@dataclass
class _Repository:
    candidates: list[KnowledgeChunkCandidate] = field(default_factory=list)

    def list_active_chunk_candidates(
        self,
        *,
        source_type: str | None = None,
        candidate_limit: int = 200,
    ) -> list[KnowledgeChunkCandidate]:
        rows = [
            item
            for item in self.candidates
            if source_type is None or item.source_type == source_type
        ]
        return rows[:candidate_limit]


def _candidate(
    *,
    chunk_id: str,
    source_name: str,
    source_type: str,
    title: str,
    content: str,
    page_id: str,
    module_key: str,
    source_path: str | None = None,
) -> KnowledgeChunkCandidate:
    return KnowledgeChunkCandidate(
        chunk_id=chunk_id,
        source_id=f"source-{chunk_id}",
        source_name=source_name,
        source_type=source_type,
        source_path=source_path or f"/tmp/{chunk_id}.md",
        chunk_index=0,
        source_language="en",
        title=title,
        content=content,
        language_code="en",
        module_key=module_key,
        page_id=page_id,
        role_keys=[],
        permission_keys=[],
        token_count=32,
    )


def test_customer_scoped_order_query_prefers_customer_workspace_sources() -> None:
    retriever = AssistantKnowledgeRetriever(
        repository=_Repository(
            candidates=[
                _candidate(
                    chunk_id="p02",
                    source_name="Planning Orders Overview",
                    source_type="workflow_help",
                    title="Orders & Planning Records",
                    content="Use the global P-02 route to manage all orders and planning records.",
                    page_id="P-02",
                    module_key="planning",
                ),
                _candidate(
                    chunk_id="c01",
                    source_name="CustomerOrdersTab.vue",
                    source_type="expert_knowledge_pack",
                    title="Customer Orders tab",
                    content="The selected customer Orders tab starts the customer-scoped order flow.",
                    page_id="C-01",
                    module_key="customers",
                ),
                _candidate(
                    chunk_id="c02",
                    source_name="new-plan-step-content.vue",
                    source_type="workflow_help",
                    title="Customer Order Workspace",
                    content="The customer order workspace guides order details, documents, planning record, shift plan, and staffing handoff.",
                    page_id="C-02",
                    module_key="customers",
                ),
            ]
        )
    )

    results = retriever.retrieve_knowledge_chunks(
        query="Wie erstelle ich einen Auftrag direkt beim Kunden?",
        language_code="de",
        workflow_intent="customer_scoped_order_create",
        page_ids=["C-01", "C-02", "P-04"],
        module_keys=["customers", "planning"],
        limit=3,
    )

    assert results[0].page_id in {"C-01", "C-02"}
    assert results[0].page_id != "P-02"
    assert results[-1].page_id == "P-02"


def test_general_order_management_query_can_still_prefer_p02() -> None:
    retriever = AssistantKnowledgeRetriever(
        repository=_Repository(
            candidates=[
                _candidate(
                    chunk_id="p02",
                    source_name="Planning Orders Overview",
                    source_type="workflow_help",
                    title="Orders & Planning Records",
                    content="Use the global P-02 route to manage all orders and planning records.",
                    page_id="P-02",
                    module_key="planning",
                ),
                _candidate(
                    chunk_id="c02",
                    source_name="new-plan-step-content.vue",
                    source_type="workflow_help",
                    title="Customer Order Workspace",
                    content="The customer order workspace is for customer-scoped order creation.",
                    page_id="C-02",
                    module_key="customers",
                ),
            ]
        )
    )

    results = retriever.retrieve_knowledge_chunks(
        query="Wie verwalte ich alle Aufträge?",
        language_code="de",
        workflow_intent="customer_order_create",
        page_ids=["C-01", "P-02"],
        module_keys=["customers", "planning"],
        limit=2,
    )

    assert results[0].page_id == "P-02"
