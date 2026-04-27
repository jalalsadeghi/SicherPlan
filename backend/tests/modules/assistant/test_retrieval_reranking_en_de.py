from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from app.modules.assistant.knowledge.types import KnowledgeChunkCandidate


@dataclass
class _Repository:
    candidates: list[KnowledgeChunkCandidate] = field(default_factory=list)

    def list_active_chunk_candidates(self, *, source_type: str | None = None, candidate_limit: int = 200) -> list[KnowledgeChunkCandidate]:
        filtered = [item for item in self.candidates if source_type is None or item.source_type == source_type]
        return filtered[:candidate_limit]


def _candidate(
    *,
    chunk_id: str,
    source_type: str,
    title: str,
    content: str,
    module_key: str,
    page_id: str,
    workflow_keys: list[str] | None = None,
) -> KnowledgeChunkCandidate:
    return KnowledgeChunkCandidate(
        chunk_id=chunk_id,
        source_id=f"source-{chunk_id}",
        source_name=title,
        source_type=source_type,
        source_path=f"/docs/{chunk_id}.md",
        chunk_index=0,
        source_language="de",
        title=title,
        content=content,
        language_code="de",
        module_key=module_key,
        page_id=page_id,
        content_preview=content[:120],
        workflow_keys=workflow_keys or [],
        role_keys=[],
        permission_keys=[],
        api_families=[],
        domain_terms=[],
        language_aliases=[],
        token_count=max(len(content) // 4, 1),
    )


def test_contract_question_demotes_dashboard_and_employee_sources() -> None:
    retriever = AssistantKnowledgeRetriever(
        repository=_Repository(
            [
                _candidate(
                    chunk_id="ps",
                    source_type="workflow_help",
                    title="Contract registration",
                    content="Platform Services PS-01 handles contract and document registration with customer or planning context.",
                    module_key="platform_services",
                    page_id="PS-01",
                    workflow_keys=["contract_or_document_register"],
                ),
                _candidate(
                    chunk_id="f02",
                    source_type="page_route_catalog",
                    title="Dashboard",
                    content="Dashboard overview for KPIs.",
                    module_key="dashboard",
                    page_id="F-02",
                ),
                _candidate(
                    chunk_id="e01",
                    source_type="user_manual",
                    title="Employees Workspace",
                    content="Employee file administration in E-01.",
                    module_key="employees",
                    page_id="E-01",
                ),
            ]
        ),
        max_context_chunks=3,
        max_input_chars=1200,
    )

    results = retriever.retrieve_knowledge_chunks(
        query="Wie registriere ich einen neuen Vertrag?",
        language_code="de",
        workflow_intent="contract_or_document_register",
        page_ids=["PS-01", "C-01", "P-02"],
        module_keys=["platform_services", "customers", "planning"],
        limit=3,
    )

    assert results[0].page_id == "PS-01"
    assert all(item.page_id != "F-02" for item in results[:2])
    assert all(item.page_id != "E-01" for item in results[:2])


def test_employee_assignment_question_prefers_employee_and_staffing_sources() -> None:
    retriever = AssistantKnowledgeRetriever(
        repository=_Repository(
            [
                _candidate(
                    chunk_id="staffing",
                    source_type="workflow_help",
                    title="Employee assignment",
                    content="Assign the employee in Staffing Board P-04 after verifying shift and readiness.",
                    module_key="planning",
                    page_id="P-04",
                    workflow_keys=["employee_assign_to_shift"],
                ),
                _candidate(
                    chunk_id="employee",
                    source_type="user_manual",
                    title="Employees Workspace",
                    content="Employee readiness and qualifications are managed in E-01.",
                    module_key="employees",
                    page_id="E-01",
                ),
                _candidate(
                    chunk_id="dashboard",
                    source_type="page_route_catalog",
                    title="Dashboard",
                    content="Overview dashboard.",
                    module_key="dashboard",
                    page_id="F-02",
                ),
            ]
        ),
        max_context_chunks=3,
        max_input_chars=1200,
    )

    results = retriever.retrieve_knowledge_chunks(
        query="How do I assign an employee to a shift?",
        language_code="en",
        workflow_intent="employee_assign_to_shift",
        page_ids=["E-01", "P-03", "P-04", "P-05"],
        module_keys=["employees", "planning"],
        limit=3,
    )

    assert {results[0].page_id, results[1].page_id} == {"P-04", "E-01"}
