from __future__ import annotations

from pathlib import Path

from app.modules.assistant.knowledge import ingest as ingest_module


class _FakeSession:
    def commit(self) -> None:
        return None


class _FakeSessionFactory:
    def __call__(self):
        return self

    def __enter__(self):
        return _FakeSession()

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeRepository:
    runs = 0
    active_chunks = 0
    hashes: dict[str, str] = {}

    def __init__(self, session) -> None:  # noqa: ANN001
        self.session = session

    def purge_all(self) -> None:
        type(self).hashes.clear()

    def find_active_source_by_path_hash(self, *, source_path: str, source_hash: str):
        current = type(self).hashes.get(source_path)
        if current == source_hash:
            return object()
        return None

    def find_latest_source_by_path(self, *, source_path: str):
        return None

    def upsert_source(
        self,
        *,
        existing_source,
        source_type: str,
        source_name: str,
        source_path: str,
        source_hash: str,
        source_version: str | None,
        source_language: str | None,
        status: str,
    ):
        type(self).hashes[source_path] = source_hash
        return type("Source", (), {"id": source_path, "source_path": source_path})()

    def replace_chunks(self, *, source, chunks):  # noqa: ANN001
        type(self).runs += 1
        type(self).active_chunks = len(chunks)

    def count_active_chunks(self) -> int:
        return type(self).active_chunks


def _prepare_repo(repo_root: Path) -> None:
    docs_root = repo_root / "docs"
    for relative_path in (
        "sprint/AI-Assistant.md",
        "engineering/ai-assistant-architecture.md",
        "security/ai-assistant-security.md",
        "qa/ai-assistant-test-plan.md",
        "support/hypercare-runbook.md",
        "training/us-35-role-guides.md",
        "discovery/us-1-t1-scope-review.md",
    ):
        path = docs_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Seed\n\nC-01 P-02 PS-01\n", encoding="utf-8")


def test_run_reindex_reports_registered_and_skipped_unchanged(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    _prepare_repo(repo_root)
    monkeypatch.setattr(ingest_module, "AssistantKnowledgeRepository", _FakeRepository)

    first = ingest_module.run_reindex(
        repo_root=repo_root,
        session_factory=_FakeSessionFactory(),
        reindex=True,
    )
    second = ingest_module.run_reindex(
        repo_root=repo_root,
        session_factory=_FakeSessionFactory(),
        reindex=False,
    )

    assert first["sources_registered"] >= 8
    assert first["chunks_created"] > 0
    assert second["sources_skipped_unchanged"] >= 1
    assert "chunks_active" in second
