from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.dialects import postgresql

from app.modules.assistant.knowledge.repository import AssistantKnowledgeRepository
from app.modules.assistant.knowledge.embeddings import NoopAssistantEmbeddingRetriever
from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from app.modules.assistant.knowledge.types import KnowledgeChunkCandidate


@dataclass
class InMemoryKnowledgeRetrievalRepository:
    candidates: list[KnowledgeChunkCandidate] = field(default_factory=list)

    def list_active_chunk_candidates(
        self,
        *,
        source_type: str | None = None,
        candidate_limit: int = 200,
    ) -> list[KnowledgeChunkCandidate]:
        filtered = [
            item
            for item in self.candidates
            if source_type is None or item.source_type == source_type
        ]
        return filtered[:candidate_limit]


class _FakeResult:
    def __init__(self, rows) -> None:  # noqa: ANN001
        self._rows = rows

    def all(self):  # noqa: ANN201
        return self._rows


@dataclass
class _RecordingSession:
    statement: object | None = None

    def execute(self, statement):  # noqa: ANN001, ANN201
        self.statement = statement
        return _FakeResult([])


def _candidate(
    *,
    chunk_id: str,
    source_id: str,
    source_name: str,
    source_type: str = "repository_docs",
    title: str | None,
    content: str,
    language_code: str | None = None,
    module_key: str | None = None,
    page_id: str | None = None,
    role_keys: list[str] | None = None,
    permission_keys: list[str] | None = None,
    chunk_index: int = 0,
    source_path: str | None = None,
) -> KnowledgeChunkCandidate:
    return KnowledgeChunkCandidate(
        chunk_id=chunk_id,
        source_id=source_id,
        source_name=source_name,
        source_type=source_type,
        source_path=source_path or f"/docs/{source_name.casefold().replace(' ', '-')}.md",
        chunk_index=chunk_index,
        title=title,
        content=content,
        language_code=language_code,
        module_key=module_key,
        page_id=page_id,
        role_keys=list(role_keys or []),
        permission_keys=list(permission_keys or []),
        token_count=max(len(content) // 4, 1),
    )


def _retriever(
    candidates: list[KnowledgeChunkCandidate],
    *,
    max_context_chunks: int = 4,
    max_input_chars: int = 600,
) -> AssistantKnowledgeRetriever:
    return AssistantKnowledgeRetriever(
        repository=InMemoryKnowledgeRetrievalRepository(candidates),
        embedding_retriever=NoopAssistantEmbeddingRetriever(),
        max_context_chunks=max_context_chunks,
        max_input_chars=max_input_chars,
    )


def test_retrieves_relevant_english_how_to_chunk() -> None:
    retriever = _retriever(
        [
            _candidate(
                chunk_id="c1",
                source_id="s1",
                source_name="Planning Manual",
                title="Release shifts to the employee app",
                content="To release a shift to the employee app, open planning page P-04 and release the assignment.",
                language_code="en",
                module_key="planning",
                page_id="P-04",
            ),
            _candidate(
                chunk_id="c2",
                source_id="s2",
                source_name="Customers Manual",
                title="Create customer",
                content="Create a new customer from customer master data.",
                language_code="en",
                module_key="customers",
                page_id="C-01",
            ),
        ]
    )

    results = retriever.retrieve_knowledge_chunks(
        query="How do I release a shift to the employee app?",
        language_code="en",
        limit=3,
    )

    assert results[0].chunk_id == "c1"
    assert results[0].matched_by == "lexical"


def test_retrieves_relevant_german_how_to_chunk() -> None:
    retriever = _retriever(
        [
            _candidate(
                chunk_id="c1",
                source_id="s1",
                source_name="Kundenhandbuch",
                title="Neuen Kunden erstellen",
                content="Wie erstelle ich einen neuen Kunden? Oeffnen Sie die Kundenverwaltung und erfassen Sie die Stammdaten.",
                language_code="de",
                module_key="customers",
            ),
            _candidate(
                chunk_id="c2",
                source_id="s2",
                source_name="Planning Manual",
                title="Release shifts",
                content="Release shifts to employees from planning.",
                language_code="en",
                module_key="planning",
            ),
        ]
    )

    results = retriever.retrieve_knowledge_chunks(
        query="Wie erstelle ich einen neuen Kunden?",
        language_code="de",
        limit=2,
    )

    assert results[0].chunk_id == "c1"
    assert results[0].language_code == "de"


def test_retrieves_relevant_persian_how_to_chunk_with_lexical_fallback() -> None:
    retriever = _retriever(
        [
            _candidate(
                chunk_id="c1",
                source_id="s1",
                source_name="Employee Manual FA",
                title="self-service access براي کارمند",
                content="چطور برای یک کارمند self-service access بسازم؟ از صفحه E-01 کاربر را به employee_user وصل کنید.",
                language_code="fa",
                module_key="employees",
                page_id="E-01",
            ),
            _candidate(
                chunk_id="c2",
                source_id="s2",
                source_name="English Manual",
                title="Create customer",
                content="Create a new customer in master data.",
                language_code="en",
                module_key="customers",
            ),
        ]
    )

    results = retriever.retrieve_knowledge_chunks(
        query="چطور برای یک کارمند self-service access بسازم؟",
        language_code="fa",
        limit=2,
    )

    assert results[0].chunk_id == "c1"
    assert results[0].language_code == "fa"


def test_boosts_page_and_module_metadata() -> None:
    retriever = _retriever(
        [
            _candidate(
                chunk_id="c1",
                source_id="s1",
                source_name="Planning Manual",
                title="Release",
                content="Release the assignment here.",
                language_code="en",
                module_key="planning",
                page_id="P-04",
            ),
            _candidate(
                chunk_id="c2",
                source_id="s2",
                source_name="Generic Manual",
                title="Release assignment",
                content="Release the assignment in another module.",
                language_code="en",
                module_key="employees",
                page_id="E-01",
            ),
        ]
    )

    results = retriever.retrieve_knowledge_chunks(
        query="release assignment",
        language_code="en",
        module_key="planning",
        page_id="P-04",
        limit=2,
    )

    assert results[0].chunk_id == "c1"
    assert results[0].page_id == "P-04"


def test_stable_ordering_for_equal_scores() -> None:
    retriever = _retriever(
        [
            _candidate(
                chunk_id="c1",
                source_id="s1",
                source_name="A Manual",
                title="Status",
                content="Check subcontractor invoice status here.",
                language_code="en",
            ),
            _candidate(
                chunk_id="c2",
                source_id="s2",
                source_name="B Manual",
                title="Status",
                content="Check subcontractor invoice status here.",
                language_code="en",
            ),
        ]
    )

    results = retriever.retrieve_knowledge_chunks(
        query="Where can I check subcontractor invoice status?",
        language_code="en",
        limit=2,
    )

    assert [item.chunk_id for item in results] == ["c1", "c2"]


def test_caps_results_at_configured_limit() -> None:
    retriever = _retriever(
        [
            _candidate(
                chunk_id=f"c{index}",
                source_id=f"s{index}",
                source_name=f"Manual {index}",
                title="Planning release",
                content="Planning release instructions.",
                language_code="en",
            )
            for index in range(1, 6)
        ],
        max_context_chunks=2,
    )

    results = retriever.retrieve_knowledge_chunks(
        query="planning release",
        language_code="en",
        limit=5,
    )

    assert len(results) == 2
    assert results[0].rank == 1
    assert results[1].rank == 2


def test_truncates_oversized_chunk_content() -> None:
    retriever = _retriever(
        [
            _candidate(
                chunk_id="c1",
                source_id="s1",
                source_name="Long Manual",
                title="Planning release",
                content=("Planning release " * 80).strip(),
                language_code="en",
            )
        ],
        max_context_chunks=2,
        max_input_chars=120,
    )

    results = retriever.retrieve_knowledge_chunks(
        query="planning release",
        language_code="en",
        limit=2,
    )

    assert len(results[0].content) <= 60
    assert results[0].content.endswith("...")


def test_works_when_embeddings_are_missing() -> None:
    retriever = _retriever(
        [
            _candidate(
                chunk_id="c1",
                source_id="s1",
                source_name="Planning Manual",
                title="Release shifts",
                content="Release shifts to the employee app.",
                language_code="en",
            )
        ]
    )

    results = retriever.retrieve_knowledge_chunks(
        query="release shifts",
        language_code="en",
        limit=1,
    )

    assert len(results) == 1
    assert results[0].matched_by == "lexical"


def test_does_not_require_openai_api_key() -> None:
    retriever = _retriever(
        [
            _candidate(
                chunk_id="c1",
                source_id="s1",
                source_name="Planning Manual",
                title="Release shifts",
                content="Release shifts to the employee app.",
                language_code="en",
            )
        ]
    )

    results = retriever.retrieve_knowledge_chunks(
        query="release shifts",
        language_code="en",
        limit=1,
    )

    assert results[0].source_name == "Planning Manual"


def test_repository_query_reads_only_active_knowledge_chunks() -> None:
    session = _RecordingSession()
    repository = AssistantKnowledgeRepository(session)  # type: ignore[arg-type]

    repository.list_active_chunk_candidates(source_type="repository_docs", candidate_limit=25)

    compiled = str(session.statement.compile(dialect=postgresql.dialect()))
    params = session.statement.compile(dialect=postgresql.dialect()).params
    assert "assistant.knowledge_chunk" in compiled
    assert "assistant.knowledge_source" in compiled
    assert "status" in compiled
    assert params["status_1"] == "active"
    assert params["source_type_1"] == "repository_docs"
